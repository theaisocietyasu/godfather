"""Authentication middleware"""
from functools import wraps
from typing import Optional
from flask import request, jsonify
from domains.auth import tokens
from domains.auth.service import AuthService
from shared.config import settings
from shared.logger import get_logger

logger = get_logger(__name__)


def authenticated_user_id() -> Optional[str]:
    """Return the Discord user ID from a valid bearer token, or None"""
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None

    payload = tokens.verify(header[len('Bearer '):].strip(), settings.GODFATHER_TOKEN_SECRET)
    if not payload:
        return None

    return payload['sub']


def require_auth(f):
    """Require a signed token whose user holds the admin role, checked live against Discord"""
    @wraps(f)
    def decorated(*args, **kwargs):
        discord_user_id = authenticated_user_id()
        if not discord_user_id:
            return jsonify({'error': 'Authentication required'}), 401

        if not AuthService.verify_discord_admin(discord_user_id):
            logger.warning(f'User {discord_user_id} does not have the admin role')
            return jsonify({'error': 'Admin role required'}), 403

        request.discord_user_id = discord_user_id
        return f(*args, **kwargs)

    return decorated


def require_token(f):
    """Require a signed token whose user is a member of the Discord server, checked live"""
    @wraps(f)
    def decorated(*args, **kwargs):
        discord_user_id = authenticated_user_id()
        if not discord_user_id:
            return jsonify({'error': 'Authentication required'}), 401

        if not AuthService.verify_discord_member(discord_user_id):
            logger.warning(f'Rejected request: {discord_user_id} is not a Discord server member')
            return jsonify({'error': 'Must be a member of the AI Society Discord server'}), 403

        request.discord_user_id = discord_user_id
        return f(*args, **kwargs)

    return decorated
