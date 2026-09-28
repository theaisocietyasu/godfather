"""Pod management routes"""
from flask import Blueprint, request, jsonify
from domains.auth.middleware import require_auth, require_token
from domains.pods.service import PodService
from domains.ssh.service import SSHService, is_valid_public_key, safe_username
from domains.discord.service import DiscordService
from shared.config import settings
from shared.logger import get_logger
import secrets

logger = get_logger(__name__)

pods_bp = Blueprint('pods', __name__, url_prefix='/api/pods')


@pods_bp.route('', methods=['GET'])
@require_auth
def get_pods():
    """Get all pods"""
    try:
        logger.info(f'Get all pods request from user: {request.discord_user_id}')
        pods = PodService.get_all_pods()
        return jsonify({'pods': pods})
    except Exception as e:
        logger.error(f'Error in get_pods: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@pods_bp.route('', methods=['POST'])
@require_auth
def create_pod():
    """Create a new pod"""
    try:
        data = request.get_json(silent=True) or {}
        logger.info(f'Create pod request: {data.get("name")}')

        backend_key = SSHService.get_backend_key()
        user_ca = SSHService.get_user_ca()
        if not backend_key or not user_ca:
            return jsonify({'error': 'Failed to setup SSH access'}), 500

        config = {
            'name': data.get('name', f'pod-{secrets.token_hex(4)}'),
            'image_name': data.get('image_name', 'theaisocietyasu/godfather-base:latest'),
            'gpu_type_id': data.get('gpu_type_id', 'NVIDIA RTX A4000'),
            'cloud_type': data.get('cloud_type', 'COMMUNITY'),
            'volume_in_gb': data.get('volume_in_gb', 1),
            'container_disk_in_gb': data.get('container_disk_in_gb', 2),
            'ports': data.get('ports', '22/tcp'),
            'volume_mount_path': data.get('volume_mount_path', '/workspace'),
            'is_public': data.get('is_public', False),
            'allowed_users': data.get('allowed_users', []),
            'use_cpu_only': bool(data.get('use_cpu_only', False)),
            'env': data.get('env', {})
        }
        if data.get('instance_ids'):
            config['instance_ids'] = data['instance_ids']

        pod = PodService.create_pod(
            config=config,
            creator_id=request.discord_user_id,
            ssh_public_key=backend_key['public_key'],
            ssh_ca_public_key=user_ca['public_key']
        )

        if pod:
            return jsonify({'success': True, 'pod': pod})
        else:
            return jsonify({'error': 'Failed to create pod'}), 500

    except Exception as e:
        logger.error(f'Error in create_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@pods_bp.route('/<pod_id>', methods=['GET'])
@require_auth
def get_pod_details(pod_id):
    """Get detailed information about a specific pod"""
    try:
        logger.info(f'Get pod details: {pod_id}')
        pod = PodService.get_pod(pod_id)

        if not pod:
            return jsonify({'error': 'Pod not found'}), 404

        return jsonify({'pod': pod})
    except Exception as e:
        logger.error(f'Error in get_pod_details: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@pods_bp.route('/<pod_id>', methods=['PUT'])
@require_auth
def update_pod(pod_id):
    """Update pod configuration"""
    try:
        data = request.get_json(silent=True) or {}
        logger.info(f'Update pod: {pod_id}')

        PodService.update_pod(pod_id, data)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error in update_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@pods_bp.route('/<pod_id>/action', methods=['POST'])
@require_auth
def pod_action(pod_id):
    """Perform actions on a pod (start, stop, restart, terminate)"""
    try:
        data = request.get_json(silent=True) or {}
        action = data.get('action')
        logger.info(f'Pod action: {action} on {pod_id}')

        if action == 'stop':
            result = PodService.stop_pod(pod_id)
        elif action == 'start':
            result = PodService.start_pod(pod_id)
        elif action == 'restart':
            result = PodService.restart_pod(pod_id)
        elif action == 'terminate':
            result = PodService.terminate_pod(pod_id)
        else:
            return jsonify({'error': 'Invalid action'}), 400

        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f'Error in pod_action: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@pods_bp.route('/public', methods=['GET'])
@require_token
def get_public_pods():
    """Get pods accessible to CLI users"""
    try:
        discord_user_id = request.discord_user_id

        pods = PodService.get_accessible_pods(discord_user_id)
        return jsonify({'pods': pods})
    except Exception as e:
        logger.error(f'Error in get_public_pods: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@pods_bp.route('/<pod_id>/connect', methods=['POST'])
@require_token
def connect_to_pod(pod_id):
    """Sign the caller's SSH public key for this pod and return connection details"""
    try:
        logger.info(f'Connect request for pod: {pod_id}')

        discord_user_id = request.discord_user_id
        data = request.get_json(silent=True) or {}
        public_key = data.get('public_key', '')

        if not is_valid_public_key(public_key):
            return jsonify({'error': 'A valid SSH public key is required. Update the CLI: pip install -U godfather-cli'}), 400

        member = DiscordService.get_member(discord_user_id)
        if not member:
            return jsonify({'error': 'Must be a member of the AI Society Discord server'}), 403

        is_admin = settings.ADMIN_ROLE_ID in member.get('roles', []) if settings.ADMIN_ROLE_ID else False

        if not is_admin and not PodService.check_pod_access(pod_id, discord_user_id):
            return jsonify({'error': 'Pod not accessible'}), 403

        ssh_info = PodService.get_pod_ssh_info(pod_id)
        if not ssh_info:
            return jsonify({'error': 'Pod network information not available'}), 503

        # Discord username gives a stable per-user workspace folder and account
        username = safe_username((member.get('user') or {}).get('username') or discord_user_id)

        certificate = SSHService.sign_user_key(public_key, pod_id, discord_user_id, username, is_admin)
        if not certificate:
            return jsonify({'error': 'Failed to issue SSH certificate'}), 500

        ssh_info['user_folder'] = username
        ssh_info['is_admin'] = is_admin
        ssh_info['certificate'] = certificate

        return jsonify({'ssh_info': ssh_info})
    except Exception as e:
        logger.error(f'Error in connect_to_pod: {e}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
