"""Authentication and authorization service"""
import base64
import json
import requests
from datetime import datetime
from typing import Optional, Dict
from config.settings import settings
from config.database import users_collection
from utils.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    """Handle authentication and authorization"""
    
    @staticmethod
    def verify_clerk_token(token: str) -> Optional[Dict]:
        """Verify Clerk JWT token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
                
            payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
            decoded_payload = base64.urlsafe_b64decode(payload)
            user_data = json.loads(decoded_payload)
            
            return user_data
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    @staticmethod
    def get_discord_id_from_clerk(clerk_user_id: str) -> Optional[str]:
        """Fetch Discord ID from Clerk API"""
        try:
            headers = {
                'Authorization': f'Bearer {settings.CLERK_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://api.clerk.com/v1/users/{clerk_user_id}'
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f'Clerk API error: {response.status_code}')
                return None
            
            user_data = response.json()
            external_accounts = user_data.get('external_accounts', [])
            
            for account in external_accounts:
                if account.get('provider') == 'oauth_discord':
                    return account.get('provider_user_id')
            
            return None
        except Exception as e:
            logger.error(f'Error fetching Discord ID: {e}')
            return None
    
    @staticmethod
    def verify_discord_admin(discord_user_id: str) -> bool:
        """Verify if user has Admin role in Discord"""
        try:
            headers = {
                'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/members/{discord_user_id}'
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                return False
            
            member_data = response.json()
            
            roles_url = f'https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/roles'
            roles_response = requests.get(roles_url, headers=headers)
            
            if roles_response.status_code != 200:
                return False
            
            roles = roles_response.json()
            admin_role_id = None
            
            for role in roles:
                if role.get('name', '').lower() == 'admin':
                    admin_role_id = role['id']
                    break
            
            if not admin_role_id:
                return False
            
            return admin_role_id in member_data.get('roles', [])
            
        except Exception as e:
            logger.error(f'Discord verification error: {e}')
            return False
    
    @staticmethod
    def store_user(clerk_id: str, discord_id: str, username: str = None):
        """Store or update user in database"""
        user_doc = {
            'clerk_id': clerk_id,
            'discord_id': discord_id,
            'username': username,
            'last_login': datetime.utcnow()
        }
        
        users_collection.update_one(
            {'clerk_id': clerk_id},
            {'$set': user_doc},
            upsert=True
        )
