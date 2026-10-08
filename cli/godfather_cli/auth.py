"""CLI authentication: token storage, login flow, and token verification."""

import json
import os
import requests
import webbrowser
from pathlib import Path
from typing import Dict, Optional
from rich.panel import Panel
from rich.prompt import Prompt

from .ui import console, success, error, warning, spinner, BOX, BORDER

TOKEN_PREFIX = 'plat_'


class CLIAuthenticator:
    """Handle CLI authentication."""

    def __init__(self, api_base: str, org: str, config_dir: Path):
        self.api_base = api_base
        self.org = org
        self.config_dir = config_dir
        self.config_file = config_dir / 'config.json'
        self.config = self.load_config()

    @staticmethod
    def read_config(config_dir: Path) -> Dict:
        """The stored config in config_dir, or an empty dict."""
        config_file = config_dir / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def load_config(self) -> Dict:
        """Load stored config from disk, if any."""
        return self.read_config(self.config_dir)

    def save_config(self):
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        os.chmod(self.config_file, 0o600)

    def compute_url(self, path: str = '') -> str:
        """URL of a platform compute route for the configured org."""
        return f"{self.api_base}/api/compute/{self.org}{path}"

    def authenticate(self) -> bool:
        """Walk the user through signing in with Discord and pasting the token it shows."""
        login_url = self.compute_url('/cli/login')
        panel = Panel(
            f"[bold]1.[/bold] Open [bold]{login_url}[/bold] and sign in with Discord\n"
            f"[bold]2.[/bold] Copy the token shown there\n"
            f"[bold]3.[/bold] Paste it below",
            title="Log in to Godfather",
            border_style=BORDER,
            box=BOX,
        )
        console.print(panel)
        console.print()
        try:
            webbrowser.open(login_url)
        except webbrowser.Error:
            pass

        token = Prompt.ask("Token", password=True).strip()
        if not token:
            error("No token entered")
            return False

        if not token.startswith(TOKEN_PREFIX):
            error("That doesn't look like a valid Godfather token")
            console.print(f"[dim]Tokens start with {TOKEN_PREFIX}. Get a fresh one from {login_url}[/dim]")
            return False

        try:
            with spinner("Verifying token..."):
                response = requests.get(
                    self.compute_url('/me/pods'),
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
            return False

        self.config = {'token': token, 'api_url': self.api_base, 'org': self.org}
        self.save_config()
        success(f"Logged in to {self.org}")
        return True

    def get_token(self) -> Optional[str]:
        return self.config.get('token')

    def auth_headers(self) -> Dict[str, str]:
        """Headers that authenticate an API request."""
        return {'Authorization': f"Bearer {self.config.get('token', '')}"}

    def is_authenticated(self) -> bool:
        """A platform token is stored for this server and org."""
        return (
            str(self.config.get('token', '')).startswith(TOKEN_PREFIX)
            and self.config.get('api_url') == self.api_base
            and self.config.get('org') == self.org
        )

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
                self.compute_url('/me/pods'),
                headers=self.auth_headers(),
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
