# Godfather - Quick Start Guide

## For Administrators

### Deploying Backend + Frontend to RunPod

1. Deploy using your script:
   ```bash
   ./deploy-direct.sh
   ```

2. Note your RunPod URL (e.g., `https://xyz-12345.runpod.io`)

3. Share the installation command with members (see below)

## For Members

### Installing the CLI

**One-line installation:**
```bash
curl -sSL https://raw.githubusercontent.com/theaisocietyasu/godfather/main/cli/install.sh | bash
```

**Manual installation:**
```bash
pip install git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
export GODFATHER_API_URL=https://your-backend-url.runpod.io
```

### First Time Setup

1. **Authenticate:**
   ```bash
   godfather auth
   ```
   
2. **Visit the provided URL** to get your authentication token from Clerk

3. **Paste the token** when prompted

4. **You're ready!** Start using the CLI:
   ```bash
   godfather list      # See available pods
   godfather connect   # Connect to a pod
   ```

### Common Commands

```bash
# Interactive menu
godfather

# List all available pods
godfather list

# Connect to a pod (interactive selection)
godfather connect

# Connect to specific pod
godfather connect <pod-id>

# Check CLI status
godfather status

# Re-authenticate
godfather auth

# Logout
godfather logout
```

### Configuration

The CLI stores configuration in `~/.godfather/`:
- `config.json` - Authentication token and settings
- `ssh/godfather_key` - SSH private key for pod access

You can change the backend URL by setting:
```bash
export GODFATHER_API_URL=https://your-new-backend.com
```

### Troubleshooting

**"Token expired" error:**
```bash
godfather auth
```

**"SSH connection failed":**
- Make sure the pod is using the `theaisocietyasu/godfather-base` image
- Or that SSH keys are properly configured in the pod

**"Command not found":**
```bash
# Reload your shell
source ~/.bashrc  # or ~/.zshrc for zsh, or restart terminal

# Check if godfather is in PATH
which godfather

# If not found, add to PATH manually
export PATH="$PATH:$HOME/.local/bin"  # Linux
# or
export PATH="$PATH:$HOME/Library/Python/3.x/bin"  # macOS
```

**Can't connect to backend:**
- Check your `GODFATHER_API_URL` environment variable
- Verify the backend is running on RunPod
- Test with: `curl $GODFATHER_API_URL/health`

## Development

### Running Locally

1. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **CLI (pointing to local backend):**
   ```bash
   export GODFATHER_API_URL=http://localhost:5000
   godfather list
   ```

### Testing the CLI

```bash
cd cli
pip install -e .
godfather --help
```

## Architecture

```
┌─────────────────┐
│   CLI Users     │
│  (godfather)    │
└────────┬────────┘
         │
         │ HTTPS
         ↓
┌─────────────────┐      ┌──────────────┐
│  Flask Backend  │◄────►│   MongoDB    │
│  (RunPod)       │      └──────────────┘
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   RunPod API    │
│   (GPU Pods)    │
└─────────────────┘
```

## Support

- **GitHub Issues:** https://github.com/theaisocietyasu/godfather/issues
- **Contact:** AI Society ASU administrators
- **Documentation:** See README.md and DEPLOYMENT.md

## Security Notes

- **Never share your authentication token**
- **Tokens are stored locally** in `~/.godfather/config.json`
- **Use `godfather logout`** to clear your session
- **SSH keys are shared** across all organization members
- **Admin access** is controlled via Discord roles
