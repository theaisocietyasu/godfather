"""
File management utilities for RunPod connections
"""
import paramiko
import os
from typing import List, Dict, Optional

class PodFileManager:
    def __init__(self, host: str, port: int = 22, username: str = 'root', ssh_key_path: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.client = None
        self.sftp = None
    
    def connect(self) -> bool:
        """Establish SSH/SFTP connection to pod"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                # Try different key types
                private_key = None
                try:
                    # Try Ed25519 key first
                    private_key = paramiko.Ed25519Key.from_private_key_file(self.ssh_key_path)
                except paramiko.ssh_exception.SSHException:
                    try:
                        # Try RSA key
                        private_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
                    except paramiko.ssh_exception.SSHException:
                        try:
                            # Try ECDSA key
                            private_key = paramiko.ECDSAKey.from_private_key_file(self.ssh_key_path)
                        except paramiko.ssh_exception.SSHException:
                            # Try DSA key as last resort
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
                # No SSH key provided
                return False
            
            self.sftp = self.client.open_sftp()
            return True
            
        except Exception as e:
            print(f"SSH connection failed: {e}")
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
            print(f"Failed to list directory {path}: {e}")
            return []
    
    def _is_directory(self, item) -> bool:
        """Check if an item is a directory"""
        import stat
        return stat.S_ISDIR(item.st_mode) if hasattr(item, 'st_mode') else False
    
    def create_directory(self, path: str) -> bool:
        """Create a directory"""
        if not self.sftp:
            return False
        
        try:
            self.sftp.mkdir(path)
            return True
        except Exception as e:
            print(f"Failed to create directory {path}: {e}")
            return False
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to the pod"""
        if not self.sftp:
            return False
        
        try:
            self.sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            print(f"Failed to upload file {local_path} to {remote_path}: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from the pod"""
        if not self.sftp:
            return False
        
        try:
            self.sftp.get(remote_path, local_path)
            return True
        except Exception as e:
            print(f"Failed to download file {remote_path} to {local_path}: {e}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file"""
        if not self.sftp:
            return False
        
        try:
            self.sftp.remove(path)
            return True
        except Exception as e:
            print(f"Failed to delete file {path}: {e}")
            return False
    
    def delete_directory(self, path: str) -> bool:
        """Delete a directory (must be empty)"""
        if not self.sftp:
            return False
        
        try:
            self.sftp.rmdir(path)
            return True
        except Exception as e:
            print(f"Failed to delete directory {path}: {e}")
            return False
    
    def execute_command(self, command: str) -> tuple:
        """Execute a command on the remote server"""
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
        """Ensure user has their own workspace directory"""
        user_workspace = f'/workspace/{username}'
        
        try:
            # Check if directory exists
            self.sftp.stat(user_workspace)
        except FileNotFoundError:
            # Directory doesn't exist, create it
            if not self.create_directory(user_workspace):
                return False
        
        # Set proper permissions
        command = f'chown -R {self.username}:{self.username} {user_workspace} && chmod 755 {user_workspace}'
        stdout, stderr, exit_code = self.execute_command(command)
        
        return exit_code == 0