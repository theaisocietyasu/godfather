# Godfather Base Image

A custom Docker image for RunPod that automatically sets up SSH keys for seamless CLI access.

## Features
- Based on `runpod/base:0.4.0-cuda11.8.0`
- Auto-configures SSH keys on container startup
- Creates workspace structure
- Includes common development tools (vim, git, curl, htop, tmux)

## Building the Image

```bash
cd docker-images/godfather-base
docker build -t yourdockerhub/godfather-base:latest .
docker push yourdockerhub/godfather-base:latest
```

## How It Works

1. When the container starts, `/start.sh` runs automatically
2. It reads `GODFATHER_SSH_PUBLIC_KEY` environment variable
3. Adds the public key to `/root/.ssh/authorized_keys`
4. Sets up workspace directories
5. Launches bash shell

## Usage in Godfather

Update the default image in the admin panel to:
```
yourdockerhub/godfather-base:latest
```

Or create variants for different use cases:
- `godfather-base:pytorch` - PyTorch pre-installed
- `godfather-base:tensorflow` - TensorFlow pre-installed
- `godfather-base:minimal` - Minimal setup

## Environment Variables

- `GODFATHER_SSH_PUBLIC_KEY` - (Required) Public SSH key for authentication
- `GODFATHER_SETUP` - (Optional) Set to "true" to indicate Godfather management

## Testing Locally

```bash
docker run -it \
  -e GODFATHER_SSH_PUBLIC_KEY="ssh-ed25519 AAAA... godfather-org-key" \
  yourdockerhub/godfather-base:latest
```
