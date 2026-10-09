"""Pod listing and selection."""

import requests
from typing import List, Dict, Optional
from rich.table import Table
from rich.prompt import IntPrompt

from .ui import console, error, warning, spinner, BOX, BORDER, PURPLE

RUNNING = 'RUNNING'

# Status colors in rich markup. Other statuses show dim.
STATUS_STYLE = {
    RUNNING: f"bold {PURPLE}",
    'EXITED': "yellow",
    'STOPPED': "yellow",
    'TERMINATED': "red",
    'GONE': "red",
}

# Error kinds that ApiError reports.
UNREACHABLE = 'unreachable'
TIMEOUT = 'timeout'
EXPIRED = 'expired'
FORBIDDEN = 'forbidden'
STOPPED = 'stopped'
FAILED = 'failed'


def status_markup(status: str) -> str:
    """The pod status as rich markup in its color."""
    status = status or 'UNKNOWN'
    style = STATUS_STYLE.get(status, 'dim')
    return f"[{style}]{status}[/{style}]"


def access_label(pod: Dict) -> str:
    """How the member has access to the pod: public to the org or shared with them."""
    if 'is_public' not in pod:
        return ''
    return 'public' if pod.get('is_public') else 'shared with you'


class ApiError(Exception):
    """A failed API call. kind is one of the error kinds above; hint says what to do."""

    def __init__(self, kind: str, message: str, hint: str = ''):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.hint = hint


def report(e: ApiError) -> None:
    """Print an ApiError and its hint."""
    error(e.message)
    if e.hint:
        console.print(f"[dim]{e.hint}[/dim]")


def _server_message(response, default: str) -> str:
    try:
        body = response.json()
        message = body.get('error') if isinstance(body, dict) else None
    except ValueError:
        message = None
    return message or default


def _response_error(response, default: str) -> ApiError:
    """An ApiError for a non-200 response, with a hint for the status code."""
    message = _server_message(response, default)
    code = response.status_code
    if code == 401:
        return ApiError(EXPIRED, message, "Run 'godfather auth' to log in again.")
    if code == 403:
        return ApiError(FORBIDDEN, message, "Ask an officer to share the pod with you, or rejoin the Discord server.")
    if code == 404:
        return ApiError(FAILED, message, "Check the pod ID with 'godfather list', and the org with 'godfather status'.")
    if code == 409:
        return ApiError(STOPPED, message, "The pod is not running. Ask an officer to start it, then try again.")
    if code >= 500:
        return ApiError(FAILED, message, "The server had a problem. Try again in a moment.")
    return ApiError(FAILED, message)


def _network_error(api_base: str, e: requests.RequestException) -> ApiError:
    if isinstance(e, requests.ConnectionError):
        return ApiError(
            UNREACHABLE,
            f"Couldn't reach {api_base}",
            "Check your internet connection, and the server URL with 'godfather status'.",
        )
    if isinstance(e, requests.Timeout):
        return ApiError(TIMEOUT, "The server took too long to answer", "Try again in a moment.")
    return ApiError(FAILED, f"Connection error: {e}")


class PodManager:
    """Fetch and present the pods a user can connect to."""

    def __init__(self, api_base: str, authenticator):
        self.api_base = api_base
        self.authenticator = authenticator

    def fetch_pods(self) -> List[Dict]:
        """The pods this member may connect to. Raises ApiError."""
        try:
            response = requests.get(
                self.authenticator.compute_url('/me/pods'),
                headers=self.authenticator.auth_headers(),
                timeout=10
            )
        except requests.RequestException as e:
            raise _network_error(self.api_base, e)

        if response.status_code != 200:
            raise _response_error(response, 'Failed to fetch pods')
        try:
            pods = response.json().get('pods', [])
        except (ValueError, AttributeError):
            raise ApiError(FAILED, "Received an unreadable response from the server")
        return [p for p in pods if isinstance(p, dict) and p.get('id')]

    def get_public_pods(self) -> List[Dict]:
        """The pods this member may connect to, or [] after printing the error."""
        try:
            return self.fetch_pods()
        except ApiError as e:
            report(e)
            return []

    def fetch_connection_info(self, pod_id: str, public_key: str) -> Dict:
        """SSH connection details and a certificate for our public key. Raises ApiError."""
        try:
            response = requests.post(
                self.authenticator.compute_url(f'/me/pods/{pod_id}/connect'),
                headers=self.authenticator.auth_headers(),
                json={'public_key': public_key},
                timeout=15
            )
        except requests.RequestException as e:
            raise _network_error(self.api_base, e)

        if response.status_code != 200:
            raise _response_error(response, 'Connection failed')
        try:
            ssh_info = response.json().get('ssh_info')
        except (ValueError, AttributeError):
            ssh_info = None
        if not isinstance(ssh_info, dict):
            raise ApiError(FAILED, "Received an unreadable response from the server")
        return ssh_info

    def get_connection_info(self, pod_id: str, public_key: str) -> Optional[Dict]:
        """SSH connection details, or None after printing the error."""
        try:
            return self.fetch_connection_info(pod_id, public_key)
        except ApiError as e:
            report(e)
            return None

    @staticmethod
    def pods_table(pods: List[Dict], title: str, numbered: bool = False) -> Table:
        """A table of pods with status, name, access and full pod ID."""
        table = Table(title=title, box=BOX, border_style=BORDER)
        if numbered:
            table.add_column("#", style="bold", width=3)
        table.add_column("Name", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Access")
        table.add_column("Pod ID", style="dim")
        for i, pod in enumerate(pods, 1):
            row = [
                str(pod.get('name') or pod['id']),
                status_markup(pod.get('status', '')),
                access_label(pod),
                str(pod['id']),
            ]
            table.add_row(*([str(i)] + row if numbered else row))
        return table

    @staticmethod
    def show_no_pods() -> None:
        warning("No pods are available to you right now.")
        console.print(
            "[dim]Only running pods that are public or shared with you show here. "
            "Ask an officer to start a pod or share one with you.[/dim]"
        )

    def show_pods(self, pods: List[Dict]) -> None:
        """Print the pods table and how to connect."""
        if not pods:
            self.show_no_pods()
            return
        console.print()
        console.print(self.pods_table(pods, f"Your pods ({len(pods)})"))
        console.print(f"[dim]Connect with: godfather connect {pods[0]['id']}[/dim]")

    def list_pods(self):
        """Fetch and print the pods available to the user."""
        with spinner("Fetching pods..."):
            pods = self.get_public_pods()
        self.show_pods(pods)

    def prompt_pod_number(self, pods: List[Dict]) -> Optional[str]:
        """Ask for a pod by number with a plain prompt, return its ID."""
        console.print()
        console.print(self.pods_table(pods, "Select a pod", numbered=True))
        console.print()
        try:
            choice = IntPrompt.ask("Pod number", choices=[str(i) for i in range(1, len(pods) + 1)])
            return pods[choice - 1]['id']
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Cancelled[/dim]")
            return None

    def select_pod(self) -> Optional[str]:
        """Fetch pods and ask for one by number, return its ID."""
        with spinner("Fetching pods..."):
            pods = self.get_public_pods()
        if not pods:
            self.show_no_pods()
            return None
        return self.prompt_pod_number(pods)
