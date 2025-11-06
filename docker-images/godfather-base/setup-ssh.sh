#!/bin/bash
set -e

echo "🚀 Godfather Pod Initialization"
echo "================================"

# Start SSH service
echo "🔧 Starting SSH service..."
service ssh start || /usr/sbin/sshd
echo "✅ SSH service started"

# Setup SSH key if GODFATHER_SSH_PUBLIC_KEY is set
if [ -n "$GODFATHER_SSH_PUBLIC_KEY" ]; then
    echo "🔑 Setting up SSH key for Godfather access..."
    mkdir -p /root/.ssh
    
    # Add the key if it's not already there
    if ! grep -q "$GODFATHER_SSH_PUBLIC_KEY" /root/.ssh/authorized_keys 2>/dev/null; then
        echo "$GODFATHER_SSH_PUBLIC_KEY" >> /root/.ssh/authorized_keys
        chmod 700 /root/.ssh
        chmod 600 /root/.ssh/authorized_keys
        echo "✅ SSH key configured successfully"
    else
        echo "✅ SSH key already configured"
    fi
else
    echo "⚠️  GODFATHER_SSH_PUBLIC_KEY not set - SSH key authentication won't work"
fi

# Create workspace structure
echo "📁 Setting up workspace structure..."
mkdir -p /workspace/users
chmod 755 /workspace/users

# Create a shared directory for collaboration
mkdir -p /workspace/shared
chmod 777 /workspace/shared

echo "✅ Workspace ready"

# Create user setup script that will be called when users connect
cat > /usr/local/bin/godfather-user-setup.sh << 'USERSETUP'
#!/bin/bash
# This script sets up user workspace and permissions

USERNAME=$1
IS_ADMIN=$2

if [ -z "$USERNAME" ]; then
    echo "Error: Username not provided"
    exit 1
fi

# Create user's personal workspace
USER_WORKSPACE="/workspace/users/$USERNAME"
mkdir -p "$USER_WORKSPACE"
chown root:root "$USER_WORKSPACE"
chmod 700 "$USER_WORKSPACE"

echo "✅ Workspace created: $USER_WORKSPACE"

# If not admin, create restricted environment
if [ "$IS_ADMIN" != "true" ]; then
    echo "👤 Setting up restricted user environment..."
    
    # Create a restricted bash profile for non-admins
    cat > /tmp/restricted_profile_$USERNAME << 'PROFILE'
# Godfather Restricted User Environment
export PS1="\[\033[01;32m\]\u@godfather\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "

# Restrict access to user's own workspace
cd /workspace/users/$USERNAME 2>/dev/null || cd /workspace/shared

# Function to prevent leaving workspace
function cd() {
    local target="$1"
    if [ -z "$target" ]; then
        target="/workspace/users/$USERNAME"
    fi
    
    # Resolve to absolute path
    local abs_path=$(builtin cd "$target" 2>/dev/null && pwd)
    
    # Check if path is within allowed directories
    if [[ "$abs_path" == "/workspace/users/$USERNAME"* ]] || \
       [[ "$abs_path" == "/workspace/shared"* ]] || \
       [[ "$abs_path" == "/workspace/users/$USERNAME" ]] || \
       [[ "$abs_path" == "/workspace/shared" ]]; then
        builtin cd "$target"
    else
        echo "⛔ Access denied: You can only access your workspace (/workspace/users/$USERNAME) and shared folder (/workspace/shared)"
        return 1
    fi
}

# Disable dangerous commands
alias sudo='echo "⛔ sudo: Permission denied. Contact an admin if you need elevated privileges."'
alias su='echo "⛔ su: Permission denied."'
alias chmod='echo "⛔ chmod: Permission denied in restricted environment."'
alias chown='echo "⛔ chown: Permission denied in restricted environment."'

# Show welcome message
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Welcome to Godfather Pod - Restricted User Mode"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Your workspace: /workspace/users/$USERNAME"
echo "🤝 Shared folder: /workspace/shared"
echo "⚠️  You have restricted access (no sudo)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
PROFILE
    
    # Return path to restricted profile
    echo "/tmp/restricted_profile_$USERNAME"
else
    echo "👑 Setting up admin environment..."
    
    # Create admin profile
    cat > /tmp/admin_profile_$USERNAME << 'PROFILE'
# Godfather Admin Environment
export PS1="\[\033[01;31m\]\u@godfather(ADMIN)\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "

cd /workspace/users/$USERNAME 2>/dev/null || cd /workspace

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Welcome to Godfather Pod - Admin Mode"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Your workspace: /workspace/users/$USERNAME"
echo "👑 Full system access (sudo available)"
echo "⚠️  With great power comes great responsibility!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
PROFILE
    
    # Return path to admin profile
    echo "/tmp/admin_profile_$USERNAME"
fi
USERSETUP

chmod +x /usr/local/bin/godfather-user-setup.sh

echo "✅ User setup script installed"

echo "================================"
echo "🎉 Pod initialization complete!"
echo ""
echo "Note: User workspaces will be created on first connection"

# Keep container running and maintain SSH service
tail -f /dev/null
