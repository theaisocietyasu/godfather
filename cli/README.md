# Godfather CLI

Command-line client for Godfather, free compute for ASU students run by the
AI Society at ASU. Log in with your Discord account and SSH into a GPU or CPU
machine the club pays for, with your own private workspace.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Installation

Install from PyPI:

```bash
pip install godfather-cli
```

Or install straight from GitHub:

```bash
pip install git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
```

For local development:

```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather/cli
pip install -e .
```

## Getting started

1. Run `godfather` with no arguments. On first run you won't be logged in
   yet, so it'll walk you into the login flow.
2. It opens the sign-in page in your browser and prints the link. Sign in
   with Discord. The browser sends the login back to the CLI, which checks it
   and stores the token in `~/.godfather/config.json`.
3. If the browser cannot reach the CLI (no browser on this computer, an
   older server, or no sign-in within 5 minutes), the CLI asks you to paste
   the token that the sign-in page shows. `godfather auth --paste` goes
   straight to that, for a browser on another computer.
4. From the menu (or `godfather connect`), pick a pod. The CLI creates an SSH
   key on your machine the first time, asks the server for a 12-hour
   certificate for that pod, and opens the connection.

A token lasts 90 days. When it expires, or if you leave the Discord server,
the CLI asks you to log in again.

You need OpenSSH installed (`ssh` and `ssh-keygen`). macOS, Linux and
Windows 10+ ship it.

## Usage

### Interactive menu

Running `godfather` with no arguments opens a menu. Use the arrow keys to
choose Connect to a pod, List pods, Status, Log out or Exit, and press Enter.
Ctrl-C quits.

Connect to a pod shows a list of your pods with their status, access and
pod ID. A pod that is not running shows with the reason and cannot be
chosen. If only one pod is running, the CLI asks for a yes instead.

When input is not a terminal (for example in a script), the menu and the pod
list use numbered prompts.

### Commands

```bash
godfather list                    # List pods you can connect to
godfather connect                 # Connect to a pod, picking from a list
godfather connect <pod-id>        # Connect to a specific pod
godfather status                  # Show server, org, login, token expiry and version
godfather auth                    # Log in with Discord in your browser
godfather auth --paste            # Log in by pasting the token
godfather logout                  # Clear the stored session
godfather update                  # Update the CLI to the latest version

# Use another platform server or organization
godfather --api-url https://platform.example.com --org soda list
```

## Files it keeps

Everything lives in `~/.godfather/`:

- `config.json`: your token (mode 600). Treat it like a password.
- `ssh/id_ed25519`, `ssh/id_ed25519.pub`: your SSH key, created on first connect. The private key never leaves your machine.
- `ssh/id_ed25519-cert.pub`: the certificate for the last pod you connected to.

Delete the folder to reset everything.

### Server and organization

By default the CLI talks to the AI Society platform with the org `ais`.
`--api-url` and `--org` (or `GODFATHER_API_URL` and `GODFATHER_ORG`) pick
another server or org; the ones you last logged in with are remembered.

## Troubleshooting

- **"Couldn't reach \<url\>"** — check your internet connection and that the
  API URL is correct (`godfather status` shows what's currently configured).
- **"Your token is invalid or expired"** — run `godfather auth` and sign in
  again. In the menu, the CLI offers to do this for you.
- **"Pod is not running"** — the pod stopped. Ask an officer to start it.
- **"You are no longer a member of this organization"** — rejoin the club's
  Discord server, then try again.
- **"SSH could not log in to the pod"** — the pod does not run the
  `godfather-base` image. Ask an officer to recreate it.
- **"A valid SSH public key is required"** — your CLI is older than the
  server. Run `godfather update`.
- **`ssh: command not found`** — install OpenSSH; the CLI uses your system's
  `ssh` and `ssh-keygen`.

## Development

The code is in `godfather_cli/`: `cli.py` (commands and menu), `picker.py` (arrow-key menu and pod picker), `auth.py`
(platform sign-in), `login_server.py` (the sign-in callback), `pod_manager.py` (API calls), `ssh_connector.py` (keys,
certificate, running ssh), `update_checker.py` (PyPI version check), `ui.py`
(shared console styling). Tests are in `tests/`:

```bash
uv sync --group dev
uv run pytest -q tests
```

`make check-cli` at the repo root runs ruff, the tests and a build, as CI does.

Releases go to PyPI when a version bump is merged to main; see the
repo README.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md).

## License

MIT — see the LICENSE file for details.

## Support

- [Discord](https://discord.gg/fXWXwz6fEG)

Built by [AI Society at Arizona State University](https://ais-asu.com/).
