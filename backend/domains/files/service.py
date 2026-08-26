"""SSH/SFTP file operations against a pod"""
import paramiko
import os
import stat
from typing import List, Dict, Optional
from shared.logger import get_logger

logger = get_logger(__name__)


class PodFileManager:
    def __init__(self, host: str, port: int = 22, username: str = 'root', ssh_key_path: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.client = None
        self.sftp = None

    def connect(self) -> bool:
        """Open the SSH/SFTP connection to the pod"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                # Key type isn't known ahead of time, so try each in turn
                private_key = None
                try:
                    private_key = paramiko.Ed25519Key.from_private_key_file(self.ssh_key_path)
                except paramiko.ssh_exception.SSHException:
                    try:
                        private_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
                    except paramiko.ssh_exception.SSHException:
                        try:
                            private_key = paramiko.ECDSAKey.from_private_key_file(self.ssh_key_path)
                        except paramiko.ssh_exception.SSHException:
                            private_key = paramiko.DSSKey.from_private_key_file(self.ssh_key_path)

                if not private_key:
                    return False

                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=private_key,
                    timeout=10,
                    look_for_keys=False,
                    allow_agent=False
                )
            else:
                return False

            self.sftp = self.client.open_sftp()
            return True

        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            return False

    def disconnect(self):
        """Close SSH/SFTP connection"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()

    def list_directory(self, path: str = '/workspace') -> List[Dict]:
        """List files and directories in the given path"""
        if not self.sftp:
            return []

        try:
            items = []
            for item in self.sftp.listdir_attr(path):
                file_info = {
                    'name': item.filename,
                    'type': 'directory' if self._is_directory(item) else 'file',
                    'size': item.st_size if hasattr(item, 'st_size') else 0,
                    'modified': item.st_mtime if hasattr(item, 'st_mtime') else 0,
                    'permissions': oct(item.st_mode)[-3:] if hasattr(item, 'st_mode') else '755'
                }
                items.append(file_info)

            return sorted(items, key=lambda x: (x['type'] == 'file', x['name']))

        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            return []

    def _is_directory(self, item) -> bool:
        return stat.S_ISDIR(item.st_mode) if hasattr(item, 'st_mode') else False

    def create_directory(self, path: str) -> bool:
        if not self.sftp:
            return False

        try:
            self.sftp.mkdir(path)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        if not self.sftp:
            return False

        try:
            self.sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            logger.error(f"Failed to upload file {local_path} to {remote_path}: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self.sftp:
            return False

        try:
            self.sftp.get(remote_path, local_path)
            return True
        except Exception as e:
            logger.error(f"Failed to download file {remote_path} to {local_path}: {e}")
            return False

    def delete_file(self, path: str) -> bool:
        if not self.sftp:
            return False

        try:
            self.sftp.remove(path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False

    def delete_directory(self, path: str) -> bool:
        """Delete a directory (must be empty)"""
        if not self.sftp:
            return False

        try:
            self.sftp.rmdir(path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete directory {path}: {e}")
            return False

    def execute_command(self, command: str) -> tuple:
        if not self.client:
            return "", "No SSH connection", 1

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')

            return stdout_data, stderr_data, exit_status

        except Exception as e:
            return "", str(e), 1

    def ensure_user_workspace(self, username: str) -> bool:
        """Ensure the user has their own workspace directory, creating and chowning it if missing"""
        user_workspace = f'/workspace/{username}'

        try:
            self.sftp.stat(user_workspace)
        except FileNotFoundError:
            if not self.create_directory(user_workspace):
                return False

        command = f'chown -R {self.username}:{self.username} {user_workspace} && chmod 755 {user_workspace}'
        stdout, stderr, exit_code = self.execute_command(command)

        return exit_code == 0

    def read_file(self, remote_path: str) -> Optional[str]:
        if not self.sftp:
            return None

        try:
            with self.sftp.open(remote_path, 'r') as f:
                return f.read().decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to read file {remote_path}: {e}")
            return None

    def write_file(self, remote_path: str, content: str) -> bool:
        if not self.sftp:
            return False

        try:
            with self.sftp.open(remote_path, 'w') as f:
                f.write(content.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Failed to write file {remote_path}: {e}")
            return False

    def rename(self, old_path: str, new_path: str) -> bool:
        if not self.sftp:
            return False

        try:
            self.sftp.rename(old_path, new_path)
            return True
        except Exception as e:
            logger.error(f"Failed to rename {old_path} to {new_path}: {e}")
            return False

    def copy(self, source_path: str, dest_path: str) -> bool:
        """Copy a file or directory (shells out to cp -r since SFTP has no recursive copy)"""
        if not self.client:
            return False

        try:
            command = f'cp -r "{source_path}" "{dest_path}"'
            stdout, stderr, exit_code = self.execute_command(command)
            return exit_code == 0
        except Exception as e:
            logger.error(f"Failed to copy {source_path} to {dest_path}: {e}")
            return False

    def search_files(self, base_path: str, query: str) -> List[Dict]:
        """Search for files/directories matching a name pattern under base_path"""
        if not self.client:
            return []

        try:
            command = f'find "{base_path}" -name "*{query}*" -type f -o -name "*{query}*" -type d'
            stdout, stderr, exit_code = self.execute_command(command)

            if exit_code != 0:
                return []

            results = []
            for line in stdout.strip().split('\n'):
                if line:
                    try:
                        stat_info = self.sftp.stat(line)
                        is_dir = stat.S_ISDIR(stat_info.st_mode)

                        results.append({
                            'path': line,
                            'name': line.split('/')[-1],
                            'type': 'directory' if is_dir else 'file',
                            'size': stat_info.st_size if not is_dir else 0,
                            'modified': stat_info.st_mtime
                        })
                    except Exception:
                        pass

            return results
        except Exception as e:
            logger.error(f"Failed to search files: {e}")
            return []

    def bulk_delete(self, paths: List[str]) -> tuple:
        """Delete multiple files/directories. Returns (success_count, failed_count)"""
        if not self.client:
            return (0, len(paths))

        success_count = 0
        failed_count = 0

        for path in paths:
            try:
                command = f'rm -rf "{path}"'
                stdout, stderr, exit_code = self.execute_command(command)

                if exit_code == 0:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {path}: {e}")
                failed_count += 1

        return (success_count, failed_count)
