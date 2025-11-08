"""Authentication routes"""
from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from utils.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/verify', methods=['POST'])
def verify_auth():
    """Verify user has godfather role in Discord - Discord is source of truth"""
    logger.info('Auth verification request')
    
    data = request.get_json() or {}
    discord_user_id = data.get('discord_user_id')
    
    if not discord_user_id:
        logger.warning('No Discord user ID provided')
        return jsonify({'error': 'Discord user ID required'}), 400
    
    # Check godfather role directly from Discord (source of truth)
    is_admin = AuthService.verify_discord_admin(discord_user_id)
    
    if not is_admin:
        logger.warning(f'User {discord_user_id} does not have godfather role')
        return jsonify({'error': 'Godfather role required'}), 403
    
    logger.info(f'User {discord_user_id} successfully verified as admin')
    return jsonify({
        'success': True,
        'discord_user_id': discord_user_id,
        'is_admin': True
    })


