"""Local SSH key pair, pod certificates, and the SSH connection to a pod."""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from rich.panel import Panel

from .ui import console, success, error, BOX, BORDER

USERNAME_RE = re.compile(r'^[a-z0-9_][a-z0-9._-]{0,21}$')


class SSHConnector:
    """Keep a local key pair, store the certificate the API issues, and run ssh."""

    def __init__(self, config_dir: Path):
        self.ssh_key_dir = config_dir / 'ssh'
        self.key_file = self.ssh_key_dir / 'id_ed25519'
        self.cert_file = self.ssh_key_dir / 'id_ed25519-cert.pub'
        self.legacy_key_file = self.ssh_key_dir / 'godfather_key'

    def ensure_keypair(self) -> Optional[str]:
        """Create the local key pair on first use and return the public key."""
        # Versions before 1.1.0 stored a shared organization key here; it is no longer used
        if self.legacy_key_file.exists():
            try:
                self.legacy_key_file.unlink()
            except OSError:
                pass

        pub_file = Path(f'{self.key_file}.pub')
        if not self.key_file.exists() or not pub_file.exists():
            try:
                self.ssh_key_dir.mkdir(parents=True, exist_ok=True)
                os.chmod(self.ssh_key_dir, 0o700)
                for path in (self.key_file, pub_file):
                    if path.exists():
                        path.unlink()
                subprocess.run(
                    ['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', 'godfather-cli', '-f', str(self.key_file)],
                    check=True, capture_output=True
                )
            except FileNotFoundError:
                error("ssh-keygen not found. Install OpenSSH to use 'godfather connect'.")
                return None
            except (OSError, subprocess.CalledProcessError) as e:
                error(f"Failed to create an SSH key: {e}")
                return None

        try:
            return pub_file.read_text().strip()
        except OSError as e:
            error(f"Failed to read SSH public key: {e}")
            return None

    def save_certificate(self, certificate: str) -> bool:
        """Store the certificate the API issued for this connection."""
        if not certificate:
            error("The server did not issue an SSH certificate. Update the CLI: pip install -U godfather-cli")
            return False
        try:
            self.cert_file.write_text(certificate.strip() + '\n')
            return True
        except OSError as e:
            error(f"Failed to save SSH certificate: {e}")
            return False

    def build_command(self, ssh_info: Dict) -> Optional[List[str]]:
        """Build the ssh command line for a pod."""
        host = ssh_info.get('host')
        port = ssh_info.get('port', 22)
        username = ssh_info.get('username', 'root')
        user_folder = ssh_info.get('user_folder', '')
        is_admin = ssh_info.get('is_admin', False)

        if not host or not USERNAME_RE.match(user_folder):
            return None

        command = [
            'ssh',
            '-t',
            '-i', str(self.key_file),
            '-o', f'CertificateFile={self.cert_file}',
            '-o', 'IdentitiesOnly=yes',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'LogLevel=ERROR',
            '-p', str(port),
            f'{username}@{host}',
        ]
        # Member certificates carry a forced login command; admins ask for it explicitly
        if is_admin:
            command.append(f'/usr/local/bin/godfather-login --admin {user_folder}')
        return command

    def connect(self, ssh_info: Dict) -> int:
        """Open an SSH session to the pod."""
        command = self.build_command(ssh_info)
        if not command:
            error("Incomplete connection details from the server")
            return 1

        mode = "Administrator" if ssh_info.get('is_admin') else "Restricted user"
        details = (
            f"Host    {ssh_info['host']}:{ssh_info.get('port', 22)}\n"
            f"User    {ssh_info['user_folder']}\n"
            f"Auth    SSH certificate (valid 12 hours)\n"
            f"Mode    {mode}"
        )
        console.print(Panel(details, title="Connecting", border_style=BORDER, box=BOX))
        console.print()

        try:
            result = subprocess.run(command)
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

        console.print()
        if result.returncode == 255:
            error("SSH could not log in to the pod")
            console.print(
                "[dim]The pod must run the current theaisocietyasu/godfather-base image and have been "
                "created after the Godfather 1.1.0 upgrade. Ask an admin to recreate it if it is older.[/dim]"
            )
            return result.returncode

        success("Disconnected")
        return 0
