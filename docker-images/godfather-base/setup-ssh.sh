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

# Create beautiful MOTD (Message of the Day)
echo "🎨 Creating welcome banner..."
cat > /etc/motd << 'MOTD'

MOTD

cat > /etc/update-motd.d/00-header << 'HEADER'
#!/bin/bash
cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗  ██████╗ ██████╗ ███████╗ ██████╗ ████████╗██╗  ██╗███████╗██████╗║
║  ██╔════╝ ██╔═══██╗██╔══██╗██╔════╝██╔═══██╗╚══██╔══╝██║  ██║██╔════╝██╔══██║
║  ██║  ███╗██║   ██║██║  ██║█████╗  ███████║   ██║   ███████║█████╗  ██████╔╝║
║  ██║   ██║██║   ██║██║  ██║██╔══╝  ██╔══██║   ██║   ██╔══██║██╔══╝  ██╔══██╗║
║  ╚██████╔╝╚██████╔╝██████╔╝██║     ██║  ██║   ██║   ██║  ██║███████╗██║  ██║║
║   ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝║
║                                                                              ║
║                      🚀 High-Performance Computing Pod 🚀                    ║
║                        Powered by RunPod & AIS Society                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

EOF
HEADER

chmod +x /etc/update-motd.d/00-header

# Create system info script
cat > /etc/update-motd.d/10-sysinfo << 'SYSINFO'
#!/bin/bash
echo ""
echo "  📊 System Information"
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    if [ -n "$GPU_INFO" ]; then
        echo "  💎 GPU: $GPU_INFO"
    fi
fi
echo "  🖥️  CPU: $(nproc) cores"
echo "  💾 RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  💿 Disk: $(df -h / | awk 'NR==2 {print $4}') available"
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
SYSINFO

chmod +x /etc/update-motd.d/10-sysinfo

# Disable other MOTD scripts to keep it clean
chmod -x /etc/update-motd.d/10-help-text 2>/dev/null || true
chmod -x /etc/update-motd.d/50-motd-news 2>/dev/null || true
chmod -x /etc/update-motd.d/90-updates-available 2>/dev/null || true

echo "✅ Welcome banner created"

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
    fi
    
    # Set proper ownership for the workspace
    chown -R "godfather_$USERNAME:godfather_$USERNAME" "$USER_WORKSPACE" 2>/dev/null || true
    
    # Give restricted user access to shared folder
    chmod 777 /workspace/shared 2>/dev/null || true
    
    # Create a wrapper script that switches to the restricted user
    cat > /tmp/switch_to_restricted_$USERNAME.sh << SWITCHSCRIPT
#!/bin/bash
# Switch to restricted user account

# Display user welcome banner
echo ""
echo "  ╔════════════════════════════════════════════════════════════════════════╗"
echo "  ║                    👤 Restricted User Mode                             ║"
echo "  ╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  📁 Your Workspace:     /workspace/users/$USERNAME"
echo "  🤝 Shared Folder:      /workspace/shared"
echo "  🔒 Access Level:       Restricted (No sudo/root)"
echo ""
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  � Quick Tips:"
echo "     • All your files are saved in your personal workspace"
echo "     • Use /workspace/shared for collaboration with others"
echo "     • Changes persist across sessions"
echo ""
echo "  ⚡ Common Commands:"
echo "     • ls -la              - List files"
echo "     • cd ~                - Go to home directory"
echo "     • pwd                 - Show current path"
echo "     • exit                - Disconnect from pod"
echo ""
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Execute shell as restricted user in their workspace
exec su - "godfather_$USERNAME" -c "cd /workspace/users/$USERNAME && exec bash --rcfile <(echo 'export PS1=\"\[\033[01;36m\]godfather_$USERNAME\[\033[00m\]@\[\033[01;35m\]pod\[\033[00m\]:\[\033[01;33m\]\w\[\033[00m\]\\$ \"'; echo 'alias ll=\"ls -lah --color=auto\"'; echo 'alias workspace=\"cd /workspace/users/$USERNAME\"'; echo 'alias shared=\"cd /workspace/shared\"')"
SWITCHSCRIPT
    
    chmod +x /tmp/switch_to_restricted_$USERNAME.sh
    
    # Return path to switch script
    echo "/tmp/switch_to_restricted_$USERNAME.sh"
else
    # Create admin shell wrapper
    cat > /tmp/admin_shell_$USERNAME.sh << ADMINSHELL
#!/bin/bash
# Godfather Admin Environment

# Display admin welcome banner
echo ""
echo "  ╔════════════════════════════════════════════════════════════════════════╗"
echo "  ║                        👑 Admin Mode                                   ║"
echo "  ╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  📁 Your Workspace:     /workspace/users/$USERNAME"
echo "  👑 Access Level:       Administrator (Full root access)"
echo "  ⚡ Sudo:               Available"
echo ""
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ⚠️  Important Reminders:"
echo "     • You have full system access - use with caution"
echo "     • Changes to system files affect all users"
echo "     • Keep user workspaces isolated and secure"
echo ""
echo "  ⚡ Quick Admin Commands:"
echo "     • workspace          - Jump to your workspace"
echo "     • shared             - Go to shared folder"
echo "     • htop               - View system resources"
echo "     • nvidia-smi         - Check GPU status"
echo ""
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Change to workspace
cd /workspace/users/$USERNAME 2>/dev/null || cd /workspace

# Start bash with custom prompt and aliases
exec bash --rcfile <(echo '
export PS1="\[\033[01;31m\]👑 \u\[\033[00m\]@\[\033[01;35m\]godfather\[\033[00m\]:\[\033[01;33m\]\w\[\033[00m\]\\$ "
alias ll="ls -lah --color=auto"
alias workspace="cd /workspace/users/$USERNAME"
alias shared="cd /workspace/shared"
alias pods="kubectl get pods 2>/dev/null || echo '\''kubectl not available'\''"
')
ADMINSHELL
    
    chmod +x /tmp/admin_shell_$USERNAME.sh
    
    # Return path to admin shell script
    echo "/tmp/admin_shell_$USERNAME.sh"
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
