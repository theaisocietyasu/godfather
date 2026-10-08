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
2. It opens the AI Society platform's sign-in page in your browser (and
   prints the link). Sign in with Discord and copy the token shown there.
3. Paste the token back into the terminal. The CLI checks it with the
   platform and stores it in `~/.godfather/config.json`.
4. From the menu (or `godfather connect`), pick a pod. The CLI creates an SSH
   key on your machine the first time, asks the server for a 12-hour
   certificate for that pod, and opens the connection.

A token lasts 90 days. When it expires, or if you leave the Discord server,
the CLI asks you to log in again.

You need OpenSSH installed (`ssh` and `ssh-keygen`). macOS, Linux and
Windows 10+ ship it.

## Usage

### Interactive menu

Running `godfather` with no arguments opens a menu to list pods, connect,
check status, or log out.

### Commands

```bash
godfather list                    # List pods you can connect to
godfather connect                 # Connect to a pod, picking from a list
godfather connect <pod-id>        # Connect to a specific pod
godfather status                  # Show login and configuration status
godfather auth                    # Log in, or refresh an expired session
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
  again.
- **"You are no longer a member of this organization"** — rejoin the club's
  Discord server, then try again.
- **"SSH could not log in to the pod"** — the pod does not run the
  `godfather-base` image. Ask an officer to recreate it.
- **"A valid SSH public key is required"** — your CLI is older than the
  server. Run `godfather update`.
- **`ssh: command not found`** — install OpenSSH; the CLI uses your system's
  `ssh` and `ssh-keygen`.

## Development

The code is in `godfather_cli/`: `cli.py` (commands and menu), `auth.py`
(platform sign-in), `pod_manager.py` (API calls), `ssh_connector.py` (keys,
certificate, running ssh), `update_checker.py` (PyPI version check), `ui.py`
(shared console styling). Tests are in `tests/`:

```bash
pip install -e . pytest
pytest -q tests
```

Releases go to PyPI when a version bump is merged to main; see the
repo README.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes and open a Pull Request.

## License

MIT — see the LICENSE file for details.

## Support

- [Discord](https://discord.gg/fXWXwz6fEG)

Built by [AI Society at Arizona State University](https://ais-asu.com/).
