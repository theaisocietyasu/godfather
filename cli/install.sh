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

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "   ✓ Python $PYTHON_VERSION found"

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required"
    echo "   Install with: python3 -m ensurepip --upgrade"
    exit 1
fi

echo "   ✓ pip3 found"

if ! command -v ssh &> /dev/null; then
    echo "❌ SSH client is required"
    if [[ "$OS" == "Linux" ]]; then
        echo "   Install with: sudo apt-get install openssh-client"
    elif [[ "$OS" == "macOS" ]]; then
        echo "   SSH should be pre-installed on macOS"
    fi
    exit 1
fi

echo "   ✓ SSH client found"
echo ""

# Detect if running from repo or standalone
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/pyproject.toml" ] && [ -d "$SCRIPT_DIR/godfather_cli" ]; then
    echo "📦 Installing Godfather CLI from local repository..."
    pip3 install --user --upgrade -e "$SCRIPT_DIR"
    echo "   (Development mode - edits will be reflected immediately)"
else
    echo "📦 Installing Godfather CLI from GitHub..."
    pip3 install --user --upgrade git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
fi

# Ensure pip bin directory is in PATH
if [[ "$OS" == "Linux" ]]; then
    PIP_BIN="$HOME/.local/bin"
elif [[ "$OS" == "macOS" ]]; then
    PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PIP_BIN="$HOME/Library/Python/$PYTHON_VER/bin"
fi

if [[ ":$PATH:" != *":$PIP_BIN:"* ]]; then
    echo ""
    echo "⚙️  Adding $PIP_BIN to PATH..."
    
    # Add to bash profile
    if [ -f "$HOME/.bashrc" ]; then
        echo "" >> ~/.bashrc
        echo "# Godfather CLI" >> ~/.bashrc
        echo "export PATH=\"\$PATH:$PIP_BIN\"" >> ~/.bashrc
    fi
    
    # Add to zsh profile
    if [ -f "$HOME/.zshrc" ]; then
        echo "" >> ~/.zshrc
        echo "# Godfather CLI" >> ~/.zshrc
        echo "export PATH=\"\$PATH:$PIP_BIN\"" >> ~/.zshrc
    fi
    
    # Add to fish config
    if [ -d "$HOME/.config/fish" ]; then
        mkdir -p "$HOME/.config/fish/conf.d"
        echo "# Godfather CLI" > "$HOME/.config/fish/conf.d/godfather.fish"
        echo "set -gx PATH \$PATH $PIP_BIN" >> "$HOME/.config/fish/conf.d/godfather.fish"
    fi
    
    export PATH="$PATH:$PIP_BIN"
fi

# Set API URL
echo ""
echo "⚙️  Configuration..."
echo ""

# Try to detect BACKEND_URL from parent .env if we're in the repo
if [ -f "$SCRIPT_DIR/../.env" ]; then
    echo "🔍 Detecting backend URL from .env..."
    DETECTED_URL=$(grep '^BACKEND_URL=' "$SCRIPT_DIR/../.env" | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    if [ -n "$DETECTED_URL" ]; then
        API_URL="$DETECTED_URL"
        echo "   ✓ Found: $API_URL"
    else
        # Fallback to production URL
        API_URL="https://8bzhwve1ri5cw2-80.proxy.runpod.net"
        echo "   ⚠️  BACKEND_URL not found, using default: $API_URL"
    fi
else
    # Public install - use production URL
    API_URL="https://8bzhwve1ri5cw2-80.proxy.runpod.net"
    echo "   Using production URL: $API_URL"
fi

# Add to profiles (optional - CLI will auto-detect anyway)
if [ -f "$HOME/.bashrc" ]; then
    # Remove old entry if exists
    sed -i '/GODFATHER_API_URL/d' ~/.bashrc 2>/dev/null || true
    echo "export GODFATHER_API_URL=\"$API_URL\"" >> ~/.bashrc
fi

if [ -f "$HOME/.zshrc" ]; then
    sed -i '/GODFATHER_API_URL/d' ~/.zshrc 2>/dev/null || true
    echo "export GODFATHER_API_URL=\"$API_URL\"" >> ~/.zshrc
fi

if [ -d "$HOME/.config/fish" ]; then
    mkdir -p "$HOME/.config/fish/conf.d"
    echo "# Godfather CLI" > "$HOME/.config/fish/conf.d/godfather.fish"
    echo "set -gx GODFATHER_API_URL \"$API_URL\"" >> "$HOME/.config/fish/conf.d/godfather.fish"
fi

export GODFATHER_API_URL="$API_URL"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║           Installation Complete! ✅          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo " Next steps:"
echo ""
echo "  1. Reload your shell:"
if [[ "$SHELL" == *"fish"* ]]; then
    echo "     source ~/.config/fish/config.fish"
elif [[ "$SHELL" == *"zsh"* ]]; then
    echo "     source ~/.zshrc"
else
    echo "     source ~/.bashrc"
fi
echo "     (or just restart your terminal)"
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
echo "💡 Tips:"
echo "   - Run 'godfather --help' for all commands"
echo "   - Run 'godfather status' to check your connection"
echo "   - Run 'godfather logout' to clear your session"
echo ""
echo "📚 Documentation:"
echo "   https://github.com/theaisocietyasu/godfather"
echo ""
echo "❓ Need help?"
echo "   Contact AI Society administrators"
echo ""
