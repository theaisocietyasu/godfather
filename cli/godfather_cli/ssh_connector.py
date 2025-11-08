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
        
        print(f"🔗 Connecting to {host}:{port}")
        print(f"👤 User workspace: /workspace/users/{user_folder}")
        
        if is_admin:
            print("👑 Admin mode: Full system access")
        else:
            print("🔒 Restricted mode: Limited to your workspace")
        
        print("\n📁 Setting up your personal workspace...")
        
        # Setup user workspace
        admin_flag = "true" if is_admin else "false"
        setup_command = f"/usr/local/bin/godfather-user-setup.sh {user_folder} {admin_flag}"
        
        # Build SSH connection command
        ssh_command = [
            'ssh',
            '-t',
            '-i', str(self.ssh_key_file),
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-p', str(port),
            f'{username}@{host}',
            f'PROFILE=$({setup_command}) && source $PROFILE && exec bash'
        ]
        
        try:
            print("🚪 Opening SSH session...")
            
            if is_admin:
                print("✅ You have full admin access (sudo available)")
            else:
                print("💡 You're in your personal workspace")
                print("🤝 You can also access /workspace/shared for collaboration")
                print("⚠️  Restricted mode: No sudo access")
            
            print("📝 Type 'exit' to disconnect\n")
            
            # Execute SSH connection
            result = subprocess.run(ssh_command)
            
            if result.returncode != 0:
                print("\n❌ SSH connection failed!")
                print("\n⚠️  SSH Key Setup Required")
                print("=" * 60)
                print("The pod needs to have the SSH key configured first.")
                print("\nOption 1: Use the godfather-base Docker image (recommended)")
                print("  - The image automatically sets up SSH on startup")
                print("  - Image: theaisocietyasu/godfather-base:latest")
                print("\nOption 2: Manual setup in RunPod web terminal:")
                print("\n  mkdir -p /root/.ssh && \\")
                print(f'  echo "$GODFATHER_SSH_PUBLIC_KEY" >> /root/.ssh/authorized_keys && \\')
                print("  chmod 700 /root/.ssh && \\")
                print("  chmod 600 /root/.ssh/authorized_keys")
                print("\n💡 The GODFATHER_SSH_PUBLIC_KEY environment variable is already set in your pod.")
                print("=" * 60)
                return result.returncode
            else:
                print("\n👋 Disconnected from pod")
                return 0
            
        except KeyboardInterrupt:
            print("\n👋 Connection cancelled")
            return 1
        except FileNotFoundError:
            print("❌ SSH client not found. Please install OpenSSH client.")
            return 1
        except subprocess.SubprocessError as e:
            print(f"❌ SSH connection failed: {e}")
            return 1
