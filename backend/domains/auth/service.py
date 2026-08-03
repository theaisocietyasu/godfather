"""Authentication and authorization service"""
import requests
from typing import Optional, Dict
from shared.config import settings
from shared.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    """Discord-backed authentication and authorization"""

    @staticmethod
    def get_discord_user_from_token(access_token: str) -> Optional[Dict]:
        """Get Discord user info from OAuth access token"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
            }

            response = requests.get('https://discord.com/api/v10/users/@me', headers=headers)

            if response.status_code != 200:
                logger.error(f'Discord API error: {response.status_code}')
                return None

            return response.json()
        except Exception as e:
            logger.error(f'Error fetching Discord user: {e}')
            return None

    @staticmethod
    def verify_discord_admin(discord_user_id: str) -> bool:
        """Verify admin role directly against Discord guild membership (source of truth, not cached)"""
        try:
            if not settings.ADMIN_ROLE_ID:
                logger.error('ADMIN_ROLE_ID not configured in environment variables')
                return False

            headers = {
                'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}',
                'Content-Type': 'application/json'
            }

            url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/members/{discord_user_id}'
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                logger.warning(f'User {discord_user_id} not found in guild')
                return False

            member_data = response.json()

            user_roles = member_data.get('roles', [])
            logger.info(f'User {discord_user_id} roles: {user_roles}')
            has_admin = settings.ADMIN_ROLE_ID in user_roles

            logger.info(f'User {discord_user_id} admin check: {has_admin} (checking role ID: {settings.ADMIN_ROLE_ID})')
            return has_admin

        except Exception as e:
            logger.error(f'Discord verification error: {e}')
            return False

    @staticmethod
    def verify_discord_member(discord_user_id: str) -> bool:
        """Verify if user is a member of the Discord server"""
        try:
            headers = {
                'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}',
                'Content-Type': 'application/json'
            }

            url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/members/{discord_user_id}'
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                logger.info(f'User {discord_user_id} is a member of the Discord server')
                return True
            else:
                logger.warning(f'User {discord_user_id} is not a member of the Discord server')
                return False

        except Exception as e:
            logger.error(f'Discord member verification error: {e}')
            return False
