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
    echo "Error: Username not provided" >&2
    exit 1
fi

# Create user's personal workspace
USER_WORKSPACE="/workspace/users/$USERNAME"
mkdir -p "$USER_WORKSPACE"
chown root:root "$USER_WORKSPACE"
chmod 700 "$USER_WORKSPACE"

# Log to stderr so it doesn't interfere with the profile path output
echo "Workspace ready: $USER_WORKSPACE" >&2

# If not admin, create restricted environment
if [ "$IS_ADMIN" != "true" ]; then
    # Create restricted user account if it doesn't exist
    if ! id "godfather_$USERNAME" &>/dev/null; then
        # Create user without sudo privileges and no password
        useradd -m -s /bin/bash -d "/home/godfather_$USERNAME" "godfather_$USERNAME" 2>/dev/null || true
        
        # Lock the user account to prevent password login
        passwd -l "godfather_$USERNAME" &>/dev/null || true
        
        # Create symlink from user home to their workspace
        ln -sf "/workspace/users/$USERNAME" "/home/godfather_$USERNAME/workspace" 2>/dev/null || true
        ln -sf "/workspace/shared" "/home/godfather_$USERNAME/shared" 2>/dev/null || true
    fi
    
    # Set proper ownership
    chown -R "godfather_$USERNAME:godfather_$USERNAME" "$USER_WORKSPACE" 2>/dev/null || true
    
    # Create a wrapper script that switches to the restricted user
    cat > /tmp/switch_to_restricted_$USERNAME.sh << SWITCHSCRIPT
#!/bin/bash
# Switch to restricted user account
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Welcome to Godfather Pod - Restricted User Mode"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Your workspace: /workspace/users/$USERNAME"
echo "🤝 Shared folder: /workspace/shared"
echo "⚠️  You have restricted access (no sudo/root)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Execute shell as restricted user
exec su - "godfather_$USERNAME" -c "cd /workspace/users/$USERNAME 2>/dev/null || cd /workspace/shared; exec bash --noprofile --norc"
SWITCHSCRIPT
    
    chmod +x /tmp/switch_to_restricted_$USERNAME.sh
    
    # Return path to switch script
    echo "/tmp/switch_to_restricted_$USERNAME.sh"
else
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
