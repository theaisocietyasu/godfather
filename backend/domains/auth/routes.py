"""Authentication routes"""
from flask import Blueprint, request, jsonify
from domains.auth.middleware import require_token
from domains.auth.service import AuthService
from shared.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/me', methods=['GET'])
@require_token
def me():
    """Return the caller's Discord user ID and whether they hold the admin role"""
    discord_user_id = request.discord_user_id
    is_admin = AuthService.verify_discord_admin(discord_user_id)
    return jsonify({
        'success': True,
        'discord_user_id': discord_user_id,
        'is_admin': is_admin
    })
