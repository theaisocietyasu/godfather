"""
Update checker for Godfather CLI
""" import requests
import sys
import subprocess
from packaging import version as version_lib
from rich.console import Console
from rich.panel import Panel

from . import __version__

console = Console()

def check_for_updates(force_check=False):
    """ Check if a new version is available on PyPI
    Returns: (has_update, latest_version)
    """ try:
        response = requests.get(
            "https://pypi.org/pypi/godfather-cli/json",
            timeout=3
        )
        if response.status_code == 200:
            data = response.json()
            latest_version = data['info']['version'] current_version = __version__
            
            if version_lib.parse(latest_version) > version_lib.parse(current_version):
                return True, latest_version
            return False, current_version
    except Exception:
        # Silently fail if we can't check for updates
        pass
    return False, __version__

def show_update_warning(latest_version):
    """Display update warning to user""" console.print()
    console.print(Panel.fit(
        f"[bold yellow] Update Available![/bold yellow]\n\n" f"Current version: [red]{__version__}[/red]\n" f"Latest version: [green]{latest_version}[/green]\n\n" f"Update now with: [bold cyan]godfather update[/bold cyan]",
        border_style="yellow" ))
    console.print()

def force_update_check():
    """ Check for updates and force user to update if outdated
    """ has_update, latest_version = check_for_updates(force_check=True)
    
    if has_update:
        console.print()
        console.print(Panel.fit(
            f"[bold red] Update Required![/bold red]\n\n" f"Current version: [red]{__version__}[/red]\n" f"Latest version: [green]{latest_version}[/green]\n\n" f"Please update to continue using Godfather CLI.\n" f"Run: [bold cyan]godfather update[/bold cyan]",
            border_style="red" ))
        console.print()
        sys.exit(1)

def perform_update():
    """ Perform the actual update using pip
    """ console.print("[cyan]Checking for updates...[/cyan]")
    
    has_update, latest_version = check_for_updates(force_check=True)
    
    if not has_update:
        console.print(f"[green][/green] You're already on the latest version ({__version__})")
        return
    
    console.print(f"[yellow]Updating from {__version__} to {latest_version}...[/yellow]")
    
    try:
        # Try to update using pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "godfather-cli"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print()
            console.print(Panel.fit(
                f"[bold green] Successfully updated![/bold green]\n\n" f"Godfather CLI has been updated to version [green]{latest_version}[/green]\n\n" f"Please restart your terminal or run the command again.",
                border_style="green" ))
            console.print()
        else:
            console.print(f"[red] Update failed:[/red] {result.stderr}")
            console.print(f"\n[yellow]Try manually:[/yellow] pip install --upgrade godfather-cli")
    except Exception as e:
        console.print(f"[red] Update failed:[/red] {str(e)}")
        console.print(f"\n[yellow]Try manually:[/yellow] pip install --upgrade godfather-cli")
