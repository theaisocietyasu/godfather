"""SSH key retrieval and the SSH connection to a pod."""

import os
import subprocess
import requests
from pathlib import Path
from typing import Dict

from rich.panel import Panel
from rich.rule import Rule

from .ui import console, success, error, spinner, BOX, BORDER, PURPLE


class SSHConnector:
    """Fetch the user's SSH key and hand off to the system ssh client."""

    def __init__(self, api_base: str, config_dir: Path):
        self.api_base = api_base
        self.ssh_key_dir = config_dir / 'ssh'
        self.ssh_key_file = self.ssh_key_dir / 'godfather_key'

    def fetch_ssh_key(self, discord_user_id: str) -> bool:
        """Fetch the SSH private key from the API and write it to disk."""
        try:
            with spinner("Fetching SSH key..."):
                headers = {'X-Discord-User-ID': discord_user_id}
                response = requests.get(
                    f'{self.api_base}/api/ssh-key',
                    headers=headers,
                    timeout=10
                )

            if response.status_code != 200:
                try:
                    message = response.json().get('error', 'Unknown error')
                except ValueError:
                    message = 'Unknown error'
                error(f"Failed to fetch SSH key: {message}")
                return False

            try:
                private_key = response.json().get('private_key')
            except ValueError:
                error("Received an unreadable response from the server")
                return False

            if not private_key:
                error("No SSH key returned from the API")
                return False

            if '\\n' in private_key:
                private_key = private_key.replace('\\n', '\n')

            if not private_key.endswith('\n'):
                private_key += '\n'

            self.ssh_key_dir.mkdir(exist_ok=True)

            with open(self.ssh_key_file, 'w') as f:
                f.write(private_key)

            os.chmod(self.ssh_key_file, 0o600)

            return True

        except requests.ConnectionError:
            error(f"Couldn't reach {self.api_base}")
            return False
        except requests.RequestException as e:
            error(f"Failed to fetch SSH key: {e}")
            return False
        except IOError as e:
            error(f"Failed to save SSH key: {e}")
            return False

    def connect(self, ssh_info: Dict) -> int:
        """Open an SSH session to the pod."""
        host = ssh_info.get('host')
        port = ssh_info.get('port', 22)
        username = ssh_info.get('username', 'root')
        user_folder = ssh_info.get('user_folder', 'user')
        is_admin = ssh_info.get('is_admin', False)

        if not host:
            error("No host information available for this pod")
            return 1

        mode = "Administrator" if is_admin else "Restricted user"
        details = (
            f"Host    {host}:{port}\n"
            f"User    {user_folder}\n"
            f"Auth    SSH key\n"
            f"Mode    {mode}"
        )
        console.print(Panel(details, title="Connecting", border_style=BORDER, box=BOX))
        console.print()

        admin_flag = "true" if is_admin else "false"
        setup_command = f"SCRIPT=$(/usr/local/bin/godfather-user-setup.sh {user_folder} {admin_flag}) && bash $SCRIPT"

        ssh_command = [
            'ssh',
            '-t',
            '-i', str(self.ssh_key_file),
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'LogLevel=ERROR',
            '-p', str(port),
            f'{username}@{host}',
            setup_command
        ]

        try:
            result = subprocess.run(ssh_command)

            if result.returncode != 0:
                console.print()
                console.print(Rule("SSH key not set up on this pod", style="red"))
                console.print()
                console.print(
                    "The pod needs the Godfather SSH key added before you can connect.\n\n"
                    "[bold]Recommended:[/bold] use the godfather-base image, which configures this "
                    "automatically.\n"
                    f"  Image: [bold {PURPLE}]theaisocietyasu/godfather-base:latest[/bold {PURPLE}]\n\n"
                    "[bold]Manual fix[/bold] (from the RunPod web terminal):\n"
                    "  mkdir -p /root/.ssh &&\n"
                    "  echo \"$GODFATHER_SSH_PUBLIC_KEY\" >> /root/.ssh/authorized_keys &&\n"
                    "  chmod 700 /root/.ssh &&\n"
                    "  chmod 600 /root/.ssh/authorized_keys\n\n"
                    "[dim]GODFATHER_SSH_PUBLIC_KEY is already set as an env var on your pod.[/dim]"
                )
                console.print()
                return result.returncode
            else:
                console.print()
                success("Disconnected")
                return 0

        except KeyboardInterrupt:
            console.print()
            console.print("[yellow]Connection cancelled[/yellow]")
            return 1
        except FileNotFoundError:
            error("SSH client not found. Install OpenSSH to use 'godfather connect'.")
            return 1
        except subprocess.SubprocessError as e:
            error(f"SSH connection failed: {e}")
            return 1
