#!/bin/bash
set -e

echo "🚀 Godfather Pod Initialization"
echo "================================"

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
echo "📁 Setting up workspace..."
mkdir -p /workspace/users
chmod 755 /workspace/users
echo "✅ Workspace ready"

echo "================================"
echo "🎉 Pod initialization complete!"
echo ""

# Keep the container running by executing bash
exec /bin/bash
