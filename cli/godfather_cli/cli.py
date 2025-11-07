#!/usr/bin/env python3
"""
AI Society Godfather CLI - Modular version
Command line interface for connecting to RunPod environments
"""

import os
import sys
import argparse
from pathlib import Path

from .auth import CLIAuthenticator
from .pod_manager import PodManager
from .ssh_connector import SSHConnector


class GodfatherCLI:
    """Main CLI application"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.godfather'
        self.api_base = os.getenv('GODFATHER_API_URL', 'http://localhost:5000')
        
        # Initialize components
        self.authenticator = CLIAuthenticator(self.api_base, self.config_dir)
        self.pod_manager = PodManager(self.api_base)
        self.ssh_connector = SSHConnector(self.api_base, self.config_dir)
    
    def print_banner(self):
        """Print CLI banner"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    AI Society Godfather CLI                  ║
║                   RunPod Environment Manager                 ║
╚══════════════════════════════════════════════════════════════╝
        """)
    
    def ensure_authenticated(self) -> bool:
        """Ensure user is authenticated"""
        if not self.authenticator.is_authenticated():
            return self.authenticator.authenticate()
        
        # Verify token is still valid
        if not self.authenticator.verify_token():
            print("❌ Token expired. Please re-authenticate.")
            return self.authenticator.authenticate()
        
        return True
    
    def list_pods(self):
        """List available public pods"""
        if not self.ensure_authenticated():
            return
        
        token = self.authenticator.get_token()
        self.pod_manager.list_pods(token)
    
    def connect_to_pod(self, pod_id: str = None):
        """Connect to a specific pod"""
        if not self.ensure_authenticated():
            return
        
        token = self.authenticator.get_token()
        
        # Select pod if not provided
        if not pod_id:
            pod_id = self.pod_manager.select_pod(token)
            if not pod_id:
                return
        
        print(f"🔌 Connecting to pod {pod_id[:8]}...")
        
        # Get connection details
        ssh_info = self.pod_manager.get_connection_info(pod_id, token)
        if not ssh_info:
            return
        
        # Fetch SSH key
        if not self.ssh_connector.fetch_ssh_key(token):
            return
        
        # Establish SSH connection
        self.ssh_connector.connect(ssh_info)
    
    def status(self):
        """Show CLI status and configuration"""
        print("📊 Godfather CLI Status\n")
        
        if self.authenticator.is_authenticated():
            print("🔐 Authentication: ✅ Authenticated")
            
            if self.authenticator.verify_token():
                print("🌐 API Connection: ✅ Connected")
            else:
                print("🌐 API Connection: ❌ Token expired")
        else:
            print("🔐 Authentication: ❌ Not authenticated")
        
        print(f"🏠 Config Directory: {self.config_dir}")
        print(f"🔗 API Endpoint: {self.api_base}")
    
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
            print("\n🎯 What would you like to do?")
            print("  1. List available pods")
            print("  2. Connect to a pod")
            print("  3. Show status")
            print("  4. Logout")
            print("  5. Exit")
            
            try:
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == '1':
                    self.list_pods()
                elif choice == '2':
                    self.connect_to_pod()
                elif choice == '3':
                    self.status()
                elif choice == '4':
                    self.logout()
                elif choice == '5':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
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
        """
    )
    
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
