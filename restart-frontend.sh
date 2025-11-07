#!/bin/bash

echo "🔄 Restarting frontend..."

# Kill any existing frontend processes
echo "🛑 Stopping existing frontend..."
pkill -f "npm start" || true
pkill -f "node.*next" || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 3

# Start frontend
cd /godfather/frontend
echo "🚀 Starting frontend..."
nohup npm start > /var/log/godfather-frontend.log 2>&1 &

# Wait for it to start
sleep 5

# Check if it's running
FRONTEND_PID=$(pgrep -f "node.*next.*start" | head -n 1)
if [ -n "$FRONTEND_PID" ]; then
    echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
    echo "📝 View logs: tail -f /var/log/godfather-frontend.log"
else
    echo "❌ Frontend failed to start"
    echo "📝 Check logs: tail -f /var/log/godfather-frontend.log"
    exit 1
fi

# Test if port 3000 is listening
sleep 3
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Port 3000 is listening"
    echo "🌐 Frontend should be accessible at http://localhost:3000"
else
    echo "⚠️  Port 3000 is not listening yet, give it a few more seconds"
fi
