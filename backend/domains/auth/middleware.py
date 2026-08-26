"""Authentication middleware"""
from functools import wraps
from flask import request, jsonify
from domains.auth.service import AuthService
from shared.logger import get_logger

logger = get_logger(__name__)


def require_auth(f):
    """Require the godfather (admin) role, checked live against Discord on each request"""
    @wraps(f)
    def decorated(*args, **kwargs):
        logger.info('Authenticating request')

        # Discord user ID is set by the frontend after Discord OAuth
        discord_user_id = request.headers.get('X-Discord-User-ID')

        if not discord_user_id:
            # Fall back to JSON body
            if request.json:
                discord_user_id = request.json.get('discord_user_id')

        if not discord_user_id:
            logger.warning('No Discord user ID provided')
            return jsonify({'error': 'Authentication required'}), 401

        # Verify godfather role directly from Discord (source of truth)
        is_admin = AuthService.verify_discord_admin(discord_user_id)

        if not is_admin:
            logger.warning(f'User {discord_user_id} does not have godfather role')
            return jsonify({'error': 'Godfather role required'}), 403

        logger.info(f'Authorization successful for {discord_user_id}')

        request.discord_user_id = discord_user_id

        return f(*args, **kwargs)

    return decorated


def require_token(f):
    """Require a Discord user ID header, verified live against Discord guild
    membership (source of truth), without the admin role check.

    The header is client-supplied and must not be trusted at face value -
    without the membership check below, anyone could set an arbitrary
    X-Discord-User-ID and reach endpoints that hand out pod access or the
    organization SSH key.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        discord_user_id = request.headers.get('X-Discord-User-ID')

        if not discord_user_id:
            return jsonify({'error': 'Authentication required'}), 401

        if not AuthService.verify_discord_member(discord_user_id):
            logger.warning(f'Rejected request: {discord_user_id} is not a verified Discord member')
            return jsonify({'error': 'Authentication required'}), 401

        request.discord_user_id = discord_user_id
        return f(*args, **kwargs)

    return decorated
