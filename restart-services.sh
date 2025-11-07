#!/bin/bash

echo "🔄 Restarting Godfather services..."

# Stop all PM2 processes
pm2 delete all 2>/dev/null || true

# Start services with updated configuration
pm2 start /godfather/ecosystem.config.js

# Save PM2 configuration
pm2 save

# Wait for services to start
sleep 3

# Show status
pm2 list

echo ""
echo "✅ Services restarted!"
echo ""
echo "📝 Check logs with:"
echo "   pm2 logs"
echo ""
echo "📊 Run health check:"
echo "   /godfather/check-status.sh"
