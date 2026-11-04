"""CLI authentication: token storage, login flow, and token verification."""

import base64
import datetime
import hashlib
import json
import os
import secrets
import webbrowser
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlencode

import requests
from rich.panel import Panel
from rich.prompt import Prompt

from .login_server import LoopbackReceiver
from .ui import BORDER, BOX, console, error, spinner, success, warning

TOKEN_PREFIX = 'plat_'
# The platform issues CLI tokens for 90 days.
TOKEN_DAYS = 90

# How long the CLI waits for the browser sign-in.
LOGIN_WAIT_SECONDS = 300

# Token states that check_token returns.
TOKEN_OK = 'ok'
TOKEN_MISSING = 'missing'
TOKEN_EXPIRED = 'expired'
TOKEN_UNREACHABLE = 'unreachable'
TOKEN_REFUSED = 'refused'


def make_verifier() -> str:
    """A PKCE code verifier (RFC 7636): 64 URL-safe characters."""
    return secrets.token_urlsafe(48)


def challenge_for(verifier: str) -> str:
    """The S256 code challenge of a verifier: base64url SHA-256 without padding."""
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


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

    def authenticate(self, paste: bool = False) -> bool:
        """Sign in with Discord. The browser hands the token back; the paste flow is the fallback."""
        if not paste:
            if self.supports_loopback():
                token = self._browser_login()
                if token:
                    return self._verify_and_save(token)
            else:
                console.print("[dim]This server does not support browser sign-in yet. Paste the token instead.[/dim]")
        return self._paste_login()

    def supports_loopback(self) -> bool:
        """True when the server has the cli/token route. It answers 400 to an empty body."""
        try:
            response = requests.post(self.compute_url('/cli/token'), json={}, timeout=10)
        except requests.RequestException:
            return False
        return response.status_code == 400

    def _browser_login(self) -> Optional[str]:
        """The token from the localhost callback with PKCE, or None after printing why not."""
        state = secrets.token_urlsafe(16)
        verifier = make_verifier()
        try:
            receiver = LoopbackReceiver(state)
        except OSError:
            console.print("[dim]Could not listen on 127.0.0.1. Paste the token instead.[/dim]")
            return None
        try:
            query = urlencode(
                {
                    'port': receiver.port,
                    'state': state,
                    'code_challenge': challenge_for(verifier),
                    'code_challenge_method': 'S256',
                }
            )
            login_url = f"{self.compute_url('/cli/login')}?{query}"
            try:
                opened = webbrowser.open(login_url)
            except webbrowser.Error:
                opened = False
            if not opened:
                console.print("[dim]No browser opened on this computer. Paste the token instead.[/dim]")
                return None
            console.print(f"Sign in with Discord in your browser. If it did not open, go to:\n{login_url}")
            try:
                with spinner("Waiting for the browser sign-in..."):
                    code = receiver.wait(LOGIN_WAIT_SECONDS)
            except KeyboardInterrupt:
                console.print("[dim]Cancelled[/dim]")
                return None
        finally:
            receiver.close()
        if not code:
            console.print("[dim]The browser sign-in did not finish in time. Paste the token instead.[/dim]")
            return None
        return self._redeem(code, verifier)

    def _redeem(self, code: str, verifier: str) -> Optional[str]:
        """Exchange the one-time code and the PKCE verifier for a token."""
        try:
            with spinner("Getting your token..."):
                response = requests.post(
                    self.compute_url('/cli/token'),
                    json={'code': code, 'code_verifier': verifier},
                    timeout=10,
                )
            token = str(response.json().get('token') or '') if response.status_code == 200 else ''
        except (requests.RequestException, ValueError, AttributeError):
            token = ''
        if not token.startswith(TOKEN_PREFIX):
            console.print("[dim]The server did not return a token. Paste the token instead.[/dim]")
            return None
        return token

    def _paste_login(self) -> bool:
        """Open the sign-in page and take the token the member pastes."""
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

        try:
            token = Prompt.ask("Token", password=True).strip()
        except EOFError:
            token = ''
        if not token:
            error("No token entered")
            return False

        if not token.startswith(TOKEN_PREFIX):
            error("That doesn't look like a valid Godfather token")
            console.print(f"[dim]Tokens start with {TOKEN_PREFIX}. Get a fresh one from {login_url}[/dim]")
            return False
        return self._verify_and_save(token)

    def _verify_and_save(self, token: str) -> bool:
        """Check the token with GET /me/pods, then save it with the server and org."""
        try:
            with spinner("Verifying token..."):
                response = requests.get(
                    self.compute_url('/me/pods'), headers={'Authorization': f'Bearer {token}'}, timeout=10
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

    def check_token(self) -> str:
        """Ask the server whether the stored token works. Returns one of the TOKEN_ states."""
        if not self.is_authenticated():
            return TOKEN_MISSING

        try:
            response = requests.get(self.compute_url('/me/pods'), headers=self.auth_headers(), timeout=5)
        except requests.RequestException:
            return TOKEN_UNREACHABLE
        if response.status_code == 200:
            return TOKEN_OK
        if response.status_code == 401:
            return TOKEN_EXPIRED
        return TOKEN_REFUSED

    def verify_token(self) -> bool:
        """Check the stored token is still accepted by the backend."""
        return self.check_token() == TOKEN_OK

    def token_saved_at(self) -> Optional[datetime.datetime]:
        """When the stored token was saved, from the config file time. Only login writes a token."""
        if not self.is_authenticated():
            return None
        try:
            return datetime.datetime.fromtimestamp(self.config_file.stat().st_mtime)
        except OSError:
            return None

    def token_expires_at(self) -> Optional[datetime.datetime]:
        """About when the stored token expires: TOKEN_DAYS after it was saved."""
        saved = self.token_saved_at()
        return saved + datetime.timedelta(days=TOKEN_DAYS) if saved else None
