# Godfather CLI

The AI Society Godfather CLI allows users to connect to available RunPod environments managed by the admin portal.

## Installation

### From Source

```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather/cli
pip install -e .
```

### From PyPI (when published)

```bash
pip install godfather-cli
```

## Usage

### Interactive Mode

Simply run the CLI without arguments for an interactive menu:

```bash
godfather
```

### Command Line Mode

```bash
# List available public pods
godfather list

# Connect to a pod interactively
godfather connect

# Connect to a specific pod
godfather connect <pod-id>

# Show CLI status
godfather status

# Logout
godfather logout
```

## Authentication

1. Visit the admin portal at your organization's Godfather URL
2. Login with Discord (requires Admin role in AI Society Discord server)
3. Copy your authentication token from the portal
4. Run `godfather` and paste the token when prompted

## Features

- **Secure Authentication**: Uses Clerk with Discord OAuth
- **Pod Discovery**: Automatically finds available public pods
- **Isolated Workspaces**: Each user gets their own folder in the pod
- **SSH Connection**: Direct terminal access to pods
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.7+
- SSH client (OpenSSH)
- Internet connection
- Valid AI Society Discord account with Admin role

## Configuration

Configuration is stored in `~/.godfather/config.json`. You can manually edit this file or use the CLI commands.

## Troubleshooting

### SSH Connection Issues

1. Ensure SSH client is installed:
   - **Windows**: Install OpenSSH or use WSL
   - **macOS**: SSH is pre-installed
   - **Linux**: Install `openssh-client`

2. Check firewall settings
3. Verify pod is running and accessible

### Authentication Issues

1. Ensure you have Admin role in AI Society Discord server
2. Check if your token has expired (run `godfather status`)
3. Re-authenticate using `godfather auth`

### Network Issues

1. Check internet connection
2. Verify API endpoint URL
3. Check if behind corporate firewall/proxy

## Support

For support, contact AI Society administrators or create an issue on GitHub.

## License

MIT License - see LICENSE file for details.