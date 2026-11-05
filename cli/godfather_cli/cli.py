#!/usr/bin/env python3
"""Godfather CLI entry point: argument parsing and the interactive menu."""

import argparse
import datetime
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from . import __version__, picker
from .auth import (
    TOKEN_DAYS,
    TOKEN_EXPIRED,
    TOKEN_MISSING,
    TOKEN_OK,
    TOKEN_REFUSED,
    TOKEN_UNREACHABLE,
    CLIAuthenticator,
)
from .picker import ask_menu, ask_pod, ask_yes, connectable, is_interactive
from .pod_manager import EXPIRED, ApiError, PodManager, report
from .ssh_connector import USERNAME_RE, SSHConnector, forward_spec
from .ui import BORDER, BOX, PURPLE, console, error, info, spinner, warning
from .update_checker import check_for_updates, perform_update, show_update_warning

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
            f"[bold {PURPLE}]Godfather CLI[/bold {PURPLE}]\n"
            f"[dim]Free compute from AI Society at ASU v{__version__}[/dim]",
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
            if not pods:
                self.print_next_session()

    def list_sessions(self):
        """Print the upcoming sessions on the member's pods."""
        if not self.ensure_authenticated():
            return
        try:
            with spinner("Fetching sessions..."):
                sessions = self.pod_manager.fetch_sessions()
        except ApiError as e:
            report(e)
            return
        if sessions is None:
            info("This server does not list sessions yet.")
        elif not sessions:
            info("No upcoming sessions on your pods.")
        else:
            console.print(self.pod_manager.sessions_table(sessions))
            console.print("[dim]A pod starts 10 minutes before its session.[/dim]")

    def print_next_session(self) -> None:
        """Print the soonest session on the member's pods. Prints nothing when there is none or on an error."""
        try:
            sessions = self.pod_manager.fetch_sessions()
        except ApiError:
            return
        line = self.pod_manager.next_session_line(sessions or [])
        if line:
            console.print(line)

    def choose_pod(self) -> Optional[str]:
        """Fetch pods and let the user pick one. None when there is none or the user cancels."""
        pods = self.load_pods()
        if pods is None:
            return None
        if not pods:
            self.pod_manager.show_no_pods()
            self.print_next_session()
            return None
        if not is_interactive():
            return self.pod_manager.prompt_pod_number(pods)
        if not connectable(pods):
            error("None of your pods are running.")
            console.print("[dim]Ask an officer to start one, then run 'godfather connect' again.[/dim]")
            self.print_next_session()
            return None
        try:
            return ask_pod(pods)
        except (KeyboardInterrupt, EOFError):
            console.print("[dim]Cancelled[/dim]")
            return None

    def connect_to_pod(self, pod_id: str = None, admin: bool = False, forwards=()):
        if not self.ensure_authenticated():
            return

        if not pod_id:
            pod_id = self.choose_pod()
            if not pod_id:
                return

        ssh_info = self.fetch_certificate(pod_id, admin)
        if not ssh_info:
            return
        if not self.ssh_connector.save_certificate(ssh_info.get('certificate', '')):
            return
        if admin and not ssh_info.get('is_admin'):
            warning("The server gave you a member shell, not root.")

        self.ssh_connector.connect(ssh_info, forwards)

    def fetch_certificate(self, pod_id: str, admin: bool = False) -> Optional[Dict]:
        """The connection details with a fresh certificate, or None after printing why not."""
        public_key = self.ssh_connector.ensure_keypair()
        if not public_key:
            return None
        for attempt in range(2):
            try:
                with spinner(f"Getting a certificate for pod {pod_id[:12]}..."):
                    return self.pod_manager.fetch_connection_info(pod_id, public_key, admin=admin)
            except ApiError as e:
                if e.kind == EXPIRED and attempt == 0:
                    if self._offer_login(e):
                        continue
                    return None
                report(e)
                return None
        return None

    def setup_vscode(self, pod_id: str = None, admin: bool = False):
        """Write an SSH config entry for a pod and open it in VS Code Remote-SSH."""
        if not self.ensure_authenticated():
            return
        if not pod_id:
            pod_id = self.choose_pod()
            if not pod_id:
                return

        ssh_info = self.fetch_certificate(pod_id, admin)
        if not ssh_info:
            return
        cert_file = self.ssh_connector.pod_cert_file(pod_id)
        if not self.ssh_connector.save_certificate(ssh_info.get('certificate', ''), cert_file):
            return
        alias = self.ssh_connector.write_host(pod_id, ssh_info, Path.home() / '.ssh' / 'config')
        if not alias:
            return

        is_admin = bool(ssh_info.get('is_admin'))
        if admin and not is_admin:
            warning("The server gave you a member certificate, not root.")
        user_folder = str(ssh_info.get('user_folder', ''))
        folder = f"/workspace/users/{user_folder}" if USERNAME_RE.match(user_folder) else '/workspace'
        steps = (
            f"[bold]Host[/bold]      {alias}  [dim](in ~/.ssh/config)[/dim]\n"
            f"[bold]Folder[/bold]    {folder}\n"
            f"[bold]Valid[/bold]     12 hours. Run [bold]godfather vscode {pod_id}[/bold] again to renew.\n\n"
            "In VS Code: install the Remote - SSH extension, run [bold]Remote-SSH: Connect to Host...[/bold],\n"
            f"pick [bold]{alias}[/bold], then open {folder}."
        )
        if is_admin:
            steps += "\n[yellow]This is a root login. Changes to system files affect every user of the pod.[/yellow]"
        console.print(Panel(steps, title="VS Code is set up", border_style=BORDER, box=BOX))

        code = shutil.which('code')
        if code:
            uri = f'vscode-remote://ssh-remote+{alias}{folder}'
            try:
                subprocess.Popen([code, '--folder-uri', uri])
                info("Opening VS Code...")
            except OSError:
                pass

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

    def authenticate(self, paste: bool = False):
        self.authenticator.authenticate(paste=paste)

    def update(self):
        perform_update()

    def run_action(self, action: str) -> None:
        """Run one main menu action."""
        if action == picker.CONNECT:
            self.connect_to_pod()
        elif action == picker.LIST:
            self.list_pods()
        elif action == picker.SESSIONS:
            self.list_sessions()
        elif action == picker.VSCODE:
            self.setup_vscode()
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
        actions = {
            '1': picker.LIST,
            '2': picker.CONNECT,
            '3': picker.STATUS,
            '4': picker.LOGOUT,
            '5': picker.SESSIONS,
            '6': picker.VSCODE,
            '7': picker.EXIT,
        }
        while True:
            console.print()
            menu = Table.grid(padding=(0, 2))
            menu.add_column(style=f"bold {PURPLE}", justify="right")
            menu.add_column()
            menu.add_row("1.", "List available pods")
            menu.add_row("2.", "Connect to a pod")
            menu.add_row("3.", "Show status")
            menu.add_row("4.", "Log out")
            menu.add_row("5.", "Show sessions")
            menu.add_row("6.", "Set up VS Code")
            menu.add_row("7.", "Exit")
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
  godfather connect --admin     Connect as root (officers, on a pod with pod admin on)
  godfather connect --forward 8080   Connect and open http://localhost:8080 to port 8080 on the pod
  godfather sessions            Show upcoming sessions on your pods
  godfather vscode              Set up VS Code Remote-SSH for a pod, picking from a list
  godfather vscode <pod-id>     Set up VS Code for a pod, or renew its 12-hour certificate
  godfather status              Show login and configuration status
  godfather auth                Log in with Discord in your browser
  godfather auth --paste        Log in by pasting the token (browser on another computer)
  godfather logout              Clear the stored session
  godfather update              Update the CLI to the latest version

Questions or issues: https://discord.gg/fXWXwz6fEG
        """,
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['list', 'connect', 'vscode', 'sessions', 'status', 'logout', 'auth', 'update'],
        help='Command to run (omit to open the interactive menu)',
    )
    parser.add_argument('pod_id', nargs='?', help='Pod ID (with "connect" or "vscode")')
    parser.add_argument('--api-url', help='Use a specific platform API URL instead of the default')
    parser.add_argument('--org', help='Organization prefix on the platform (default: ais)')
    parser.add_argument('--paste', action='store_true', help='With "auth": paste the token, no browser sign-in')
    parser.add_argument('--admin', action='store_true', help='With "connect" or "vscode": ask for root')
    parser.add_argument(
        '--forward',
        action='append',
        type=forward_spec,
        default=[],
        metavar='PORT[:POD_PORT]',
        help='With "connect": forward localhost:PORT to POD_PORT (default PORT) on the pod. Repeat for more ports',
    )

    args = parser.parse_args()
    if args.paste and args.command != 'auth':
        parser.error('--paste works only with "auth"')
    if args.admin and args.command not in ('connect', 'vscode'):
        parser.error('--admin works only with "connect" and "vscode"')
    if args.forward and args.command != 'connect':
        parser.error('--forward works only with "connect"')

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
        cli.connect_to_pod(args.pod_id, admin=args.admin, forwards=args.forward)
    elif args.command == 'vscode':
        cli.setup_vscode(args.pod_id, admin=args.admin)
    elif args.command == 'sessions':
        cli.list_sessions()
    elif args.command == 'status':
        cli.status()
    elif args.command == 'logout':
        cli.logout()
    elif args.command == 'auth':
        cli.authenticate(paste=args.paste)
    elif args.command == 'update':
        cli.update()


if __name__ == '__main__':
    main()
