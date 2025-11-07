"""CLI Authentication module"""
import os
import json
import requests
import getpass
from pathlib import Path
from typing import Dict, Optional


class CLIAuthenticator:
    """Handle CLI authentication"""
    
    def __init__(self, api_base: str, config_dir: Path):
        self.api_base = api_base
        self.config_dir = config_dir
        self.config_file = config_dir / 'config.json'
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def save_config(self):
        """Save configuration to file"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def authenticate(self) -> bool:
        """Authenticate user via Clerk token"""
        print("🔐 Authentication required...")
        print("Please visit the admin portal to get your authentication token:")
        print(f"   {self.api_base}/cli-auth")
        print()
        
        token = getpass.getpass("Enter your authentication token: ").strip()
        if not token:
            print("❌ No token provided")
            return False
        
        # Verify token with backend
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(
                f'{self.api_base}/api/auth/verify',
                json={'token': token},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.config['token'] = token
                self.save_config()
                print("✅ Authentication successful!")
                return True
            else:
                error = response.json().get('error', 'Authentication failed')
                print(f"❌ Authentication failed: {error}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_token(self) -> Optional[str]:
        """Get authentication token"""
        return self.config.get('token')
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return 'token' in self.config
    
    def logout(self):
        """Clear authentication token"""
        if 'token' in self.config:
            del self.config['token']
            self.save_config()
            print("👋 Logged out successfully")
        else:
            print("💡 You were not logged in")
    
    def verify_token(self) -> bool:
        """Verify current token is still valid"""
        if not self.is_authenticated():
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.get_token()}'}
            response = requests.post(
                f'{self.api_base}/api/auth/verify',
                json={'token': self.get_token()},
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
