"""CLI Authentication module"""

import os
import json
import requests
import getpass
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.prompt import Prompt

console = Console()


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
        """Authenticate user via CLI token"""

panel = Panel(
            f"[cyan]Visit the admin portal to get your authentication token:[/cyan]\n" f"[bold white]{self.api_base}/cli-auth[/bold white]",
            title="[bold magenta]🔐 Authentication Required[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED
        )
        console.print(panel)
        console.print()
        
        token = Prompt.ask("[cyan]Enter your authentication token[/cyan]", password=True).strip()
        if not token:
            console.print("[red][/red] No token provided")
            return False
        
        # Extract Discord ID from token (format: discord_<ID>_<timestamp>)
        try:
            if token.startswith('discord_'):
                parts = token.split('_')
                if len(parts) >= 2:
                    discord_user_id = parts[1] else:
                    console.print("[red][/red] Invalid token format")
                    return False
            else:
                console.print("[red][/red] Invalid token format")
                return False
        except:
            console.print("[red][/red] Invalid token format")
            return False
        
        # Verify token with backend
        try:
            response = requests.post(
                f'{self.api_base}/api/auth/verify',
                json={'discord_user_id': discord_user_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                is_admin = data.get('is_admin', False)
                
                self.config['token'] = token
                self.config['discord_user_id'] = discord_user_id
                self.config['is_admin'] = is_admin
                self.save_config()
                
                if is_admin:
                    console.print("[green][/green] Authentication successful! [bold cyan](Admin)[/bold cyan]")
                else:
                    console.print("[green][/green] Authentication successful! [bold yellow](Member)[/bold yellow]")
                
                return True
            else:
                error = response.json().get('error', 'Authentication failed')
                console.print(f"[red][/red] Authentication failed: {error}")
                return False
                
        except requests.RequestException as e:
            console.print(f"[red][/red] Connection error: {e}")
            return False
    
    def get_token(self) -> Optional[str]:
        """Get authentication token"""

return self.config.get('token')
    
    def get_discord_user_id(self) -> Optional[str]:
        """Get Discord user ID"""

return self.config.get('discord_user_id')
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges"""

return self.config.get('is_admin', False)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""

return 'token' in self.config
    
    def logout(self):
        """Clear authentication token"""

if 'token' in self.config:
            del self.config['token'] self.save_config()
            console.print("[green][/green] Logged out successfully")
        else:
            console.print("[yellow]ℹ[/yellow] You were not logged in")
    
    def verify_token(self) -> bool:
        """Verify current token is still valid"""

if not self.is_authenticated():
            return False
        
        discord_user_id = self.config.get('discord_user_id')
        if not discord_user_id:
            return False
        
        try:
            response = requests.post(
                f'{self.api_base}/api/auth/verify',
                json={'discord_user_id': discord_user_id},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
