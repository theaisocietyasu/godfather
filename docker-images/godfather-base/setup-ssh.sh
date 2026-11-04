#!/bin/bash
set -euo pipefail

echo "Godfather pod initialization"
echo "================================"

mkdir -p /root/.ssh /etc/ssh/godfather_principals
chmod 700 /root/.ssh

# Backend key: SFTP for the officer file manager and the ps command for presence.
# restrict turns off the pty and all forwarding for this key.
BACKEND_KEY="${GODFATHER_SSH_PUBLIC_KEY:-}"
if [ -n "$BACKEND_KEY" ]; then
    touch /root/.ssh/authorized_keys
    grep -vxF "$BACKEND_KEY" /root/.ssh/authorized_keys > /root/.ssh/authorized_keys.new || true
    mv /root/.ssh/authorized_keys.new /root/.ssh/authorized_keys
    grep -qxF "restrict $BACKEND_KEY" /root/.ssh/authorized_keys || echo "restrict $BACKEND_KEY" >> /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
    echo "Backend SSH key configured"
else
    echo "GODFATHER_SSH_PUBLIC_KEY not set: the web file manager will not reach this pod"
fi

# User CA: CLI users connect with short-lived certificates issued for this pod only
if [ -n "${GODFATHER_SSH_CA_PUBLIC_KEY:-}" ]; then
    echo "$GODFATHER_SSH_CA_PUBLIC_KEY" > /etc/ssh/godfather_user_ca.pub
    chmod 644 /etc/ssh/godfather_user_ca.pub
    echo "User CA configured"
else
    echo "GODFATHER_SSH_CA_PUBLIC_KEY not set: CLI logins will not work"
fi

if [ -n "${RUNPOD_POD_ID:-}" ]; then
    echo "gf-$RUNPOD_POD_ID" > /etc/ssh/godfather_principals/root
else
    echo "RUNPOD_POD_ID not set: CLI logins will not work"
    : > /etc/ssh/godfather_principals/root
fi
chmod 644 /etc/ssh/godfather_principals/root

# No password matches '*', so su to root fails. Key and certificate logins as root keep working.
usermod -p '*' root

# hidepid=2 hides the processes of other users. RunPod can refuse the remount.
mkdir -p /etc/godfather
if mount -o remount,hidepid=2 /proc 2>/dev/null; then
    echo on > /etc/godfather/hidepid
    echo "hidepid=2 on /proc"
else
    echo off > /etc/godfather/hidepid
    echo "hidepid=2 not allowed on /proc: members can see each other's processes"
fi

ssh-keygen -A >/dev/null
service ssh start || /usr/sbin/sshd
echo "SSH service started"

# Members can enter their own folder in /workspace/users but cannot list the others.
mkdir -p /workspace/users
chown root:root /workspace/users
chmod 711 /workspace/users

# Shared directory for collaboration; sticky so users cannot delete each other's files
mkdir -p /workspace/shared
chmod 1777 /workspace/shared

echo "Workspace ready"

# Create beautiful MOTD (Message of the Day)
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

echo "Welcome banner created"

echo "================================"
echo "Pod initialization complete"
echo ""
echo "Note: User workspaces will be created on first connection"

# Keep the container running
exec sleep infinity
