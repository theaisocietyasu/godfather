#!/bin/bash
set -e

echo "🚀 Deploying Godfather to RunPod"
echo "================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create it from .env.example with your configuration."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check required variables
REQUIRED_VARS=("RUNPOD_API_KEY" "CLERK_SECRET_KEY" "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" "DISCORD_BOT_TOKEN" "DISCORD_GUILD_ID" "PUBLIC_URL")

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    fi
done

echo "✅ Environment variables loaded"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed"
fi

# Install Docker Compose if not present
if ! docker compose version &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    apt-get update
    apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose installed"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Build and start services
echo "🏗️  Building and starting services..."
docker compose --env-file .env up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo ""
    echo "================================"
    echo "✅ Deployment successful!"
    echo "================================"
    echo ""
    echo "🌐 Your application is running at:"
    echo "   $PUBLIC_URL"
    echo ""
    echo "📊 Service Status:"
    docker compose ps
    echo ""
    echo "📝 To view logs:"
    echo "   docker compose logs -f"
    echo ""
    echo "🛑 To stop:"
    echo "   docker compose down"
    echo ""
else
    echo "❌ Some services failed to start"
    echo "Check logs with: docker compose logs"
    exit 1
fi
