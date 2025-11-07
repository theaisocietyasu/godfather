"""Application configuration settings"""
import os
from typing import Optional

class Settings:
    """Application settings from environment variables"""
    
    # MongoDB
    MONGODB_URI: str = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/godfather')
    
    # RunPod
    RUNPOD_API_KEY: Optional[str] = os.getenv('RUNPOD_API_KEY')
    
    # Clerk Authentication
    CLERK_SECRET_KEY: Optional[str] = os.getenv('CLERK_SECRET_KEY')
    
    # Discord Bot
    DISCORD_BOT_TOKEN: Optional[str] = os.getenv('DISCORD_BOT_TOKEN')
    DISCORD_GUILD_ID: Optional[str] = os.getenv('DISCORD_GUILD_ID')
    ADMIN_ROLE_ID: Optional[str] = os.getenv('ADMIN_ROLE_ID')
    
    # JWT
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'your-secret-key')
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        required = [
            ('RUNPOD_API_KEY', cls.RUNPOD_API_KEY),
            ('CLERK_SECRET_KEY', cls.CLERK_SECRET_KEY),
            ('DISCORD_BOT_TOKEN', cls.DISCORD_BOT_TOKEN),
            ('DISCORD_GUILD_ID', cls.DISCORD_GUILD_ID),
        ]
        
        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

settings = Settings()
