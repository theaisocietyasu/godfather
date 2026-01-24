#!/usr/bin/env python3
"""
AI Society Godfather CLI - Modular version
Command line interface for connecting to RunPod environments
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from .auth import CLIAuthenticator
from .pod_manager import PodManager
from .ssh_connector import SSHConnector
from .update_checker import check_for_updates, show_update_warning, perform_update, force_update_check
from . import __version__

console = Console()


class GodfatherCLI:
    """Main CLI application""" 
    def __init__(self):
        self.config_dir = Path.home() / '.godfather'
        
        # Auto-detect API URL from multiple possible environment variables
        # Priority: GODFATHER_API_URL > BACKEND_URL > NEXT_PUBLIC_BACKEND_URL > NEXT_PUBLIC_API_URL
        self.api_base = (
            os.getenv('GODFATHER_API_URL') or 
            os.getenv('BACKEND_URL') or 
            os.getenv('NEXT_PUBLIC_BACKEND_URL') or 
            (os.getenv('NEXT_PUBLIC_API_URL', '').replace('/api', '')) or
            'https://admin.ais-asu.com'  # Fallback to RunPod proxy
        )
        
        # Initialize components
        self.authenticator = CLIAuthenticator(self.api_base, self.config_dir)
        self.pod_manager = PodManager(self.api_base)
        self.ssh_connector = SSHConnector(self.api_base, self.config_dir)
    
    def print_banner(self):
        """Print CLI banner""" banner = Panel.fit(
            "[bold magenta]Godfather CLI[/bold magenta]\n" f"[dim]AI Society RunPod Environment Manager v{__version__}[/dim]",
            border_style="magenta",
            box=box.DOUBLE
        )
        console.print(banner)
        console.print()
    
    def ensure_authenticated(self) -> bool:
        """Ensure user is authenticated""" 
        if not self.authenticator.is_authenticated():
            return self.authenticator.authenticate()
        
        # Verify token is still valid
        if not self.authenticator.verify_token():
            console.print("[yellow][/yellow] Token expired. Please re-authenticate.")
            return self.authenticator.authenticate()
        
        return True
    
    def list_pods(self):
        """List available public pods""" 
        if not self.ensure_authenticated():
            return
        
        discord_user_id = self.authenticator.get_discord_user_id()
        self.pod_manager.list_pods(discord_user_id)
    
    def connect_to_pod(self, pod_id: str = None):
        """Connect to a specific pod""" 
        if not self.ensure_authenticated():
            return
        
        discord_user_id = self.authenticator.get_discord_user_id()
        
        # Select pod if not provided
        if not pod_id:
            pod_id = self.pod_manager.select_pod(discord_user_id)
            if not pod_id:
                return
        
        console.print(f"[cyan] Connecting to pod {pod_id[:8]}...[/cyan]")
        
        # Get connection details
        ssh_info = self.pod_manager.get_connection_info(pod_id, discord_user_id)
        if not ssh_info:
            return
        
        # Fetch SSH key
        if not self.ssh_connector.fetch_ssh_key(discord_user_id):
            return
        
        # Establish SSH connection
        self.ssh_connector.connect(ssh_info)
    
    def status(self):
        """Show CLI status and configuration""" 
        table = Table(title="[bold cyan]Godfather CLI Status[/bold cyan]", box=box.ROUNDED, border_style="cyan")
        table.add_column("Setting", style="cyan bold", no_wrap=True)
        table.add_column("Value", style="white")
        
        if self.authenticator.is_authenticated():
            table.add_row("🔐 Authentication", "[green] Authenticated[/green]")
            if self.authenticator.verify_token():
                table.add_row("🌐 API Connection", "[green] Connected[/green]")
            else:
                table.add_row("🌐 API Connection", "[yellow] Token expired[/yellow]")
        else:
            table.add_row("🔐 Authentication", "[red] Not authenticated[/red]")
        
        table.add_row("🏠 Config Directory", str(self.config_dir))
        table.add_row("🔗 API Endpoint", self.api_base)
        
        console.print(table)
    
    def logout(self):
        """Clear authentication token""" 
        self.authenticator.logout()
    
    def authenticate(self):
        """Trigger authentication""" 
        self.authenticator.authenticate()
    
    def interactive_menu(self):
        """Show interactive menu""" 
        self.print_banner()
        
        while True:
            console.print()
            menu = Table.grid(padding=(0, 2))
            menu.add_column(style="cyan bold", justify="right")
            menu.add_column(style="white")
            
            menu.add_row("1.", " List available pods")
            menu.add_row("2.", " Connect to a pod")
            menu.add_row("3.", "📊 Show status")
            menu.add_row("4.", "🚪 Logout")
            menu.add_row("5.", "👋 Exit")
            
            panel = Panel(
                menu,
                title="[bold cyan]What would you like to do?[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED
            )
            console.print(panel)
            
            try:
                choice = Prompt.ask("\n[cyan]Enter your choice[/cyan]", choices=["1", "2", "3", "4", "5"], default="1")
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
                    console.print("[bold magenta]👋 Goodbye![/bold magenta]")
                    break
                    
            except KeyboardInterrupt:
                console.print("\n[bold magenta]👋 Goodbye![/bold magenta]")
                break


def main():
    """Main CLI entry point""" 
    parser = argparse.ArgumentParser(
        description='AI Society Godfather CLI - RunPod Environment Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  godfather list                    # List available pods
  godfather connect                 # Interactive pod connection
  godfather connect <pod-id>        # Connect to specific pod
  godfather status                  # Show CLI status
  godfather logout                  # Clear authentication

For support, contact AI Society administrators.
        """ )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['list', 'connect', 'status', 'logout', 'auth'],
        help='Command to execute'
    )
    parser.add_argument(
        'pod_id',
        nargs='?',
        help='Pod ID for connect command'
    )
    parser.add_argument(
        '--api-url',
        help='Override API base URL'
    )
    
    args = parser.parse_args()
    
    # Override API URL if provided
    if args.api_url:
        os.environ['GODFATHER_API_URL'] = args.api_url
    
    cli = GodfatherCLI()
    
    # If no command provided, show interactive menu
    if not args.command:
        cli.interactive_menu()
        return
    
    # Execute command
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


if __name__ == '__main__':
    main()
