"""Authentication middleware"""
from functools import wraps
from flask import request, jsonify
from services.auth_service import AuthService
from utils.logger import get_logger

logger = get_logger(__name__)


def require_auth(f):
    """Decorator to require authentication and admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        logger.info('Authenticating request')
        
        # Get Discord user ID from session/request
        # This will be passed from the frontend after Discord OAuth
        discord_user_id = request.headers.get('X-Discord-User-ID')
        
        if not discord_user_id:
            # Try to get from JSON body as fallback
            if request.json:
                discord_user_id = request.json.get('discord_user_id')
        
        if not discord_user_id:
            logger.warning('No Discord user ID provided')
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify admin role directly from Discord (source of truth)
        is_admin = AuthService.verify_discord_admin(discord_user_id)
        
        if not is_admin:
            logger.warning(f'User {discord_user_id} does not have admin role')
            return jsonify({'error': 'Admin access required'}), 403
        
        logger.info(f'Authorization successful for {discord_user_id}')
        
        # Attach user info to request
        request.discord_user_id = discord_user_id
        
        return f(*args, **kwargs)
    
    return decorated


def require_token(f):
    """Decorator for endpoints that only need basic auth (no admin check)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        discord_user_id = request.headers.get('X-Discord-User-ID')
        
        if not discord_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        request.discord_user_id = discord_user_id
        return f(*args, **kwargs)
    
    return decorated
