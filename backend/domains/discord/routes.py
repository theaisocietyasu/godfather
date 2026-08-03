"""Discord-related routes"""
from flask import Blueprint, jsonify
from domains.auth.middleware import require_auth
from domains.discord.service import DiscordService
from shared.logger import get_logger

logger = get_logger(__name__)

discord_bp = Blueprint('discord', __name__, url_prefix='/api/discord')


@discord_bp.route('/members', methods=['GET'])
@require_auth
def get_discord_members():
    """Fetch all Discord guild members (admin only)"""
    logger.info('Fetching Discord guild members')

    try:
        members = DiscordService.get_all_members()
        return jsonify({'members': members})
    except Exception as e:
        logger.error(f'Error fetching Discord members: {e}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
