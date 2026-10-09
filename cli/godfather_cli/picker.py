"""Arrow-key menus and the pod picker.

The functions that build choices are pure and need no terminal. The ask_ functions
draw questionary prompts and raise KeyboardInterrupt when the user presses Ctrl-C.
"""

import sys
from typing import Dict, List, NamedTuple, Optional, Tuple

import questionary
from questionary import Choice, Style

from .pod_manager import RUNNING, access_label
from .ui import PURPLE

STYLE = Style([
    ('qmark', f'fg:{PURPLE} bold'),
    ('question', 'bold'),
    ('pointer', f'fg:{PURPLE} bold'),
    ('highlighted', f'fg:{PURPLE} bold'),
    ('selected', f'fg:{PURPLE}'),
    ('answer', f'fg:{PURPLE} bold'),
    ('instruction', 'fg:#858585 italic'),
    ('disabled', 'fg:#858585 italic'),
    ('text', ''),
])

# Prompt-toolkit styles for pod statuses in the picker.
STATUS_CLASS = {
    RUNNING: f'fg:{PURPLE} bold',
    'EXITED': 'fg:ansiyellow',
    'STOPPED': 'fg:ansiyellow',
    'TERMINATED': 'fg:ansired',
    'GONE': 'fg:ansired',
}

# Main menu actions.
CONNECT = 'connect'
LIST = 'list'
STATUS = 'status'
LOGIN = 'login'
LOGOUT = 'logout'
EXIT = 'exit'


class PodOption(NamedTuple):
    """One row of the pod picker."""
    pod_id: str
    parts: List[Tuple[str, str]]
    disabled: Optional[str]


def is_interactive() -> bool:
    """True when stdin and stdout are terminals, so arrow-key prompts can run."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def disabled_reason(pod: Dict) -> Optional[str]:
    """Why the member cannot connect to the pod now, or None if they can."""
    status = str(pod.get('status') or '')
    if not status or status == RUNNING:
        return None
    if status in ('EXITED', 'STOPPED'):
        return 'stopped, ask an officer to start it'
    if status in ('TERMINATED', 'GONE'):
        return 'deleted'
    return f'{status.lower()}, not running yet'


def connectable(pods: List[Dict]) -> List[Dict]:
    """The pods the member can connect to now."""
    return [p for p in pods if disabled_reason(p) is None]


def single_connectable(pods: List[Dict]) -> Optional[Dict]:
    """The pod when exactly one is connectable, so the picker can ask for a yes instead."""
    ready = connectable(pods)
    return ready[0] if len(ready) == 1 else None


def pod_options(pods: List[Dict]) -> List[PodOption]:
    """Picker rows, connectable pods first. Each row is name, status, access and short pod ID."""
    ordered = sorted(pods, key=lambda p: disabled_reason(p) is not None)
    width = max((len(str(p.get('name') or p['id'])) for p in ordered), default=0)
    options = []
    for pod in ordered:
        status = str(pod.get('status') or 'UNKNOWN')
        name = str(pod.get('name') or pod['id'])
        parts = [
            ('bold', name.ljust(width)),
            ('', '  '),
            (STATUS_CLASS.get(status, 'fg:#858585'), status.ljust(10)),
        ]
        access = access_label(pod)
        if access:
            parts.append(('', f'  {access.ljust(15)}'))
        parts.append(('fg:#858585', f'  {str(pod["id"])[:12]}'))
        options.append(PodOption(str(pod['id']), parts, disabled_reason(pod)))
    return options


def menu_options(logged_in: bool) -> List[Tuple[str, str, str]]:
    """Main menu rows as (action, title, description)."""
    account = (
        (LOGOUT, 'Log out', 'Remove the saved token from this computer')
        if logged_in else
        (LOGIN, 'Log in', 'Sign in with Discord and paste your token')
    )
    return [
        (CONNECT, 'Connect to a pod', 'Pick a running pod and open an SSH session'),
        (LIST, 'List pods', 'Show every pod you can use, with its status and ID'),
        (STATUS, 'Status', 'Server, org, login, token expiry and CLI version'),
        account,
        (EXIT, 'Exit', 'Quit Godfather'),
    ]


def ask_menu(logged_in: bool) -> str:
    """Ask for a main menu action with the arrow keys."""
    choices = [Choice(title, value=action, description=desc) for action, title, desc in menu_options(logged_in)]
    answer = questionary.select(
        'What would you like to do?',
        choices=choices,
        style=STYLE,
        instruction='(arrow keys, Enter to choose, Ctrl-C to quit)',
    ).unsafe_ask()
    return answer or EXIT


def ask_pod(pods: List[Dict]) -> Optional[str]:
    """Pick a connectable pod with the arrow keys. A single connectable pod asks for a yes instead."""
    only = single_connectable(pods)
    if only is not None:
        name = only.get('name') or only['id']
        if questionary.confirm(f'Connect to {name}?', default=True, style=STYLE).unsafe_ask():
            return str(only['id'])
        return None

    choices = [Choice(o.parts, value=o.pod_id, disabled=o.disabled) for o in pod_options(pods)]
    choices.append(Choice([('fg:#858585', 'Back')], value=''))
    answer = questionary.select(
        'Which pod?',
        choices=choices,
        style=STYLE,
        instruction='(arrow keys, Enter to connect)',
    ).unsafe_ask()
    return answer or None


def ask_yes(question: str, default: bool = True) -> bool:
    """A yes or no question."""
    return bool(questionary.confirm(question, default=default, style=STYLE).unsafe_ask())
