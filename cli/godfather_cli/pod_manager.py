"""Pod listing and selection, and the upcoming sessions of the member's pods."""

import datetime
from typing import Dict, List, Optional

import requests
from rich.prompt import IntPrompt
from rich.table import Table

from .ui import BORDER, BOX, PURPLE, console, error, spinner, warning

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


def parse_time(value: str) -> Optional[datetime.datetime]:
    """An ISO 8601 time from the server as an aware datetime, or None."""
    try:
        parsed = datetime.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=datetime.timezone.utc)


def starts_in(session: Dict, now: datetime.datetime) -> str:
    """When the session starts, relative to now: 'starts in 2 h 5 min', or 'now' while it runs."""
    start = parse_time(session.get('start_at', ''))
    stop = parse_time(session.get('stop_at', ''))
    if start is None:
        return ''
    if start <= now and (stop is None or now < stop):
        return 'now'
    minutes = max(0, int((start - now).total_seconds() // 60))
    days, rest = divmod(minutes, 24 * 60)
    hours, minutes = divmod(rest, 60)
    parts = [f'{days} d'] if days else []
    if hours:
        parts.append(f'{hours} h')
    if minutes or not parts:
        parts.append(f'{minutes} min')
    return 'starts in ' + ' '.join(parts)


def local_time(value: str, same_day_as: str = '') -> str:
    """A server time in the member's local zone, 'Tue Oct 21 17:00', or '19:00' on the day of same_day_as."""
    parsed = parse_time(value)
    if parsed is None:
        return ''
    local = parsed.astimezone()
    other = parse_time(same_day_as)
    if other is not None and other.astimezone().date() == local.date():
        return local.strftime('%H:%M')
    return local.strftime('%a %b %d %H:%M')


def now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


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
                self.authenticator.compute_url('/me/pods'), headers=self.authenticator.auth_headers(), timeout=10
            )
        except requests.RequestException as e:
            raise _network_error(self.api_base, e) from e

        if response.status_code != 200:
            raise _response_error(response, 'Failed to fetch pods')
        try:
            pods = response.json().get('pods', [])
        except (ValueError, AttributeError):
            raise ApiError(FAILED, "Received an unreadable response from the server") from None
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
                timeout=15,
            )
        except requests.RequestException as e:
            raise _network_error(self.api_base, e) from e

        if response.status_code != 200:
            raise _response_error(response, 'Connection failed')
        try:
            ssh_info = response.json().get('ssh_info')
        except (ValueError, AttributeError):
            ssh_info = None
        if not isinstance(ssh_info, dict):
            raise ApiError(FAILED, "Received an unreadable response from the server") from None
        return ssh_info

    def fetch_sessions(self) -> Optional[List[Dict]]:
        """Upcoming sessions on the member's pods, soonest first. None when the server has no such route."""
        try:
            response = requests.get(
                self.authenticator.compute_url('/me/sessions'), headers=self.authenticator.auth_headers(), timeout=10
            )
        except requests.RequestException as e:
            raise _network_error(self.api_base, e) from e

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise _response_error(response, 'Failed to fetch sessions')
        try:
            sessions = response.json().get('sessions', [])
        except (ValueError, AttributeError):
            raise ApiError(FAILED, "Received an unreadable response from the server") from None
        return [s for s in sessions if isinstance(s, dict) and s.get('start_at')]

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
    def sessions_table(sessions: List[Dict], now: Optional[datetime.datetime] = None) -> Table:
        """A table of sessions with pod, title, local start and end, and time until the start."""
        now = now or now_utc()
        table = Table(title=f"Upcoming sessions ({len(sessions)})", box=BOX, border_style=BORDER)
        table.add_column("Pod", style="bold")
        table.add_column("Session")
        table.add_column("Starts", no_wrap=True)
        table.add_column("Ends", no_wrap=True)
        table.add_column("In", style="dim", no_wrap=True)
        for session in sessions:
            table.add_row(
                str(session.get('pod_name') or session.get('pod_id') or ''),
                str(session.get('title') or ''),
                local_time(session.get('start_at', '')),
                local_time(session.get('stop_at', ''), same_day_as=session.get('start_at', '')),
                starts_in(session, now),
            )
        return table

    @staticmethod
    def next_session_line(sessions: List[Dict], now: Optional[datetime.datetime] = None) -> str:
        """One line about the soonest session, or '' when there is none."""
        if not sessions:
            return ''
        first = sessions[0]
        name = first.get('pod_name') or first.get('pod_id') or 'a pod'
        title = first.get('title') or 'Session'
        when = local_time(first.get('start_at', ''))
        return f"Next session: {title} on {name}, {when} ({starts_in(first, now or now_utc())})"

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
