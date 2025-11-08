"""Authentication and authorization service"""
import requests
from typing import Optional, Dict
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    """Handle authentication and authorization"""
    
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
        """Verify if user has Admin role in Discord - source of truth"""
        try:
            # Check if ADMIN_ROLE_ID is configured
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
            
            # Check if user has the Admin role by ID
            user_roles = member_data.get('roles', [])
            has_admin = settings.ADMIN_ROLE_ID in user_roles
            
            logger.info(f'User {discord_user_id} admin check: {has_admin} (checking role ID: {settings.ADMIN_ROLE_ID})')
            return has_admin
            
        except Exception as e:
            logger.error(f'Discord verification error: {e}')
            return False
