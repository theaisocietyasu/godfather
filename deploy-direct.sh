#!/bin/bash
# Direct deployment script for RunPod (no Docker needed)
# This runs the applications directly in the container

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Godfather Direct Deployment (No Docker)             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create it from .env.example with your configuration."
    exit 1
fi

# Load environment variables and export them
set -a
source .env
set +a
echo "✅ Environment variables loaded"


echo "✅ All required environment variables present"
echo ""

# Stop any existing PM2 processes
echo "🛑 Stopping any existing processes..."
pm2 delete all 2>/dev/null || true
nginx -s stop 2>/dev/null || pkill -f "nginx" || true

# Kill any stray processes using ports
echo "🧹 Cleaning up ports..."
fuser -k 3000/tcp 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
sleep 2

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y nginx python3 python3-venv python3-pip curl psmisc > /dev/null 2>&1
echo "✅ System dependencies installed"

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
    apt-get install -y nodejs > /dev/null 2>&1
    echo "✅ Node.js installed"
fi

# Install PM2 globally if not present
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing PM2 process manager..."
    npm install -g pm2 > /dev/null 2>&1
    echo "✅ PM2 installed"
fi

echo ""
echo "🔨 Building Backend..."
cd /godfather/backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Backend dependencies installed"
else
    echo "❌ Failed to install backend dependencies"
    deactivate
    exit 1
fi

echo ""
echo "🔨 Building Frontend..."
cd /godfather/frontend

# Create .env.local file for Next.js from root .env
echo "📝 Creating frontend environment file..."
cat > .env.local << EOF
# Auto-generated from root .env file
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
CLERK_SECRET_KEY=${CLERK_SECRET_KEY}
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:5000}
NEXT_PUBLIC_FRONTEND_URL=${PUBLIC_URL}
EOF
echo "✅ Frontend environment file created"

echo "Installing Node.js dependencies..."
npm install
if [ $? -eq 0 ]; then
    echo "✅ Node.js dependencies installed"
else
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

echo "Building Next.js application (this may take a few minutes)..."
npm run build
if [ $? -eq 0 ]; then
    echo "✅ Frontend built successfully"
else
    echo "❌ Frontend build failed"
    exit 1
fi

echo ""
echo "🚀 Starting services with PM2..."

# Use PM2 ecosystem file for better process management
cd /godfather
pm2 start ecosystem.config.js

echo "✅ Services started with PM2"

# Save PM2 process list
pm2 save

# Wait for services to initialize
echo "⏳ Waiting for services to initialize..."
sleep 10

# Configure nginx
echo "⚙️  Configuring nginx..."
cp /godfather/nginx/nginx.direct.conf /etc/nginx/nginx.conf

# Test nginx config
nginx -t

# Start nginx
nginx
echo "✅ Nginx started"

echo ""
echo "⏳ Waiting for all services to initialize..."
sleep 5

# Health checks
echo ""
echo "🔍 Running health checks..."

# Check backend
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Backend health check passed"
else
    echo "⚠️  Backend health check failed (may still be starting)"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend health check passed"
else
    echo "⚠️  Frontend health check failed (may still be starting)"
fi

# Check nginx
if curl -s http://localhost/health > /dev/null 2>&1; then
    echo "✅ Nginx health check passed"
else
    echo "⚠️  Nginx health check failed"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   Deployment Complete! ✅                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo ""
echo "📊 Service Status:"
pm2 list
echo ""
echo "   Backend:  http://localhost:5000"
echo "   Frontend: http://localhost:3000"
echo "   Nginx:    http://localhost:80"
echo ""

echo "🌐 Your application is accessible at:"
if [ -n "$RUNPOD_PROXY_URL" ]; then
    echo "   $RUNPOD_PROXY_URL"
fi
if [ -n "$PUBLIC_URL" ]; then
    echo "   $PUBLIC_URL"
fi
echo ""

echo "📝 Useful PM2 Commands:"
echo "   View all processes:     pm2 list"
echo "   View backend logs:      pm2 logs backend"
echo "   View frontend logs:     pm2 logs frontend"
echo "   View all logs:          pm2 logs"
echo "   Restart backend:        pm2 restart backend"
echo "   Restart frontend:       pm2 restart frontend"
echo "   Stop all:               pm2 stop all"
echo "   Delete all:             pm2 delete all"
echo "   Process monitoring:     pm2 monit"
echo "   Save process list:      pm2 save"
echo ""
echo "📝 Other Useful Commands:"
echo "   Check nginx:            nginx -t"
echo "   Restart nginx:          nginx -s reload"
echo "   Health check script:    /godfather/check-status.sh"
echo ""

echo "🎉 Deployment successful!"
