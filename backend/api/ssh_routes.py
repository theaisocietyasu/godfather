"""SSH key routes"""
from flask import Blueprint, request, jsonify
from middleware.auth import require_token
from services.ssh_service import SSHService
from utils.logger import get_logger

logger = get_logger(__name__)

ssh_bp = Blueprint('ssh', __name__, url_prefix='/api')


@ssh_bp.route('/ssh-key', methods=['GET'])
@require_token
def get_ssh_key():
    """Get organization SSH private key for CLI users"""
    try:
        logger.info(f'SSH key request from user: {request.discord_user_id}')
        
        private_key = SSHService.get_private_key()
        if not private_key:
            return jsonify({'error': 'SSH key not configured'}), 500
        
        return jsonify({'private_key': private_key})
    except Exception as e:
        logger.error(f'Error in get_ssh_key: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
