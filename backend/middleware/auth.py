"""Authentication middleware"""
from functools import wraps
from flask import request, jsonify
from services.auth_service import AuthService
from services.discord_service import DiscordService
from config.database import users_collection
from utils.logger import get_logger

logger = get_logger(__name__)


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        logger.info('Authenticating request')
        
        token = request.headers.get('Authorization')
        if not token:
            logger.warning('No token provided')
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Verify token
        user_data = AuthService.verify_clerk_token(token)
        if not user_data:
            logger.warning('Invalid token')
            return jsonify({'error': 'Invalid token'}), 401
        
        clerk_user_id = user_data.get('sub')
        logger.info(f'Token verified for user: {clerk_user_id}')
        
        # Look up user in database
        user_doc = users_collection.find_one({'clerk_id': clerk_user_id})
        
        if not user_doc:
            logger.warning(f'User {clerk_user_id} not found in database')
            return jsonify({'error': 'User not authenticated. Please refresh the page.'}), 401
        
        discord_user_id = user_doc.get('discord_id')
        if not discord_user_id:
            logger.error(f'User {clerk_user_id} has no Discord ID')
            return jsonify({'error': 'Discord account not linked'}), 401
        
        logger.info(f'Found Discord ID: {discord_user_id}')
        
        # Verify admin role
        admin_role_id = DiscordService.find_admin_role_id()
        if not admin_role_id:
            logger.error('Admin role not found in guild')
            return jsonify({'error': 'Admin role not configured'}), 500
        
        if not DiscordService.check_user_has_role(discord_user_id, admin_role_id):
            logger.warning(f'User {discord_user_id} does not have admin role')
            return jsonify({'error': 'Admin access required'}), 403
        
        logger.info('Authorization successful')
        
        # Attach user info to request
        request.user = user_data
        request.discord_user_id = discord_user_id
        
        return f(*args, **kwargs)
    
    return decorated


def require_token(f):
    """Decorator for endpoints that only need token verification (no admin check)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_data = AuthService.verify_clerk_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid token'}), 401
        
        request.user = user_data
        return f(*args, **kwargs)
    
    return decorated
