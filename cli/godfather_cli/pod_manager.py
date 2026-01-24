"""CLI Pod Operations module"""

import requests
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich import box
from rich.prompt import IntPrompt

console = Console()


class PodManager:
    """Handle pod operations"""

def __init__(self, api_base: str):
        self.api_base = api_base
    
    def get_public_pods(self, discord_user_id: str) -> List[Dict]:
        """Get list of public pods available for connection"""

try:
            headers = {'X-Discord-User-ID': discord_user_id}
            response = requests.get(
                f'{self.api_base}/api/pods/public',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('pods', [])
            elif response.status_code == 401:
                console.print("[red][/red] Authentication failed. Please re-authenticate.")
                return []
            else:
                error = response.json().get('error', 'Failed to fetch pods')
                console.print(f"[red][/red] Error: {error}")
                return []
                
        except requests.RequestException as e:
            console.print(f"[red][/red] Connection error: {e}")
            return []
    
    def get_connection_info(self, pod_id: str, discord_user_id: str) -> Optional[Dict]:
        """Get SSH connection information for a pod"""

try:
            headers = {'X-Discord-User-ID': discord_user_id}
            response = requests.post(
                f'{self.api_base}/api/pods/{pod_id}/connect',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('ssh_info')
            else:
                error = response.json().get('error', 'Connection failed')
                console.print(f"[red][/red] Connection failed: {error}")
                return None
                
        except requests.RequestException as e:
            console.print(f"[red][/red] Connection error: {e}")
            return None
    
    def list_pods(self, discord_user_id: str):
        """List available public pods"""

console.print("[cyan]📡 Fetching available pods...[/cyan]")
        pods = self.get_public_pods(discord_user_id)
        
        if not pods:
            console.print("[yellow]😔 No public pods available at the moment.[/yellow]")
            console.print(" [dim]Ask a godfather to create and make pods public.[/dim]")
            return
        
        table = Table(title=f"[bold cyan] Available Pods ({len(pods)})[/bold cyan]", box=box.ROUNDED, border_style="cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Status", justify="center", width=8)
        table.add_column("Name", style="cyan bold")
        table.add_column("ID", style="dim")
        table.add_column("Created", style="white")
        
        for i, pod in enumerate(pods, 1):
            status = pod.get('status', 'Unknown')
            if status == 'RUNNING':
                status_display = "[green]� RUN[/green]" else:
                status_display = "[red]🔴 OFF[/red]" table.add_row(
                str(i),
                status_display,
                pod['name'],
                pod['id'][:12] + "...",
                pod.get('created_at', 'Unknown')
            )
        
        console.print()
        console.print(table)
    
    def select_pod(self, discord_user_id: str) -> Optional[str]:
        """Interactive pod selection"""

pods = self.get_public_pods(discord_user_id)
        
        if not pods:
            console.print("[yellow]😔 No public pods available.[/yellow]")
            return None
        
        table = Table(title="[bold cyan] Select a Pod[/bold cyan]", box=box.SIMPLE, border_style="cyan")
        table.add_column("#", style="cyan bold", width=3)
        table.add_column("Status", justify="center", width=8)
        table.add_column("Name", style="white")
        table.add_column("ID", style="dim")
        
        for i, pod in enumerate(pods, 1):
            status = pod.get('status', 'Unknown')
            status_display = "[green]🟢 RUN[/green]" if status == 'RUNNING' else "[red]🔴 OFF[/red]" table.add_row(
                str(i),
                status_display,
                pod['name'],
                pod['id'][:12] + "..." )
        
        console.print()
        console.print(table)
        console.print()
        
        try:
            choice = IntPrompt.ask("[cyan]Select a pod number[/cyan]", choices=[str(i) for i in range(1, len(pods) + 1)])
            return pods[choice - 1]['id'] except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Selection cancelled[/yellow]")
            return None
