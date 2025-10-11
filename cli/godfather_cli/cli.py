#!/usr/bin/env python3
"""
AI Society Godfather CLI
Command line interface for connecting to RunPod environments
"""

import os
import sys
import json
import requests
import subprocess
import getpass
from pathlib import Path
import argparse
from typing import Dict, List, Optional

class GodfatherCLI:
    def __init__(self):
        self.config_dir = Path.home() / '.godfather'
        self.config_file = self.config_dir / 'config.json'
        self.api_base = os.getenv('GODFATHER_API_URL', 'http://localhost:5000')
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def save_config(self):
        """Save configuration to file"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def print_banner(self):
        """Print CLI banner"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    AI Society Godfather CLI                  ║
║                   RunPod Environment Manager                 ║
╚══════════════════════════════════════════════════════════════╝
        """)
    
    def authenticate(self) -> bool:
        """Authenticate user via Discord/Clerk"""
        print("🔐 Authentication required...")
        print("Please visit the admin portal to get your authentication token:")
        print(f"   {self.api_base.replace(':5000', ':3000')}")
        print()
        
        token = getpass.getpass("Enter your authentication token: ").strip()
        if not token:
            print("❌ No token provided")
            return False
        
        # Verify token with backend
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(f'{self.api_base}/api/auth/verify', 
                                   json={'token': token}, 
                                   headers=headers, 
                                   timeout=10)
            
            if response.status_code == 200:
                self.config['token'] = token
                self.save_config()
                print("✅ Authentication successful!")
                return True
            else:
                error = response.json().get('error', 'Authentication failed')
                print(f"❌ Authentication failed: {error}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_public_pods(self) -> List[Dict]:
        """Get list of public pods available for connection"""
        if 'token' not in self.config:
            if not self.authenticate():
                return []
        
        try:
            headers = {'Authorization': f'Bearer {self.config["token"]}'}
            response = requests.get(f'{self.api_base}/api/pods/public', 
                                  headers=headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                return response.json().get('pods', [])
            elif response.status_code == 401:
                print("❌ Token expired. Please re-authenticate.")
                del self.config['token']
                self.save_config()
                return self.get_public_pods()  # Retry
            else:
                error = response.json().get('error', 'Failed to fetch pods')
                print(f"❌ Error: {error}")
                return []
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return []
    
    def list_pods(self):
        """List available public pods"""
        print("📡 Fetching available pods...")
        pods = self.get_public_pods()
        
        if not pods:
            print("😔 No public pods available at the moment.")
            print("   Ask an admin to create and make pods public.")
            return
        
        print(f"\n🚀 Found {len(pods)} available pod(s):\n")
        
        for i, pod in enumerate(pods, 1):
            status_emoji = "🟢" if pod.get('status') == 'RUNNING' else "🔴"
            print(f"  {i}. {status_emoji} {pod['name']}")
            print(f"     ID: {pod['id']}")
            print(f"     Status: {pod.get('status', 'Unknown')}")
            print(f"     Created: {pod.get('created_at', 'Unknown')}")
            print()
    
    def connect_to_pod(self, pod_id: Optional[str] = None):
        """Connect to a specific pod"""
        if not pod_id:
            # Interactive pod selection
            pods = self.get_public_pods()
            
            if not pods:
                print("😔 No public pods available.")
                return
            
            print("\n🚀 Available pods:")
            for i, pod in enumerate(pods, 1):
                status_emoji = "🟢" if pod.get('status') == 'RUNNING' else "🔴"
                print(f"  {i}. {status_emoji} {pod['name']} ({pod['id'][:8]}...)")
            
            try:
                choice = int(input(f"\nSelect a pod (1-{len(pods)}): "))
                if 1 <= choice <= len(pods):
                    pod_id = pods[choice - 1]['id']
                else:
                    print("❌ Invalid selection")
                    return
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Invalid input or cancelled")
                return
        
        print(f"🔌 Connecting to pod {pod_id[:8]}...")
        
        # Get connection details
        try:
            headers = {'Authorization': f'Bearer {self.config["token"]}'}
            response = requests.post(f'{self.api_base}/api/pods/{pod_id}/connect', 
                                   headers=headers, 
                                   timeout=10)
            
            if response.status_code == 200:
                ssh_info = response.json().get('ssh_info')
                self._establish_ssh_connection(ssh_info)
            else:
                error = response.json().get('error', 'Connection failed')
                print(f"❌ Connection failed: {error}")
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    def _establish_ssh_connection(self, ssh_info: Dict):
        """Establish SSH connection to pod"""
        host = ssh_info.get('host')
        port = ssh_info.get('port', 22)
        username = ssh_info.get('username', 'root')
        user_folder = ssh_info.get('user_folder', 'user')
        
        if not host:
            print("❌ No host information available")
            return
        
        print(f"🔗 Connecting to {host}:{port}")
        print(f"👤 User workspace: /workspace/{user_folder}")
        print("\n📁 Setting up your personal workspace...")
        
        # Create SSH connection with workspace setup
        setup_commands = [
            f"mkdir -p /workspace/{user_folder}",
            f"chown -R {username}:{username} /workspace/{user_folder}",
            f"cd /workspace/{user_folder}"
        ]
        
        ssh_command = [
            'ssh',
            '-t',
            '-p', str(port),
            f'{username}@{host}',
            ' && '.join(setup_commands) + ' && bash'
        ]
        
        try:
            print("🚪 Opening SSH session...")
            print("💡 You'll be in your personal workspace folder")
            print("🔒 You only have access to your own folder")
            print("📝 Type 'exit' to disconnect\n")
            
            # Execute SSH connection
            subprocess.run(ssh_command)
            print("\n👋 Disconnected from pod")
            
        except KeyboardInterrupt:
            print("\n👋 Connection cancelled")
        except FileNotFoundError:
            print("❌ SSH client not found. Please install OpenSSH client.")
        except subprocess.SubprocessError as e:
            print(f"❌ SSH connection failed: {e}")
    
    def status(self):
        """Show CLI status and configuration"""
        print("📊 Godfather CLI Status\n")
        
        if 'token' in self.config:
            print("🔐 Authentication: ✅ Authenticated")
            
            # Try to fetch user info
            try:
                headers = {'Authorization': f'Bearer {self.config["token"]}'}
                response = requests.post(f'{self.api_base}/api/auth/verify', 
                                       json={'token': self.config['token']}, 
                                       headers=headers, 
                                       timeout=5)
                
                if response.status_code == 200:
                    print("🌐 API Connection: ✅ Connected")
                else:
                    print("🌐 API Connection: ❌ Token expired")
            except:
                print("🌐 API Connection: ❌ Unable to connect")
        else:
            print("🔐 Authentication: ❌ Not authenticated")
        
        print(f"🏠 Config Directory: {self.config_dir}")
        print(f"🔗 API Endpoint: {self.api_base}")
    
    def logout(self):
        """Clear authentication token"""
        if 'token' in self.config:
            del self.config['token']
            self.save_config()
            print("👋 Logged out successfully")
        else:
            print("💡 You were not logged in")

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
    
    parser.add_argument('command', 
                       choices=['list', 'connect', 'status', 'logout', 'auth'],
                       help='Command to execute')
    parser.add_argument('pod_id', 
                       nargs='?', 
                       help='Pod ID for connect command')
    parser.add_argument('--api-url', 
                       help='Override API base URL')
    
    if len(sys.argv) == 1:
        # No arguments provided, show interactive menu
        cli = GodfatherCLI()
        cli.print_banner()
        
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
                    cli.list_pods()
                elif choice == '2':
                    cli.connect_to_pod()
                elif choice == '3':
                    cli.status()
                elif choice == '4':
                    cli.logout()
                elif choice == '5':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
        return
    
    args = parser.parse_args()
    
    if args.api_url:
        os.environ['GODFATHER_API_URL'] = args.api_url
    
    cli = GodfatherCLI()
    
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