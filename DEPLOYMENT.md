# Deployment Guide

This guide covers deploying the Godfather system to RunPod and making the CLI available to users.

## Backend + Frontend Deployment (RunPod)

### Current Setup
You're using `deploy-direct.sh` to deploy backend and frontend on RunPod with nginx.

### Steps
1. Deploy to RunPod using your existing script:
   ```bash
   ./deploy-direct.sh
   ```

2. Note the public URL/IP assigned by RunPod (e.g., `https://xyz-12345.runpod.io`)

3. Update environment variables in your RunPod deployment:
   ```bash
   GODFATHER_API_URL=https://your-backend-url.runpod.io
   ```

## CLI Distribution

There are multiple ways to distribute the CLI to users:

### Option 1: PyPI (Recommended for Public Use)

**Pros:** 
- Users can install with simple `pip install godfather-cli`
- Automatic dependency management
- Version management
- Professional and standard approach

**Steps:**

1. **Prepare the package:**
   ```bash
   cd cli
   python -m pip install --upgrade build twine
   python -m build
   ```

2. **Upload to PyPI:**
   ```bash
   python -m twine upload dist/*
   ```

3. **Users install:**
   ```bash
   pip install godfather-cli
   export GODFATHER_API_URL=https://your-backend.runpod.io
   godfather auth
   ```

### Option 2: GitHub Releases (Good for Org Members)

**Pros:**
- No PyPI account needed
- Good for organization-specific tools
- Version controlled

**Steps:**

1. **Tag a release:**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **Create GitHub release:**
   - Go to GitHub → Releases → Create new release
   - Upload built wheel from `cli/dist/`

3. **Users install:**
   ```bash
   pip install git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
   # or
   pip install https://github.com/theaisocietyasu/godfather/releases/download/v1.0.0/godfather_cli-1.0.0-py3-none-any.whl
   ```

### Option 3: Direct Installation Script (Easiest for Users)

**Pros:**
- One-line installation
- Can set up everything automatically
- Best user experience

**Create an install script:**

```bash
# cli/install.sh
#!/bin/bash
set -e

echo "🚀 Installing Godfather CLI..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

# Install from GitHub
echo "📦 Installing from GitHub..."
pip3 install --user git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli

# Setup config
echo "⚙️  Setting up configuration..."
mkdir -p ~/.godfather

# Prompt for API URL if not set
if [ -z "$GODFATHER_API_URL" ]; then
    read -p "Enter your Godfather backend URL (e.g., https://backend.runpod.io): " API_URL
    echo "export GODFATHER_API_URL=$API_URL" >> ~/.bashrc
    echo "export GODFATHER_API_URL=$API_URL" >> ~/.zshrc 2>/dev/null || true
    export GODFATHER_API_URL=$API_URL
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "To get started:"
echo "  1. Reload your shell or run: source ~/.bashrc"
echo "  2. Run: godfather auth"
echo "  3. Visit the provided URL to get your token"
echo "  4. Run: godfather list"
echo ""
```

**Users install with:**
```bash
curl -sSL https://raw.githubusercontent.com/theaisocietyasu/godfather/main/cli/install.sh | bash
```

### Option 4: Docker Container (Alternative)

**Pros:**
- No Python installation needed
- Consistent environment
- Cross-platform

**Create Dockerfile:**

```dockerfile
# cli/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -e .

# Mount config directory
VOLUME /root/.godfather

ENTRYPOINT ["godfather"]
```

**Build and publish:**
```bash
cd cli
docker build -t theaisocietyasu/godfather-cli:latest .
docker push theaisocietyasu/godfather-cli:latest
```

**Users run:**
```bash
docker run -it -v ~/.godfather:/root/.godfather theaisocietyasu/godfather-cli list
```

Or create an alias:
```bash
alias godfather='docker run -it -v ~/.godfather:/root/.godfather theaisocietyasu/godfather-cli'
```

## Recommended Approach for Your Use Case

Given that this is for **AI Society members**, I recommend a **combination approach**:

### 1. Quick Setup Script (For onboarding)

Create `cli/install.sh`:

```bash
#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════╗"
echo "║   AI Society Godfather CLI Installation     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
else
    echo "⚠️  Unsupported OS: $OSTYPE"
    exit 1
fi

echo "🖥️  Detected OS: $OS"
echo ""

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required"
    echo "   Install from: https://www.python.org/downloads/"
    exit 1
fi

if ! command -v ssh &> /dev/null; then
    echo "❌ SSH client is required"
    if [[ "$OS" == "Linux" ]]; then
        echo "   Install with: sudo apt-get install openssh-client"
    elif [[ "$OS" == "macOS" ]]; then
        echo "   SSH should be pre-installed on macOS"
    fi
    exit 1
fi

echo "✅ All dependencies found"
echo ""

# Install CLI
echo "📦 Installing Godfather CLI..."
pip3 install --user --upgrade git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli

# Ensure pip bin directory is in PATH
if [[ "$OS" == "Linux" ]]; then
    PIP_BIN="$HOME/.local/bin"
elif [[ "$OS" == "macOS" ]]; then
    PIP_BIN="$HOME/Library/Python/$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/bin"
fi

if [[ ":$PATH:" != *":$PIP_BIN:"* ]]; then
    echo "export PATH=\"\$PATH:$PIP_BIN\"" >> ~/.bashrc
    echo "export PATH=\"\$PATH:$PIP_BIN\"" >> ~/.zshrc 2>/dev/null || true
    export PATH="$PATH:$PIP_BIN"
fi

# Set API URL
echo ""
echo "⚙️  Configuration..."
read -p "Enter Godfather backend URL [https://godfather.ais-asu.com]: " API_URL
API_URL=${API_URL:-https://godfather.ais-asu.com}

echo "export GODFATHER_API_URL=$API_URL" >> ~/.bashrc
echo "export GODFATHER_API_URL=$API_URL" >> ~/.zshrc 2>/dev/null || true
export GODFATHER_API_URL=$API_URL

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║           Installation Complete! ✅          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Reload your shell:"
echo "     source ~/.bashrc  (or restart your terminal)"
echo ""
echo "  2. Authenticate:"
echo "     godfather auth"
echo ""
echo "  3. List available pods:"
echo "     godfather list"
echo ""
echo "  4. Connect to a pod:"
echo "     godfather connect"
echo ""
echo "For help: godfather --help"
echo ""
```

### 2. Documentation Update

Add to your main README:

```markdown
## Getting Started for Members

### CLI Installation

Install the Godfather CLI with one command:

```bash
curl -sSL https://raw.githubusercontent.com/theaisocietyasu/godfather/main/cli/install.sh | bash
```

Then authenticate:
```bash
godfather auth
```

Visit the provided URL to get your authentication token from your Clerk account.

### Using the CLI

List available pods:
```bash
godfather list
```

Connect to a pod:
```bash
godfather connect
```
```

### 3. Backend Configuration

Make sure your backend URL is accessible and configure CORS properly:

```python
# backend/app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['*'])  # Or specific origins
```

## Summary

**For AI Society members, use this workflow:**

1. **Host backend on RunPod** (you're already doing this)
2. **Create the install script** (I can help you with this)
3. **Document the installation** in your README
4. **Share the one-line install command** with members:
   ```bash
   curl -sSL https://raw.githubusercontent.com/theaisocietyasu/godfather/main/cli/install.sh | bash
   ```

This gives you:
- ✅ Easy installation for members
- ✅ No manual dependency management
- ✅ Automatic API URL configuration
- ✅ Works on Linux and macOS
- ✅ Version controlled via Git

Would you like me to create the install script for you?
