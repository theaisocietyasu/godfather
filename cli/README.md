# Godfather CLI

Command-line client for AI Society ASU's Godfather platform. Lets members log
in with their Discord account and SSH into shared RunPod GPU pods without
touching the RunPod dashboard.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
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
2. It prints a link to the admin portal's `/cli-auth` page. Open it, sign in
   with Discord, and copy the token shown there.
3. Paste the token back into the terminal. The CLI verifies it with the
   backend and stores it in `~/.godfather/config.json`.
4. From the menu (or `godfather connect`), pick a pod. The CLI fetches your
   SSH key and opens the connection for you.

You only need to log in once — the CLI reuses the stored token until it
expires, at which point it'll prompt you to log in again automatically.

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

# Point the CLI at a non-default backend (mainly for local development)
godfather --api-url https://your-backend.example.com list
```

## Configuration

The CLI stores its config in `~/.godfather/config.json`:

```json
{
  "token": "discord_<your_discord_id>_<timestamp>",
  "discord_user_id": "<your_discord_id>"
}
```

Your fetched SSH private key is written to `~/.godfather/ssh/godfather_key`
with `0600` permissions and reused for future connections.

### Backend URL

By default the CLI talks to `https://admin.ais-asu.com`. You can override
this with, in order of priority: `GODFATHER_API_URL`, `BACKEND_URL`,
`NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_API_URL`, or the `--api-url` flag.
This mainly matters if you're running the backend locally.

## Troubleshooting

- **"Couldn't reach \<url\>"** — check your internet connection and that the
  API URL is correct (`godfather status` shows what's currently configured).
- **"That token is invalid or expired"** — get a fresh token from the admin
  portal's `/cli-auth` page and try again.
- **SSH connection fails with "SSH key not set up on this pod"** — the pod
  needs the Godfather SSH key added to `authorized_keys`. Pods built from the
  `godfather-base` image do this automatically; otherwise the CLI prints the
  manual fix to run from the RunPod web terminal.
- **`ssh: command not found`** — install OpenSSH; the CLI shells out to your
  system's `ssh` client to connect.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes and open a Pull Request.

## License

MIT — see the LICENSE file for details.

## Support

- [Discord](https://discord.gg/fXWXwz6fEG)

Built by [AI Society at Arizona State University](https://ais-asu.com/).
