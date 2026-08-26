"""Check PyPI for newer releases and handle self-update via pip."""

import subprocess
import sys

import requests
from packaging import version as version_lib
from rich.panel import Panel

from . import __version__
from .ui import console, success, error, spinner, BORDER


def check_for_updates(force_check=False):
    """Check PyPI for a newer release.

    Returns (has_update, latest_version). Fails silently (returns
    False, current version) on any network error or unexpected
    response from PyPI - update checks should never block normal
    CLI use.
    """
    try:
        response = requests.get(
            "https://pypi.org/pypi/godfather-cli/json",
            timeout=3
        )
        if response.status_code == 200:
            data = response.json()
            latest_version = data['info']['version']
            if version_lib.parse(latest_version) > version_lib.parse(__version__):
                return True, latest_version
            return False, __version__
    except (requests.RequestException, ValueError, KeyError):
        pass
    return False, __version__


def show_update_warning(latest_version):
    """Print a non-blocking notice that a newer version is available."""
    console.print()
    console.print(Panel.fit(
        f"Update available: [dim]{__version__}[/dim] -> [bold]{latest_version}[/bold]\n"
        f"Run [bold]godfather update[/bold] to install it.",
        border_style="yellow",
        title="[bold yellow]Update available[/bold yellow]",
    ))
    console.print()


def perform_update():
    """Update the installed package to the latest version via pip."""
    with spinner("Checking for updates..."):
        has_update, latest_version = check_for_updates(force_check=True)

    if not has_update:
        success(f"Already on the latest version ({__version__})")
        return

    with spinner(f"Updating from {__version__} to {latest_version}..."):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "godfather-cli"],
                capture_output=True,
                text=True
            )
        except OSError as e:
            error(f"Update failed: {e}")
            console.print("[dim]Try manually: pip install --upgrade godfather-cli[/dim]")
            return

    if result.returncode == 0:
        console.print()
        console.print(Panel.fit(
            f"Updated to version [bold]{latest_version}[/bold].\n"
            f"Restart your terminal or run the command again.",
            border_style=BORDER,
            title="[bold]Update complete[/bold]",
        ))
        console.print()
    else:
        error(f"Update failed: {result.stderr.strip()}")
        console.print("[dim]Try manually: pip install --upgrade godfather-cli[/dim]")
