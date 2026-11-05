"""Local SSH key pair, pod certificates, and the SSH connection to a pod."""

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from rich.panel import Panel

from .ui import BORDER, BOX, console, error, success

USERNAME_RE = re.compile(r'^[a-z0-9_][a-z0-9._-]{0,21}$')
POD_ID_RE = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
# The line in ~/.ssh/config that loads the Host blocks this CLI writes.
INCLUDE_MARK = '# Added by godfather-cli for VS Code Remote-SSH'


def forward_spec(value: str) -> Tuple[int, int]:
    """A (local port, pod port) pair from PORT or LOCAL:POD, for argparse."""
    parts = value.split(':')
    if len(parts) > 2 or not all(p.isdigit() and 1 <= int(p) <= 65535 for p in parts):
        raise argparse.ArgumentTypeError(f'{value!r} is not PORT or LOCAL:POD with ports from 1 to 65535')
    return int(parts[0]), int(parts[-1])


def host_alias(pod_id: str) -> str:
    """The ssh_config Host name of a pod."""
    return f'godfather-{pod_id}'


def host_block(alias: str, ssh_info: Dict, key_file: Path, cert_file: Path) -> str:
    """One ssh_config Host block for a pod, with the CLI key and the pod certificate."""
    return '\n'.join(
        [
            f'Host {alias}',
            f'    HostName {ssh_info["host"]}',
            f'    Port {ssh_info.get("port", 22)}',
            f'    User {ssh_info.get("username", "root")}',
            f'    IdentityFile "{key_file.as_posix()}"',
            f'    CertificateFile "{cert_file.as_posix()}"',
            '    IdentitiesOnly yes',
            '    StrictHostKeyChecking no',
            '    UserKnownHostsFile /dev/null',
            '    LogLevel ERROR',
            '',
        ]
    )


def replace_block(text: str, alias: str, block: str) -> str:
    """The config text with the Host block of alias replaced by block, or block appended."""
    kept: List[str] = []
    skipping = False
    for line in text.splitlines():
        if line.startswith('Host '):
            skipping = line.split()[1:] == [alias]
        if not skipping:
            kept.append(line)
    body = '\n'.join(kept).strip()
    return (body + '\n\n' if body else '') + block


def with_include(text: str, include_file: Path) -> str:
    """The ~/.ssh/config text with an Include of include_file at the top, added once."""
    line = f'Include "{include_file.as_posix()}"'
    if line in text.splitlines():
        return text
    # Include must come before the first Host block to apply to every host.
    return f'{INCLUDE_MARK}\n{line}\n\n{text}'


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
                    check=True,
                    capture_output=True,
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

    def pod_cert_file(self, pod_id: str) -> Path:
        """Where the certificate for one pod is kept for VS Code. Each pod has its own."""
        return self.ssh_key_dir / f'{pod_id}-cert.pub'

    def save_certificate(self, certificate: str, path: Optional[Path] = None) -> bool:
        """Store the certificate the API issued for this connection."""
        if not certificate:
            error("The server did not issue an SSH certificate. Update the CLI: pip install -U godfather-cli")
            return False
        try:
            (path or self.cert_file).write_text(certificate.strip() + '\n')
            return True
        except OSError as e:
            error(f"Failed to save SSH certificate: {e}")
            return False

    def build_command(self, ssh_info: Dict, forwards: Sequence[Tuple[int, int]] = ()) -> Optional[List[str]]:
        """Build the ssh command line for a pod. forwards holds (local port, pod port) pairs on 127.0.0.1."""
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
            '-i',
            str(self.key_file),
            '-o',
            f'CertificateFile={self.cert_file}',
            '-o',
            'IdentitiesOnly=yes',
            '-o',
            'StrictHostKeyChecking=no',
            '-o',
            'UserKnownHostsFile=/dev/null',
            '-o',
            'LogLevel=ERROR',
            '-p',
            str(port),
        ]
        for local, remote in forwards:
            command += ['-L', f'{local}:127.0.0.1:{remote}']
        command.append(f'{username}@{host}')
        # Member certificates carry a forced login command; admins ask for it explicitly
        if is_admin:
            command.append(f'/usr/local/bin/godfather-login --admin {user_folder}')
        return command

    def connect(self, ssh_info: Dict, forwards: Sequence[Tuple[int, int]] = ()) -> int:
        """Open an SSH session to the pod, with local forwards to ports on the pod."""
        command = self.build_command(ssh_info, forwards)
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
        for local, remote in forwards:
            details += f"\nForward http://localhost:{local} to port {remote} on the pod"

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
                "[dim]The pod must run the current ghcr.io/theaisocietyasu/godfather-base image and have been "
                "created after the Godfather 1.1.0 upgrade. Ask an admin to recreate it if it is older.[/dim]"
            )
            return result.returncode

        success("Disconnected")
        return 0

    def write_host(self, pod_id: str, ssh_info: Dict, ssh_config: Path) -> Optional[str]:
        """Write the Host block of a pod and include it from ssh_config. Returns the Host name, or None."""
        if not POD_ID_RE.match(pod_id) or not ssh_info.get('host'):
            error("Incomplete connection details from the server")
            return None
        alias = host_alias(pod_id)
        own_config = self.ssh_key_dir / 'config'
        block = host_block(alias, ssh_info, self.key_file, self.pod_cert_file(pod_id))
        try:
            old = own_config.read_text() if own_config.exists() else ''
            own_config.write_text(replace_block(old, alias, block))
            os.chmod(own_config, 0o600)
            ssh_config.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            text = ssh_config.read_text() if ssh_config.exists() else ''
            updated = with_include(text, own_config)
            if updated != text:
                ssh_config.write_text(updated)
                os.chmod(ssh_config, 0o600)
        except OSError as e:
            error(f"Failed to write the SSH config: {e}")
            return None
        return alias
