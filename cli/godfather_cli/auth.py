"""CLI authentication: token storage, login flow, and token verification."""

import json
import os
import requests
from pathlib import Path
from typing import Dict, Optional
from rich.panel import Panel
from rich.prompt import Prompt

from .ui import console, success, error, warning, spinner, BOX, BORDER


class CLIAuthenticator:
    """Handle CLI authentication."""

    def __init__(self, api_base: str, config_dir: Path):
        self.api_base = api_base
        self.config_dir = config_dir
        self.config_file = config_dir / 'config.json'
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load stored config from disk, if any."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def save_config(self):
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        os.chmod(self.config_file, 0o600)

    def authenticate(self) -> bool:
        """Walk the user through logging in with a token from the admin portal."""
        panel = Panel(
            f"[bold]1.[/bold] Open [bold]{self.api_base}/cli-auth[/bold] and sign in with Discord\n"
            f"[bold]2.[/bold] Copy the token shown there\n"
            f"[bold]3.[/bold] Paste it below",
            title="Log in to Godfather",
            border_style=BORDER,
            box=BOX,
        )
        console.print(panel)
        console.print()

        token = Prompt.ask("Token", password=True).strip()
        if not token:
            error("No token entered")
            return False

        if not token.startswith('gf1.') or token.count('.') != 2:
            error("That doesn't look like a valid Godfather token")
            console.print("[dim]Tokens start with gf1. Get a fresh one from the admin portal.[/dim]")
            return False

        try:
            with spinner("Verifying token..."):
                response = requests.get(
                    f'{self.api_base}/api/me',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=10
                )
        except requests.ConnectionError:
            error(f"Couldn't reach {self.api_base}")
            console.print("[dim]Check your internet connection, or that the API URL is correct.[/dim]")
            return False
        except requests.Timeout:
            error("Request timed out")
            console.print("[dim]The server took too long to respond. Try again in a moment.[/dim]")
            return False
        except requests.RequestException as e:
            error(f"Connection error: {e}")
            return False

        if response.status_code != 200:
            try:
                message = response.json().get('error', 'Authentication failed')
            except ValueError:
                message = 'Authentication failed'
            error(message)
            if response.status_code == 401:
                console.print("[dim]That token is invalid or expired. Get a new one from the admin portal.[/dim]")
            return False

        data = response.json()
        is_admin = data.get('is_admin', False)

        self.config = {
            'token': token,
            'discord_user_id': data.get('discord_user_id'),
            'is_admin': is_admin,
        }
        self.save_config()

        role = "Admin" if is_admin else "Member"
        success(f"Logged in as {role}")
        return True

    def get_token(self) -> Optional[str]:
        return self.config.get('token')

    def auth_headers(self) -> Dict[str, str]:
        """Headers that authenticate an API request."""
        return {'Authorization': f"Bearer {self.config.get('token', '')}"}

    def is_admin(self) -> bool:
        return self.config.get('is_admin', False)

    def is_authenticated(self) -> bool:
        return str(self.config.get('token', '')).startswith('gf1.')

    def logout(self):
        if 'token' in self.config:
            del self.config['token']
            self.save_config()
            success("Logged out")
        else:
            warning("You weren't logged in")

    def verify_token(self) -> bool:
        """Check the stored token is still accepted by the backend."""
        if not self.is_authenticated():
            return False

        try:
            response = requests.get(
                f'{self.api_base}/api/me',
                headers=self.auth_headers(),
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
