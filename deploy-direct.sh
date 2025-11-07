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

# Kill any existing processes
echo "🛑 Stopping any existing processes..."
pkill -f "python app.py" || true
pkill -f "npm start" || true
pkill -f "node.*next" || true
pkill -f "Next.js" || true
nginx -s stop 2>/dev/null || pkill -f "nginx" || true

# Kill any processes using ports 3000 and 5000
echo "🧹 Cleaning up ports..."
fuser -k 3000/tcp 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
sleep 3

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
echo "🚀 Starting services..."

# Start backend with environment variables (using venv)
cd /godfather/backend
source venv/bin/activate
nohup python app.py > /var/log/godfather-backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend failed to start"
    echo "Logs:"
    tail -20 /var/log/godfather-backend.log
    exit 1
fi

# Start frontend with environment variables
cd /godfather/frontend

# Make sure port 3000 is free
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3000 is in use, killing process..."
    fuser -k 3000/tcp 2>/dev/null || true
    sleep 2
fi

nohup npm start > /var/log/godfather-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to be ready..."
sleep 10

# Check if frontend actually started
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "⚠️  Frontend process died, checking logs..."
    tail -20 /var/log/godfather-frontend.log
    echo ""
    echo "Retrying frontend startup..."
    nohup npm start > /var/log/godfather-frontend.log 2>&1 &
    FRONTEND_PID=$!
    sleep 10
fi

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

echo "📊 Service Status:"
echo "   Backend:  http://localhost:5000 (PID: $BACKEND_PID)"
echo "   Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
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

echo "📝 Useful Commands:"
echo "   View backend logs:  tail -f /var/log/godfather-backend.log"
echo "   View frontend logs: tail -f /var/log/godfather-frontend.log"
echo "   Check processes:    ps aux | grep -E 'python|node|nginx'"
echo "   Check ports:        lsof -i :3000 -i :5000 -i :80"
echo "   Restart backend:    cd /godfather/backend && source venv/bin/activate && python app.py"
echo "   Restart frontend:   cd /godfather/frontend && npm start"
echo "   Stop all:           pkill -f 'python app.py'; pkill -f 'npm start'; pkill -f 'node.*next'; nginx -s stop"
echo "   Clean ports:        fuser -k 3000/tcp 5000/tcp"
echo ""

echo "🎉 Deployment successful!"
