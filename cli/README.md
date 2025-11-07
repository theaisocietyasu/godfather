# Godfather CLI

Command-line interface for managing AI Society RunPod environments.

## Installation

### From PyPI (Recommended)
```bash
pip install godfather-cli
```

### From GitHub
```bash
pip install git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
```

### From Source
```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather/cli
pip install -e .
```

## Configuration

Set the API endpoint (if different from default):

```bash
export GODFATHER_API_URL=https://your-backend.runpod.io
```

Or the CLI will prompt you for it on first run.

## Usage

### Interactive Mode
```bash
godfather
```

### List Available Pods
```bash
godfather list
```

### Connect to a Pod
```bash
godfather connect              # Interactive selection
godfather connect <pod-id>     # Direct connection
```

### Check Status
```bash
godfather status
```

### Authenticate
```bash
godfather auth
```

### Logout
```bash
godfather logout
```

## First Time Setup

1. Install the CLI:
   ```bash
   pip install godfather-cli
   ```

2. Run authentication:
   ```bash
   godfather auth
   ```

3. Visit the provided URL to get your authentication token

4. Start using the CLI:
   ```bash
   godfather list
   godfather connect
   ```

## Configuration File

The CLI stores configuration in `~/.godfather/config.json`:
- Authentication token
- API endpoint
- User preferences

## Requirements

- Python 3.7+
- SSH client (OpenSSH)
- Internet connection

## Support

For issues or questions:
- GitHub Issues: https://github.com/theaisocietyasu/godfather/issues
- Contact: AI Society ASU administrators

## License

MIT License - see LICENSE file for details
