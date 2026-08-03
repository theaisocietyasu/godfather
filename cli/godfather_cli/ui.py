"""Shared terminal styling for the CLI.

Keeps output consistent across modules: one Console instance, one color
convention (purple for headers/highlights, plain text for body copy, red
for errors, yellow for warnings), and one spinner helper for anything that
waits on a network call.
"""

from contextlib import contextmanager

from rich.console import Console
from rich import box

PURPLE = "#8b5cf6"

console = Console()

# Shared box/border style so every table and panel looks the same.
BOX = box.ROUNDED
BORDER = PURPLE


def heading(text: str) -> str:
    """Format text as a section heading."""
    return f"[bold {PURPLE}]{text}[/bold {PURPLE}]"


def success(message: str) -> None:
    console.print(f"[bold {PURPLE}]✓[/bold {PURPLE}] {message}")


def error(message: str) -> None:
    console.print(f"[bold red]✗[/bold red] {message}")


def warning(message: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {message}")


def info(message: str) -> None:
    console.print(message)


@contextmanager
def spinner(message: str):
    """Show a spinner for the duration of a network call or other wait."""
    with console.status(f"[bold {PURPLE}]{message}[/bold {PURPLE}]", spinner="dots"):
        yield
