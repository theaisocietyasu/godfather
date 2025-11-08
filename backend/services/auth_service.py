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
            
            # Get all roles in the guild
            roles_url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/roles'
            roles_response = requests.get(roles_url, headers=headers)
            
            if roles_response.status_code != 200:
                return False
            
            roles = roles_response.json()
            admin_role_id = None
            
            # Find the Admin role
            for role in roles:
                if role.get('name', '').lower() == 'admin':
                    admin_role_id = role['id']
                    break
            
            if not admin_role_id:
                logger.error('Admin role not found in guild')
                return False
            
            # Check if user has the Admin role
            user_roles = member_data.get('roles', [])
            has_admin = admin_role_id in user_roles
            
            logger.info(f'User {discord_user_id} admin check: {has_admin}')
            return has_admin
            
        except Exception as e:
            logger.error(f'Discord verification error: {e}')
            return False
