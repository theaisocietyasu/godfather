"""SSH keys and user certificates for pod access.

Two key pairs live in MongoDB and never leave the backend:
- backend: its public half goes into root's authorized_keys on each pod and
  the backend uses it for the web file manager.
- user_ca: pods trust it through TrustedUserCAKeys. Members and admins get
  short-lived certificates signed by it for their own locally generated keys.
The organization key used before v1.1.0 was handed to every CLI user and is
only read here as a fallback for pods created before then.
"""
import os
import re
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Optional
from shared.database import ssh_keys_collection
from shared.logger import get_logger

logger = get_logger(__name__)

BACKEND_KEY = 'backend'
USER_CA_KEY = 'user_ca'
LEGACY_KEY = 'organization'

LOGIN_COMMAND = '/usr/local/bin/godfather-login'
CERT_VALIDITY = '-5m:+12h'
ALLOWED_KEY_TYPES = (
    'ssh-ed25519',
    'ssh-rsa',
    'ecdsa-sha2-nistp256',
    'ecdsa-sha2-nistp384',
    'ecdsa-sha2-nistp521',
)
PUBLIC_KEY_RE = re.compile(r'^[a-z0-9-]+ [A-Za-z0-9+/=]+( [\x21-\x7e ]{0,200})?$')


def pod_principal(pod_id: str) -> str:
    """Certificate principal a pod accepts for root logins"""
    return f'gf-{pod_id}'


def safe_username(name: str) -> str:
    """Reduce a Discord username to characters safe for a Unix account and a path"""
    cleaned = re.sub(r'[^a-z0-9._-]', '', (name or '').lower()).lstrip('.-')[:22]
    return cleaned or 'user'


def is_valid_public_key(public_key: str) -> bool:
    """Accept a single-line OpenSSH public key of a supported type"""
    if not isinstance(public_key, str) or len(public_key) > 4096 or '\n' in public_key.strip():
        return False
    key = public_key.strip()
    return bool(PUBLIC_KEY_RE.match(key)) and key.split(' ', 1)[0] in ALLOWED_KEY_TYPES


class SSHService:
    """SSH key pairs and certificate signing for pod access"""

    @staticmethod
    def _get_or_create_keypair(key_type: str, comment: str) -> Optional[Dict]:
        existing = ssh_keys_collection.find_one({'key_type': key_type})
        if existing:
            return {'public_key': existing['public_key'], 'private_key': existing['private_key']}

        try:
            logger.info(f'Generating {key_type} SSH key pair')
            with tempfile.TemporaryDirectory() as tmpdir:
                key_path = os.path.join(tmpdir, 'key')
                subprocess.run(
                    ['ssh-keygen', '-q', '-t', 'ed25519', '-f', key_path, '-N', '', '-C', comment],
                    check=True, capture_output=True
                )
                with open(key_path) as f:
                    private_key = f.read().strip()
                with open(f'{key_path}.pub') as f:
                    public_key = f.read().strip()
        except (OSError, subprocess.CalledProcessError) as e:
            logger.error(f'Failed to generate {key_type} SSH key: {e}', exc_info=True)
            return None

        # Upsert so two workers racing on first use end up with one key
        ssh_keys_collection.update_one(
            {'key_type': key_type},
            {'$setOnInsert': {
                'key_type': key_type,
                'public_key': public_key,
                'private_key': private_key,
                'created_at': datetime.utcnow()
            }},
            upsert=True
        )
        stored = ssh_keys_collection.find_one({'key_type': key_type})
        return {'public_key': stored['public_key'], 'private_key': stored['private_key']}

    @staticmethod
    def get_backend_key() -> Optional[Dict]:
        """Key pair the backend uses to reach pods as root"""
        return SSHService._get_or_create_keypair(BACKEND_KEY, 'godfather-backend')

    @staticmethod
    def get_user_ca() -> Optional[Dict]:
        """Certificate authority key pair that pods trust for user logins"""
        return SSHService._get_or_create_keypair(USER_CA_KEY, 'godfather-user-ca')

    @staticmethod
    def get_file_manager_keys() -> List[str]:
        """Private keys to try for backend connections, current key first"""
        keys = []
        backend = SSHService.get_backend_key()
        if backend:
            keys.append(backend['private_key'])
        legacy = ssh_keys_collection.find_one({'key_type': LEGACY_KEY})
        if legacy:
            keys.append(legacy['private_key'])
        return keys

    @staticmethod
    def sign_user_key(public_key: str, pod_id: str, discord_user_id: str,
                      username: str, is_admin: bool) -> Optional[str]:
        """Sign a user's public key for one pod.

        Members get a forced command that drops them into their restricted
        account. Admins get an unrestricted root certificate.
        """
        if not is_valid_public_key(public_key):
            raise ValueError('Invalid SSH public key')

        ca = SSHService.get_user_ca()
        if not ca:
            return None

        username = safe_username(username)
        options = ['-O', 'clear', '-O', 'permit-pty', '-O', 'permit-port-forwarding']
        if is_admin:
            options += ['-O', 'permit-agent-forwarding']
        else:
            options += ['-O', f'force-command={LOGIN_COMMAND} {username}']

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                ca_path = os.path.join(tmpdir, 'ca')
                user_path = os.path.join(tmpdir, 'user')
                with open(ca_path, 'w') as f:
                    f.write(ca['private_key'] + '\n')
                os.chmod(ca_path, 0o600)
                with open(f'{user_path}.pub', 'w') as f:
                    f.write(public_key.strip() + '\n')

                subprocess.run(
                    ['ssh-keygen', '-q', '-s', ca_path,
                     '-I', f'discord:{discord_user_id}:{username}',
                     '-n', pod_principal(pod_id),
                     '-V', CERT_VALIDITY,
                     *options,
                     f'{user_path}.pub'],
                    check=True, capture_output=True
                )
                with open(f'{user_path}-cert.pub') as f:
                    return f.read().strip()
        except (OSError, subprocess.CalledProcessError) as e:
            logger.error(f'Failed to sign user key: {e}', exc_info=True)
            return None

    @staticmethod
    def save_key_to_temp_file(private_key: str) -> Optional[str]:
        """Save an SSH private key to a temp file with 600 permissions"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as key_file:
                key_file.write(private_key.strip() + '\n')
                key_path = key_file.name
            os.chmod(key_path, 0o600)
            return key_path
        except Exception as e:
            logger.error(f'Error saving key to temp file: {e}', exc_info=True)
            return None

    @staticmethod
    def cleanup_temp_key(key_path: str):
        """Remove a temporary key file"""
        try:
            if key_path and os.path.exists(key_path):
                os.unlink(key_path)
        except Exception as e:
            logger.error(f'Error cleaning up temp key: {e}')
