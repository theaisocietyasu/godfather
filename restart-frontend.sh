#!/bin/bash

echo "🔄 Restarting frontend..."

# Kill any existing frontend processes
echo "🛑 Stopping existing frontend..."
pkill -f "npm start" || true
pkill -f "node.*next" || true
pkill -f "next start" || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 3

# Start frontend using node directly (not npm)
cd /godfather/frontend
echo "🚀 Starting frontend..."

# Use node directly to avoid npm exiting
nohup node_modules/.bin/next start > /var/log/godfather-frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Frontend process started with PID: $FRONTEND_PID"

# Wait for it to initialize
sleep 5

# Check if it's still running
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
    echo "📝 View logs: tail -f /var/log/godfather-frontend.log"
else
    echo "❌ Frontend process died"
    echo "📝 Check logs: tail -f /var/log/godfather-frontend.log"
    exit 1
fi

# Test if port 3000 is listening
sleep 3
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Port 3000 is listening"
    echo "🌐 Frontend should be accessible at http://localhost:3000"
else
    echo "⚠️  Port 3000 is not listening yet, checking logs..."
    tail -20 /var/log/godfather-frontend.log
fi
