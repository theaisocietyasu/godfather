"""CLI SSH Connection module"""

import os
import subprocess
import requests
from pathlib import Path
from typing import Dict, Optional


class SSHConnector:
    """Handle SSH connections to pods"""
    
    def __init__(self, api_base: str, config_dir: Path):
        self.api_base = api_base
        self.ssh_key_dir = config_dir / 'ssh'
        self.ssh_key_file = self.ssh_key_dir / 'godfather_key'
    
    def fetch_ssh_key(self, discord_user_id: str) -> bool:
        """Fetch SSH private key from API and save it"""
        print("🔑 Fetching SSH key...")
        try:
            headers = {'X-Discord-User-ID': discord_user_id}
            response = requests.get(
                f'{self.api_base}/api/ssh-key',
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                error = response.json().get('error', 'Unknown error')
                print(f"❌ Failed to fetch SSH key: {error}")
                return False
            
            private_key = response.json().get('private_key')
            if not private_key:
                print("❌ No SSH key returned from API")
                return False
            
            # Ensure proper formatting
            if '\\n' in private_key:
                private_key = private_key.replace('\\n', '\n')
            
            if not private_key.endswith('\n'):
                private_key += '\n'
            
            # Save SSH key
            self.ssh_key_dir.mkdir(exist_ok=True)
            
            with open(self.ssh_key_file, 'w') as f:
                f.write(private_key)
            
            # Set correct permissions
            os.chmod(self.ssh_key_file, 0o600)
            print("✅ SSH key ready")
            
            return True
            
        except requests.RequestException as e:
            print(f"❌ Failed to fetch SSH key: {e}")
            return False
        except IOError as e:
            print(f"❌ Failed to save SSH key: {e}")
            return False
    
    def connect(self, ssh_info: Dict) -> int:
        """Establish SSH connection to pod"""
        host = ssh_info.get('host')
        port = ssh_info.get('port', 22)
        username = ssh_info.get('username', 'root')
        user_folder = ssh_info.get('user_folder', 'user')
        is_admin = ssh_info.get('is_admin', False)
        
        if not host:
            print("❌ No host information available")
            return 1
        
        print("\n" + "━" * 78)
        print(" 🔗 GODFATHER POD CONNECTION")
        print("━" * 78)
        print(f" 🌐 Host:        {host}:{port}")
        print(f" 👤 User:        {user_folder}")
        print(f" 🔑 Auth:        SSH Key")
        
        if is_admin:
            print(f" 👑 Mode:        Administrator (Full Access)")
        else:
            print(f" 🔒 Mode:        Restricted User")
        
        print("━" * 78)
        print()
        
        print("🔐 Establishing secure connection...")
        
        # Setup user workspace and get the profile/script to source
        admin_flag = "true" if is_admin else "false"
        setup_command = f"SCRIPT=$(/usr/local/bin/godfather-user-setup.sh {user_folder} {admin_flag}) && bash $SCRIPT"
        
        # Build SSH connection command
        ssh_command = [
            'ssh',
            '-t',
            '-i', str(self.ssh_key_file),
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'LogLevel=ERROR',  # Suppress SSH warnings
            '-p', str(port),
            f'{username}@{host}',
            setup_command
        ]
        
        try:
            # Execute SSH connection
            result = subprocess.run(ssh_command)
            
            if result.returncode != 0:
                print("\n" + "━" * 78)
                print(" ❌ CONNECTION FAILED")
                print("━" * 78)
                print()
                print(" SSH Key Setup Required")
                print()
                print("The pod needs to have the SSH key configured first.")
                print()
                print("✅ Recommended Solution:")
                print(" Use the godfather-base Docker image which auto-configures SSH")
                print(" Image: theaisocietyasu/godfather-base:latest")
                print()
                print("🔧 Manual Setup (if needed):")
                print(" 1. Open RunPod web terminal")
                print(" 2. Run these commands:")
                print()
                print(" mkdir -p /root/.ssh && \\")
                print('      echo "$GODFATHER_SSH_PUBLIC_KEY" >> /root/.ssh/authorized_keys && \\')
                print(" chmod 700 /root/.ssh && \\")
                print(" chmod 600 /root/.ssh/authorized_keys")
                print()
                print("💡 The GODFATHER_SSH_PUBLIC_KEY variable is already set in your pod")
                print("━" * 78)
                return result.returncode
            else:
                print("\n" + "━" * 78)
                print(" 👋 DISCONNECTED")
                print("━" * 78)
                print(" Thank you for using Godfather! See you next time! ")
                print("━" * 78 + "\n")
                return 0
            
        except KeyboardInterrupt:
            print("\n\n" + "━" * 78)
            print(" ⚠️ CONNECTION CANCELLED")
            print("━" * 78 + "\n")
            return 1
        except FileNotFoundError:
            print("\n❌ SSH client not found. Please install OpenSSH client.")
            return 1
        except subprocess.SubprocessError as e:
            print(f"\n❌ SSH connection failed: {e}")
            return 1
