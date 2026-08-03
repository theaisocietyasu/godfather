"""Authentication routes"""
from flask import Blueprint, request, jsonify
from domains.auth.service import AuthService
from shared.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/verify', methods=['POST'])
def verify_auth():
    """Verify user authentication and check their role level"""
    logger.info('Auth verification request')

    data = request.get_json() or {}
    discord_user_id = data.get('discord_user_id')

    if not discord_user_id:
        logger.warning('No Discord user ID provided')
        return jsonify({'error': 'Discord user ID required'}), 400

    is_admin = AuthService.verify_discord_admin(discord_user_id)
    is_member = AuthService.verify_discord_member(discord_user_id)

    if not is_member:
        logger.warning(f'User {discord_user_id} is not a member of the Discord server')
        return jsonify({'error': 'Must be a member of the AI Society Discord server'}), 403

    logger.info(f'User {discord_user_id} authenticated - Admin: {is_admin}')
    return jsonify({
        'success': True,
        'discord_user_id': discord_user_id,
        'is_admin': is_admin
    })
