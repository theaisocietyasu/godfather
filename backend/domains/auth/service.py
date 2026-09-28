"""Authentication and authorization service"""
import requests
from typing import Dict, Optional
from shared.config import settings
from shared.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Discord-backed authentication and authorization"""

    @staticmethod
    def get_guild_member(discord_user_id: str) -> Optional[Dict]:
        """Fetch the guild member record from Discord (source of truth, not cached)"""
        if not discord_user_id or not discord_user_id.isdigit():
            return None

        try:
            headers = {'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}'}
            url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/members/{discord_user_id}'
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.warning(f'User {discord_user_id} not found in guild ({response.status_code})')
                return None

            return response.json()
        except Exception as e:
            logger.error(f'Discord member lookup error: {e}')
            return None

    @staticmethod
    def verify_discord_admin(discord_user_id: str) -> bool:
        """Return True if the user holds ADMIN_ROLE_ID in the guild"""
        if not settings.ADMIN_ROLE_ID:
            logger.error('ADMIN_ROLE_ID not configured')
            return False

        member = AuthService.get_guild_member(discord_user_id)
        if not member:
            return False

        return settings.ADMIN_ROLE_ID in member.get('roles', [])

    @staticmethod
    def verify_discord_member(discord_user_id: str) -> bool:
        """Return True if the user is a member of the guild"""
        return AuthService.get_guild_member(discord_user_id) is not None
