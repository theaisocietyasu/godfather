#!/bin/bash

# AI Society Godfather Setup Script
# This script sets up the entire Godfather admin portal system

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                AI Society Godfather Setup                    ║"
echo "║              RunPod Admin Portal Installer                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment configuration..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Please edit .env file and add your API keys:"
    echo "   - RUNPOD_API_KEY"
    echo "   - CLERK_SECRET_KEY"
    echo "   - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
    echo "   - DISCORD_BOT_TOKEN"
    echo "   - DISCORD_GUILD_ID"
    echo
    read -p "Press Enter after you've configured the .env file..."
fi

# Create frontend env file
if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend environment configuration..."
    cp frontend/.env.local.example frontend/.env.local
    echo "⚠️  Please edit frontend/.env.local with your Clerk keys"
    echo
fi

# Create SSL directory for nginx (self-signed for development)
echo "🔐 Setting up SSL certificates for development..."
mkdir -p nginx/ssl

if [ ! -f nginx/ssl/cert.pem ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=AZ/L=Tempe/O=AI Society ASU/CN=localhost" \
        2>/dev/null || echo "⚠️  SSL certificate generation failed. You may need to install OpenSSL."
fi

echo "✅ SSL certificates ready"
echo

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check MongoDB
if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is running"
else
    echo "⚠️  MongoDB may not be ready yet"
fi

# Check Backend
if curl -sf http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend may not be ready yet"
fi

# Check Frontend
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend may not be ready yet"
fi

# Check Nginx
if curl -sf http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Nginx is running"
else
    echo "⚠️  Nginx may not be ready yet"
fi

echo
echo "🎉 Godfather Admin Portal setup complete!"
echo
echo "📋 Next steps:"
echo "1. Configure your environment variables in .env and frontend/.env.local"
echo "2. Set up Clerk authentication with Discord OAuth"
echo "3. Configure your Discord bot with proper permissions"
echo "4. Add your RunPod API key"
echo
echo "🌐 Access your portal:"
echo "   Local: http://localhost"
echo "   Production: https://admin.ais-asu.com (after DNS setup)"
echo
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Update: git pull && docker-compose build && docker-compose up -d"
echo
echo "📚 For more information, check the README.md file"
echo

# Install CLI
echo "🔧 Installing Godfather CLI..."
cd cli
pip install -e . 2>/dev/null || pip3 install -e . 2>/dev/null || echo "⚠️  CLI installation failed. You may need to install Python and pip."
cd ..

if command -v godfather &> /dev/null; then
    echo "✅ Godfather CLI installed successfully"
    echo "   Run 'godfather' to use the CLI"
else
    echo "⚠️  CLI installation may have failed"
fi

echo
echo "🚀 Setup complete! Your AI Society Godfather portal is ready."