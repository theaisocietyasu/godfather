"""Discord API service"""
import requests
from typing import Optional, List, Dict
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class DiscordService:
    """Handle Discord API operations"""
    
    @staticmethod
    def get_member(discord_user_id: str) -> Optional[Dict]:
        """Get Discord guild member information"""
        try:
            headers = {
                'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/members/{discord_user_id}'
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f'Failed to fetch Discord member: {response.status_code}')
                return None
            
            return response.json()
        except Exception as e:
            logger.error(f'Error fetching Discord member: {e}', exc_info=True)
            return None
    
    @staticmethod
    def get_guild_roles() -> List[Dict]:
        """Get all roles in the Discord guild"""
        try:
            headers = {
                'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/roles'
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f'Failed to fetch guild roles: {response.status_code}')
                return []
            
            return response.json()
        except Exception as e:
            logger.error(f'Error fetching guild roles: {e}', exc_info=True)
            return []
    
    @staticmethod
    def find_admin_role_id() -> Optional[str]:
        """Find the Admin role ID in the guild"""
        roles = DiscordService.get_guild_roles()
        
        for role in roles:
            if role.get('name', '').lower() == 'admin':
                return role['id']
         
        return None
    
    @staticmethod
    def check_user_has_role(discord_user_id: str, role_id: str) -> bool:
        """Check if a user has a specific role"""
        member = DiscordService.get_member(discord_user_id)
        
        if not member:
            return False
        
        member_roles = member.get('roles', [])
        return role_id in member_roles
    
    @staticmethod
    def get_all_members(limit: int = 1000) -> List[Dict]:
        """Get all members in the Discord guild"""
        try:
            headers = {
                'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/members?limit={limit}'
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f'Failed to fetch members: {response.status_code}')
                return []
            
            members = response.json()
            
            # Format and filter out bots
            formatted_members = []
            for member in members:
                user = member.get('user', {})
                if not user.get('bot', False):
                    formatted_members.append({
                        'discord_id': user.get('id'),
                        'username': user.get('username'),
                        'global_name': user.get('global_name'),
                        'nickname': member.get('nick'),
                        'avatar': user.get('avatar'),
                        'display_name': member.get('nick') or user.get('global_name') or user.get('username')
                    })
            
            return formatted_members
        except Exception as e:
            logger.error(f'Error fetching guild members: {e}', exc_info=True)
            return []
