#!/usr/bin/env python3
"""Godfather CLI entry point: argument parsing and the interactive menu."""

import os
import argparse
from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from .auth import CLIAuthenticator
from .pod_manager import PodManager
from .ssh_connector import SSHConnector
from .update_checker import check_for_updates, show_update_warning, perform_update
from .ui import console, warning, info, BOX, BORDER, PURPLE
from . import __version__


class GodfatherCLI:
    """Wires together auth, pod listing, and SSH connection for the CLI commands."""

    def __init__(self):
        self.config_dir = Path.home() / '.godfather'

        # Resolve the API base URL, in priority order. GODFATHER_API_URL is
        # the CLI-specific override; the others let us reuse whatever the
        # web app already has configured in the environment.
        self.api_base = (
            os.getenv('GODFATHER_API_URL') or
            os.getenv('BACKEND_URL') or
            os.getenv('NEXT_PUBLIC_BACKEND_URL') or
            (os.getenv('NEXT_PUBLIC_API_URL', '').replace('/api', '')) or
            'https://admin.ais-asu.com'
        )

        self.authenticator = CLIAuthenticator(self.api_base, self.config_dir)
        self.pod_manager = PodManager(self.api_base)
        self.ssh_connector = SSHConnector(self.api_base, self.config_dir)

    def print_banner(self):
        banner = Panel.fit(
            f"[bold {PURPLE}]Godfather CLI[/bold {PURPLE}]\n[dim]AI Society RunPod Environment Manager v{__version__}[/dim]",
            border_style=BORDER,
            box=BOX,
        )
        console.print(banner)
        console.print()

    def ensure_authenticated(self) -> bool:
        """Make sure the user has a valid token, prompting to log in if needed."""
        if not self.authenticator.is_authenticated():
            info("You're not logged in yet.")
            return self.authenticator.authenticate()

        if not self.authenticator.verify_token():
            warning("Your session has expired. Please log in again.")
            return self.authenticator.authenticate()

        return True

    def list_pods(self):
        if not self.ensure_authenticated():
            return

        discord_user_id = self.authenticator.get_discord_user_id()
        self.pod_manager.list_pods(discord_user_id)

    def connect_to_pod(self, pod_id: str = None):
        if not self.ensure_authenticated():
            return

        discord_user_id = self.authenticator.get_discord_user_id()

        if not pod_id:
            pod_id = self.pod_manager.select_pod(discord_user_id)
            if not pod_id:
                return

        console.print(f"Connecting to pod [bold]{pod_id[:8]}[/bold]...")

        ssh_info = self.pod_manager.get_connection_info(pod_id, discord_user_id)
        if not ssh_info:
            return

        if not self.ssh_connector.fetch_ssh_key(discord_user_id):
            return

        self.ssh_connector.connect(ssh_info)

    def status(self):
        """Print current authentication and configuration state."""
        table = Table(title="Godfather CLI Status", box=BOX, border_style=BORDER)
        table.add_column("Setting", style=f"bold {PURPLE}", no_wrap=True)
        table.add_column("Value")

        if self.authenticator.is_authenticated():
            if self.authenticator.verify_token():
                table.add_row("Authentication", "[green]Logged in[/green]")
                table.add_row("API Connection", "[green]Connected[/green]")
            else:
                table.add_row("Authentication", "[yellow]Session expired[/yellow]")
                table.add_row("API Connection", f"[dim]{self.api_base}[/dim]")
        else:
            table.add_row("Authentication", "[red]Not logged in[/red]")

        table.add_row("Config Directory", str(self.config_dir))
        table.add_row("API Endpoint", self.api_base)
        table.add_row("CLI Version", __version__)

        console.print(table)

    def logout(self):
        self.authenticator.logout()

    def authenticate(self):
        self.authenticator.authenticate()

    def update(self):
        perform_update()

    def interactive_menu(self):
        self.print_banner()

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

            panel = Panel(
                menu,
                title="What would you like to do?",
                border_style=BORDER,
                box=BOX,
            )
            console.print(panel)

            try:
                choice = Prompt.ask("\nEnter your choice", choices=["1", "2", "3", "4", "5"], default="1")
                console.print()

                if choice == '1':
                    self.list_pods()
                elif choice == '2':
                    self.connect_to_pod()
                elif choice == '3':
                    self.status()
                elif choice == '4':
                    self.logout()
                elif choice == '5':
                    console.print("Goodbye.")
                    break

            except KeyboardInterrupt:
                console.print("\nGoodbye.")
                break


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
        help='Use a specific API base URL instead of the default'
    )

    args = parser.parse_args()

    if args.api_url:
        os.environ['GODFATHER_API_URL'] = args.api_url

    cli = GodfatherCLI()

    if not args.command:
        # Only check for updates on the interactive menu, not on every
        # scripted invocation - a 'godfather list' shouldn't wait on a
        # PyPI round trip.
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
