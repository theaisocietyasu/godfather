#!/bin/bash
# Quick deployment script for RunPod
# Run this directly in your RunPod instance

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Godfather RunPod Deployment - Quick Setup           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found"
    echo "Please run this script from the /godfather directory"
    exit 1
fi

# Step 1: Create .env.production if it doesn't exist
if [ ! -f ".env.production" ]; then
    echo "📝 Creating .env.production template..."
    cat > .env.production << 'EOF'
# MongoDB Configuration
MONGODB_URI=mongodb://admin:password@mongodb:27017/godfather?authSource=admin

# RunPod API (Get from https://runpod.io/console/user/settings)
RUNPOD_API_KEY=your_runpod_api_key_here

# Clerk Authentication (Get from https://dashboard.clerk.com/)
CLERK_SECRET_KEY=your_clerk_secret_key_here
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here

# Discord Bot (Get from Discord Developer Portal)
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_discord_guild_id_here

# Public URL (Your RunPod instance URL)
PUBLIC_URL=https://your-instance-id.proxy.runpod.net
NEXT_PUBLIC_API_URL=https://your-instance-id.proxy.runpod.net/api
EOF
    
    echo ""
    echo "✅ Created .env.production template"
    echo ""
    echo "⚠️  IMPORTANT: You must edit .env.production with your actual values!"
    echo ""
    echo "Run this command to edit:"
    echo "  nano .env.production"
    echo ""
    echo "After editing, run this script again."
    exit 0
fi

# Step 2: Validate environment variables
echo "🔍 Validating environment variables..."
source .env.production

MISSING_VARS=()
[ -z "$RUNPOD_API_KEY" ] || [ "$RUNPOD_API_KEY" == "your_runpod_api_key_here" ] && MISSING_VARS+=("RUNPOD_API_KEY")
[ -z "$CLERK_SECRET_KEY" ] || [ "$CLERK_SECRET_KEY" == "your_clerk_secret_key_here" ] && MISSING_VARS+=("CLERK_SECRET_KEY")
[ -z "$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" ] || [ "$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" == "your_clerk_publishable_key_here" ] && MISSING_VARS+=("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
[ -z "$DISCORD_BOT_TOKEN" ] || [ "$DISCORD_BOT_TOKEN" == "your_discord_bot_token_here" ] && MISSING_VARS+=("DISCORD_BOT_TOKEN")
[ -z "$DISCORD_GUILD_ID" ] || [ "$DISCORD_GUILD_ID" == "your_discord_guild_id_here" ] && MISSING_VARS+=("DISCORD_GUILD_ID")
[ -z "$PUBLIC_URL" ] || [ "$PUBLIC_URL" == "https://your-instance-id.proxy.runpod.net" ] && MISSING_VARS+=("PUBLIC_URL")

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing or placeholder environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please edit .env.production with actual values:"
    echo "  nano .env.production"
    echo ""
    exit 1
fi

echo "✅ Environment variables validated"
echo ""

# Step 3: Check Docker
echo "🐳 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Step 4: Check Docker Compose
echo "🔧 Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose plugin..."
    apt-get update -qq
    apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Starting Deployment                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Step 5: Stop existing containers
echo "🛑 Stopping any existing containers..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
echo ""

# Step 6: Build and start
echo "🏗️  Building Docker images (this may take a few minutes)..."
docker compose -f docker-compose.prod.yml build

echo ""
echo "🚀 Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 15

# Step 7: Check status
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   Deployment Complete! ✅                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Service Status:"
docker compose -f docker-compose.prod.yml ps
echo ""

echo "🌐 Your application should be accessible at:"
echo "   $PUBLIC_URL"
echo ""

echo "🔍 Health Check:"
if curl -s http://localhost/health > /dev/null; then
    echo "   ✅ Application is responding!"
else
    echo "   ⚠️  Application might still be starting..."
fi

echo ""
echo "📝 Useful Commands:"
echo "   View logs:    docker compose -f docker-compose.prod.yml logs -f"
echo "   Restart:      docker compose -f docker-compose.prod.yml restart"
echo "   Stop:         docker compose -f docker-compose.prod.yml down"
echo "   Status:       docker compose -f docker-compose.prod.yml ps"
echo ""

echo "🎉 Deployment complete!"
