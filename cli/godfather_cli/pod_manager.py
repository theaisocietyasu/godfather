"""Pod listing and selection."""

import requests
from typing import List, Dict, Optional
from rich.table import Table
from rich.prompt import IntPrompt

from .ui import console, error, warning, spinner, BOX, BORDER

STATUS_STYLE = {
    'RUNNING': "[bold #8b5cf6]RUNNING[/bold #8b5cf6]",
}


def _status_display(status: str) -> str:
    return STATUS_STYLE.get(status, f"[dim]{status}[/dim]")


class PodManager:
    """Fetch and present the pods a user can connect to."""

    def __init__(self, api_base: str):
        self.api_base = api_base

    def get_public_pods(self, discord_user_id: str) -> List[Dict]:
        """Get the pods available to this user for connection."""
        try:
            headers = {'X-Discord-User-ID': discord_user_id}
            response = requests.get(
                f'{self.api_base}/api/pods/public',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                try:
                    return response.json().get('pods', [])
                except ValueError:
                    error("Received an unreadable response from the server")
                    return []
            elif response.status_code == 401:
                error("Authentication failed. Run 'godfather auth' to log in again.")
                return []
            else:
                try:
                    message = response.json().get('error', 'Failed to fetch pods')
                except ValueError:
                    message = 'Failed to fetch pods'
                error(message)
                return []

        except requests.ConnectionError:
            error(f"Couldn't reach {self.api_base}")
            return []
        except requests.RequestException as e:
            error(f"Connection error: {e}")
            return []

    def get_connection_info(self, pod_id: str, discord_user_id: str) -> Optional[Dict]:
        """Get SSH connection details for a pod."""
        try:
            headers = {'X-Discord-User-ID': discord_user_id}
            response = requests.post(
                f'{self.api_base}/api/pods/{pod_id}/connect',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                try:
                    return response.json().get('ssh_info')
                except ValueError:
                    error("Received an unreadable response from the server")
                    return None
            else:
                try:
                    message = response.json().get('error', 'Connection failed')
                except ValueError:
                    message = 'Connection failed'
                error(message)
                return None

        except requests.ConnectionError:
            error(f"Couldn't reach {self.api_base}")
            return None
        except requests.RequestException as e:
            error(f"Connection error: {e}")
            return None

    def list_pods(self, discord_user_id: str):
        """Print a table of pods available to the user."""
        with spinner("Fetching pods..."):
            pods = self.get_public_pods(discord_user_id)

        if not pods:
            warning("No pods available right now.")
            console.print("[dim]Ask a Godfather admin to make a pod public or grant you access.[/dim]")
            return

        table = Table(title=f"Available Pods ({len(pods)})", box=BOX, border_style=BORDER)
        table.add_column("#", style="dim", width=3)
        table.add_column("Status", justify="center")
        table.add_column("Name", style="bold")
        table.add_column("ID", style="dim")
        table.add_column("Created")

        for i, pod in enumerate(pods, 1):
            table.add_row(
                str(i),
                _status_display(pod.get('status', 'unknown')),
                pod['name'],
                pod['id'][:12] + "...",
                pod.get('created_at', 'unknown')
            )

        console.print()
        console.print(table)

    def select_pod(self, discord_user_id: str) -> Optional[str]:
        """Prompt the user to pick a pod from the list, return its ID."""
        with spinner("Fetching pods..."):
            pods = self.get_public_pods(discord_user_id)

        if not pods:
            warning("No pods available right now.")
            return None

        table = Table(title="Select a Pod", box=BOX, border_style=BORDER)
        table.add_column("#", style="bold", width=3)
        table.add_column("Status", justify="center")
        table.add_column("Name")
        table.add_column("ID", style="dim")

        for i, pod in enumerate(pods, 1):
            table.add_row(
                str(i),
                _status_display(pod.get('status', 'unknown')),
                pod['name'],
                pod['id'][:12] + "..."
            )

        console.print()
        console.print(table)
        console.print()

        try:
            choice = IntPrompt.ask("Pod number", choices=[str(i) for i in range(1, len(pods) + 1)])
            return pods[choice - 1]['id']
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Cancelled[/dim]")
            return None
