#!/usr/bin/env python3
"""Godfather CLI entry point: argument parsing and the interactive menu."""

import argparse
import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from . import picker
from .auth import (
    CLIAuthenticator, TOKEN_DAYS, TOKEN_EXPIRED, TOKEN_MISSING, TOKEN_OK, TOKEN_REFUSED, TOKEN_UNREACHABLE,
)
from .picker import ask_menu, ask_pod, ask_yes, connectable, is_interactive
from .pod_manager import ApiError, EXPIRED, PodManager, report
from .ssh_connector import SSHConnector
from .update_checker import check_for_updates, show_update_warning, perform_update
from .ui import console, error, warning, info, spinner, BOX, BORDER, PURPLE
from . import __version__

# The AI Society platform API and org. Override with --api-url/--org or GODFATHER_API_URL/GODFATHER_ORG.
DEFAULT_API_URL = 'https://zs6k5wi0boaaax-8000.proxy.runpod.net'
# Servers that no longer exist. A saved login or GODFATHER_API_URL that names one falls back to the default.
# Installers before 2.0 wrote GODFATHER_API_URL into ~/.bashrc, ~/.zshrc and fish conf.d.
RETIRED_API_URLS = {
    'https://854ap0rs1ws50n-8000.proxy.runpod.net',
    'https://8bzhwve1ri5cw2-80.proxy.runpod.net',
}
DEFAULT_ORG = 'ais'


class GodfatherCLI:
    """Wires together auth, pod listing, and SSH connection for the CLI commands."""

    def __init__(self):
        self.config_dir = Path.home() / '.godfather'

        # A flag or env var wins, then what the last login saved, then the defaults.
        saved = CLIAuthenticator.read_config(self.config_dir)
        saved_url = saved.get('api_url')
        if saved_url and saved_url.rstrip('/') in RETIRED_API_URLS:
            saved_url = None
        env_url = os.getenv('GODFATHER_API_URL')
        if env_url and env_url.rstrip('/') in RETIRED_API_URLS:
            warning(
                f'GODFATHER_API_URL is set to {env_url}, a server that no longer exists. Using '
                f'{DEFAULT_API_URL} instead. Remove the GODFATHER_API_URL line from your shell profile.'
            )
            env_url = None
        self.api_base = (env_url or saved_url or DEFAULT_API_URL).rstrip('/')
        self.org = os.getenv('GODFATHER_ORG') or saved.get('org') or DEFAULT_ORG

        self.authenticator = CLIAuthenticator(self.api_base, self.org, self.config_dir)
        self.pod_manager = PodManager(self.api_base, self.authenticator)
        self.ssh_connector = SSHConnector(self.config_dir)

    def print_banner(self):
        banner = Panel.fit(
            f"[bold {PURPLE}]Godfather CLI[/bold {PURPLE}]\n[dim]Free compute from AI Society at ASU v{__version__}[/dim]",
            border_style=BORDER,
            box=BOX,
        )
        console.print(banner)
        console.print(f"[dim]Server {self.api_base}  Org {self.org}[/dim]")
        console.print()

    def ensure_authenticated(self) -> bool:
        """Make sure the user has a valid token, prompting to log in if needed."""
        if not self.authenticator.is_authenticated():
            info("You're not logged in yet.")
            return self.authenticator.authenticate()

        with spinner("Checking your login..."):
            state = self.authenticator.check_token()

        if state == TOKEN_EXPIRED:
            warning("Your token has expired, or a newer login replaced it.")
            if is_interactive():
                try:
                    if not ask_yes("Log in again now?"):
                        return False
                except (KeyboardInterrupt, EOFError):
                    return False
            return self.authenticator.authenticate()
        if state == TOKEN_UNREACHABLE:
            error(f"Couldn't reach {self.api_base}")
            console.print("[dim]Check your internet connection, and the server URL with 'godfather status'.[/dim]")
            return False
        # TOKEN_REFUSED: the pods call that follows prints the server's reason.
        return True

    def _offer_login(self, e: ApiError) -> bool:
        """After an expired token error, offer to log in again. True when the user logged in."""
        report(e)
        if not is_interactive():
            return False
        try:
            if not ask_yes("Log in again now?"):
                return False
        except (KeyboardInterrupt, EOFError):
            return False
        return self.authenticator.authenticate()

    def load_pods(self) -> Optional[List[Dict]]:
        """Fetch the member's pods with a spinner. None after an error has been printed."""
        for attempt in range(2):
            try:
                with spinner("Fetching your pods..."):
                    return self.pod_manager.fetch_pods()
            except ApiError as e:
                if e.kind == EXPIRED and attempt == 0:
                    if self._offer_login(e):
                        continue
                    return None
                report(e)
                return None
        return None

    def list_pods(self):
        if not self.ensure_authenticated():
            return
        pods = self.load_pods()
        if pods is not None:
            self.pod_manager.show_pods(pods)

    def choose_pod(self) -> Optional[str]:
        """Fetch pods and let the user pick one. None when there is none or the user cancels."""
        pods = self.load_pods()
        if pods is None:
            return None
        if not pods:
            self.pod_manager.show_no_pods()
            return None
        if not is_interactive():
            return self.pod_manager.prompt_pod_number(pods)
        if not connectable(pods):
            error("None of your pods are running.")
            console.print("[dim]Ask an officer to start one, then run 'godfather connect' again.[/dim]")
            return None
        try:
            return ask_pod(pods)
        except (KeyboardInterrupt, EOFError):
            console.print("[dim]Cancelled[/dim]")
            return None

    def connect_to_pod(self, pod_id: str = None):
        if not self.ensure_authenticated():
            return

        if not pod_id:
            pod_id = self.choose_pod()
            if not pod_id:
                return

        public_key = self.ssh_connector.ensure_keypair()
        if not public_key:
            return

        ssh_info = None
        for attempt in range(2):
            try:
                with spinner(f"Getting a certificate for pod {pod_id[:12]}..."):
                    ssh_info = self.pod_manager.fetch_connection_info(pod_id, public_key)
                break
            except ApiError as e:
                if e.kind == EXPIRED and attempt == 0:
                    if self._offer_login(e):
                        continue
                    return
                report(e)
                return
        if not ssh_info:
            return

        if not self.ssh_connector.save_certificate(ssh_info.get('certificate', '')):
            return

        self.ssh_connector.connect(ssh_info)

    def status(self):
        """Print the server, org, login, token and version details."""
        table = Table(title="Godfather CLI Status", box=BOX, border_style=BORDER)
        table.add_column("Setting", style=f"bold {PURPLE}", no_wrap=True)
        table.add_column("Value")

        with spinner("Checking the server and PyPI..."):
            state = self.authenticator.check_token()
            pods = None
            if state == TOKEN_OK:
                try:
                    pods = self.pod_manager.fetch_pods()
                except ApiError:
                    pods = None
            has_update, latest = check_for_updates()

        table.add_row("Server", self.api_base)
        table.add_row("Organization", self.org)
        table.add_row("Login", LOGIN_TEXT.get(state, state))
        if self.authenticator.is_authenticated():
            table.add_row("Signed in as", "Your Discord account [dim](the server does not send the name)[/dim]")
            token = str(self.authenticator.get_token() or '')
            table.add_row("Token", f"{token[:9]}...")
            saved = self.authenticator.token_saved_at()
            expires = self.authenticator.token_expires_at()
            if saved and expires:
                left = (expires.date() - datetime.date.today()).days
                when = f"about {expires:%Y-%m-%d}" + (f" ({left} days left)" if left >= 0 else " (past)")
                table.add_row(
                    "Token expires", f"{when} [dim](logged in {saved:%Y-%m-%d}, tokens last {TOKEN_DAYS} days)[/dim]"
                )
        if pods is not None:
            table.add_row("Pods you can use", str(len(pods)))
        table.add_row("Config directory", str(self.config_dir))
        if has_update:
            table.add_row("CLI version", f"{__version__} [yellow]({latest} available, run 'godfather update')[/yellow]")
        else:
            table.add_row("CLI version", f"{__version__} [dim](no newer version found on PyPI)[/dim]")

        console.print(table)
        if state == TOKEN_EXPIRED:
            console.print("[dim]Run 'godfather auth' to log in again.[/dim]")
        elif state == TOKEN_UNREACHABLE:
            console.print("[dim]Check your internet connection, or pass --api-url to use another server.[/dim]")
        elif state == TOKEN_MISSING:
            console.print("[dim]Run 'godfather auth' to log in.[/dim]")

    def logout(self):
        self.authenticator.logout()

    def authenticate(self):
        self.authenticator.authenticate()

    def update(self):
        perform_update()

    def run_action(self, action: str) -> None:
        """Run one main menu action."""
        if action == picker.CONNECT:
            self.connect_to_pod()
        elif action == picker.LIST:
            self.list_pods()
        elif action == picker.STATUS:
            self.status()
        elif action == picker.LOGIN:
            self.authenticate()
        elif action == picker.LOGOUT:
            self.logout()

    def interactive_menu(self):
        """The main menu: arrow keys on a terminal, numbered choices otherwise."""
        self.print_banner()
        if not is_interactive():
            self.plain_menu()
            return

        while True:
            try:
                action = ask_menu(self.authenticator.is_authenticated())
                if action == picker.EXIT:
                    break
                console.print()
                self.run_action(action)
                console.print()
            except (KeyboardInterrupt, EOFError):
                console.print()
                break
        console.print("Goodbye.")

    def plain_menu(self):
        """The numbered menu for input that is not a terminal."""
        actions = {'1': picker.LIST, '2': picker.CONNECT, '3': picker.STATUS, '4': picker.LOGOUT, '5': picker.EXIT}
        while True:
            console.print()
            menu = Table.grid(padding=(0, 2))
            menu.add_column(style=f"bold {PURPLE}", justify="right")
            menu.add_column()
            menu.add_row("1.", "List available pods")
            menu.add_row("2.", "Connect to a pod")
            menu.add_row("3.", "Show status")
            menu.add_row("4.", "Log out")
            menu.add_row("5.", "Exit")
            console.print(Panel(menu, title="What would you like to do?", border_style=BORDER, box=BOX))

            try:
                choice = Prompt.ask("\nEnter your choice", choices=list(actions), default="1")
            except (KeyboardInterrupt, EOFError):
                console.print()
                break
            console.print()
            if actions[choice] == picker.EXIT:
                break
            self.run_action(actions[choice])
        console.print("Goodbye.")


LOGIN_TEXT = {
    TOKEN_OK: f"[bold {PURPLE}]Logged in, the server accepts the token[/bold {PURPLE}]",
    TOKEN_EXPIRED: "[yellow]Token expired or replaced by a newer login[/yellow]",
    TOKEN_UNREACHABLE: "[red]Server not reachable[/red]",
    TOKEN_REFUSED: "[yellow]Server refused the token (run 'godfather list' to see why)[/yellow]",
    TOKEN_MISSING: "[red]Not logged in[/red]",
}


def main():
    """Parse arguments and dispatch to the requested command."""
    parser = argparse.ArgumentParser(
        prog='godfather',
        description='Godfather CLI - manage and connect to AI Society RunPod environments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  godfather                     Open the interactive menu
  godfather list                List available pods
  godfather connect             Connect to a pod, picking from a list
  godfather connect <pod-id>    Connect to a specific pod
  godfather status              Show login and configuration status
  godfather auth                Log in or refresh your session
  godfather logout              Clear the stored session
  godfather update              Update the CLI to the latest version

Questions or issues: https://discord.gg/fXWXwz6fEG
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['list', 'connect', 'status', 'logout', 'auth', 'update'],
        help='Command to run (omit to open the interactive menu)'
    )
    parser.add_argument(
        'pod_id',
        nargs='?',
        help='Pod ID to connect to (only used with "connect")'
    )
    parser.add_argument(
        '--api-url',
        help='Use a specific platform API URL instead of the default'
    )
    parser.add_argument(
        '--org',
        help='Organization prefix on the platform (default: ais)'
    )

    args = parser.parse_args()

    if args.api_url:
        os.environ['GODFATHER_API_URL'] = args.api_url
    if args.org:
        os.environ['GODFATHER_ORG'] = args.org

    cli = GodfatherCLI()

    if not args.command:
        # Only check for updates on the interactive menu, not on every
        # scripted invocation - a 'godfather list' shouldn't wait on a
        # PyPI round trip.
        with spinner("Checking for updates..."):
            has_update, latest_version = check_for_updates()
        if has_update:
            show_update_warning(latest_version)
        cli.interactive_menu()
        return

    if args.command == 'list':
        cli.list_pods()
    elif args.command == 'connect':
        cli.connect_to_pod(args.pod_id)
    elif args.command == 'status':
        cli.status()
    elif args.command == 'logout':
        cli.logout()
    elif args.command == 'auth':
        cli.authenticate()
    elif args.command == 'update':
        cli.update()


if __name__ == '__main__':
    main()
