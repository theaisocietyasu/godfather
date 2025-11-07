"""Authentication routes"""
from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from services.discord_service import DiscordService
from utils.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/verify', methods=['POST'])
def verify_auth():
    """Verify user authentication and Discord admin status"""
    logger.info('Auth verification request')
    
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        logger.warning('No token provided')
        return jsonify({'error': 'No token provided'}), 400
    
    # Verify Clerk token
    user_data = AuthService.verify_clerk_token(token)
    if not user_data:
        logger.warning('Invalid token')
        return jsonify({'error': 'Invalid token'}), 401
    
    clerk_user_id = user_data.get('sub')
    if not clerk_user_id:
        logger.error('No Clerk user ID in token')
        return jsonify({'error': 'Invalid token'}), 401
    
    # Fetch Discord ID from Clerk
    discord_user_id = AuthService.get_discord_id_from_clerk(clerk_user_id)
    
    if not discord_user_id:
        logger.warning('Discord account not linked')
        return jsonify({
            'error': 'Discord account not linked',
            'hint': 'Go to your Clerk account settings and ensure Discord is connected'
        }), 401
    
    # Verify admin role
    is_admin = AuthService.verify_discord_admin(discord_user_id)
    
    if not is_admin:
        logger.warning(f'User {discord_user_id} does not have admin role')
        return jsonify({'error': 'Admin access required'}), 403
    
    # Store user in database
    AuthService.store_user(
        clerk_id=clerk_user_id,
        discord_id=discord_user_id,
        username=user_data.get('username')
    )
    
    logger.info(f'User {discord_user_id} successfully authenticated')
    return jsonify({'success': True, 'user': user_data})
