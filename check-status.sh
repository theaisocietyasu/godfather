#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Godfather System Status Check                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check processes
echo "📊 Running Processes:"
echo "----------------------------------------"
BACKEND_PID=$(pgrep -f "python app.py" | head -n 1)
FRONTEND_PID=$(pgrep -f "node.*next" | head -n 1)
NGINX_PID=$(pgrep -f "nginx: master" | head -n 1)

if [ -n "$BACKEND_PID" ]; then
    echo "✅ Backend:  Running (PID: $BACKEND_PID)"
else
    echo "❌ Backend:  Not running"
fi

if [ -n "$FRONTEND_PID" ]; then
    echo "✅ Frontend: Running (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend: Not running"
fi

if [ -n "$NGINX_PID" ]; then
    echo "✅ Nginx:    Running (PID: $NGINX_PID)"
else
    echo "❌ Nginx:    Not running"
fi
echo ""

# Check ports
echo "🔌 Port Status:"
echo "----------------------------------------"
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PORT_5000=$(lsof -Pi :5000 -sTCP:LISTEN -t)
    echo "✅ Port 5000 (Backend):  Listening (PID: $PORT_5000)"
else
    echo "❌ Port 5000 (Backend):  Not listening"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PORT_3000=$(lsof -Pi :3000 -sTCP:LISTEN -t)
    echo "✅ Port 3000 (Frontend): Listening (PID: $PORT_3000)"
else
    echo "❌ Port 3000 (Frontend): Not listening"
fi

if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PORT_80=$(lsof -Pi :80 -sTCP:LISTEN -t)
    echo "✅ Port 80   (Nginx):    Listening (PID: $PORT_80)"
else
    echo "❌ Port 80   (Nginx):    Not listening"
fi
echo ""

# Test endpoints
echo "🔍 Endpoint Tests:"
echo "----------------------------------------"

# Test backend
if curl -s -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Backend (localhost:5000/health): OK"
else
    echo "❌ Backend (localhost:5000/health): FAILED"
fi

# Test frontend
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend (localhost:3000): OK"
else
    echo "❌ Frontend (localhost:3000): FAILED"
fi

# Test nginx
if curl -s -f http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Nginx (localhost:80/health): OK"
else
    echo "❌ Nginx (localhost:80/health): FAILED"
fi

# Test nginx proxy to backend
if curl -s -f http://localhost:80/api/health > /dev/null 2>&1; then
    echo "✅ Nginx → Backend proxy: OK"
else
    echo "❌ Nginx → Backend proxy: FAILED"
fi

# Test nginx proxy to frontend
if curl -s -f http://localhost:80 > /dev/null 2>&1; then
    echo "✅ Nginx → Frontend proxy: OK"
else
    echo "❌ Nginx → Frontend proxy: FAILED"
fi
echo ""

# Show recent logs
echo "📝 Recent Logs (last 5 lines each):"
echo "----------------------------------------"
echo "Backend:"
tail -5 /var/log/godfather-backend.log 2>/dev/null || echo "  No backend logs"
echo ""
echo "Frontend:"
tail -5 /var/log/godfather-frontend.log 2>/dev/null || echo "  No frontend logs"
echo ""
echo "Nginx Error:"
tail -5 /var/log/nginx/error.log 2>/dev/null || echo "  No nginx error logs"
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     Recommendations                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Provide recommendations
if [ -z "$FRONTEND_PID" ]; then
    echo "⚠️  Frontend is not running - run: ./restart-frontend.sh"
fi

if [ -z "$BACKEND_PID" ]; then
    echo "⚠️  Backend is not running - run: cd /godfather/backend && source venv/bin/activate && nohup python app.py > /var/log/godfather-backend.log 2>&1 &"
fi

if [ -z "$NGINX_PID" ]; then
    echo "⚠️  Nginx is not running - run: nginx"
fi

echo ""
