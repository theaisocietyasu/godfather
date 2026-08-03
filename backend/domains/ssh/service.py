"""SSH key management service"""
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Dict
from shared.database import ssh_keys_collection
from shared.logger import get_logger

logger = get_logger(__name__)


class SSHService:
    """SSH key generation and management for pod access"""

    @staticmethod
    def get_or_create_org_key() -> Optional[Dict]:
        """Get or create the organization-wide SSH key pair"""
        try:
            existing_key = ssh_keys_collection.find_one({'key_type': 'organization'})

            if existing_key:
                logger.info('Using existing organization SSH key')
                return {
                    'public_key': existing_key['public_key'],
                    'private_key': existing_key['private_key']
                }

            logger.info('Generating new organization SSH key pair')

            with tempfile.TemporaryDirectory() as tmpdir:
                key_path = f'{tmpdir}/godfather_key'

                subprocess.run([
                    'ssh-keygen', '-t', 'ed25519', '-f', key_path,
                    '-N', '', '-C', 'godfather-org-key'
                ], check=True, capture_output=True)

                with open(key_path, 'r') as f:
                    private_key = f.read()
                with open(f'{key_path}.pub', 'r') as f:
                    public_key = f.read()

            key_doc = {
                'key_type': 'organization',
                'public_key': public_key.strip(),
                'private_key': private_key.strip(),
                'created_at': datetime.utcnow()
            }
            ssh_keys_collection.insert_one(key_doc)
            logger.info('Organization SSH key generated and stored')

            return {
                'public_key': public_key.strip(),
                'private_key': private_key.strip()
            }
        except Exception as e:
            logger.error(f'Failed to generate SSH key: {e}', exc_info=True)
            return None

    @staticmethod
    def get_private_key() -> Optional[str]:
        """Get organization SSH private key"""
        try:
            ssh_key_doc = ssh_keys_collection.find_one({'key_type': 'organization'})

            if not ssh_key_doc:
                logger.error('No SSH key found in database')
                return None

            return ssh_key_doc['private_key']
        except Exception as e:
            logger.error(f'Error fetching SSH key: {e}', exc_info=True)
            return None

    @staticmethod
    def save_key_to_temp_file(private_key: str) -> Optional[str]:
        """Save SSH private key to a temp file with 600 permissions, as required by SSH"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as key_file:
                key_file.write(private_key)
                key_path = key_file.name

            os.chmod(key_path, 0o600)

            return key_path
        except Exception as e:
            logger.error(f'Error saving key to temp file: {e}', exc_info=True)
            return None

    @staticmethod
    def cleanup_temp_key(key_path: str):
        """Remove temporary key file"""
        try:
            if os.path.exists(key_path):
                os.unlink(key_path)
        except Exception as e:
            logger.error(f'Error cleaning up temp key: {e}')
