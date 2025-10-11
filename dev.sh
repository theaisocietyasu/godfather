#!/bin/bash

# Development helper script for Godfather

case "$1" in
    "start")
        echo "🚀 Starting Godfather services..."
        docker-compose up -d
        echo "✅ Services started"
        echo "   Frontend: http://localhost:3000"
        echo "   Backend: http://localhost:5000"
        echo "   Admin Portal: http://localhost"
        ;;
    
    "stop")
        echo "🛑 Stopping Godfather services..."
        docker-compose down
        echo "✅ Services stopped"
        ;;
    
    "restart")
        echo "🔄 Restarting Godfather services..."
        docker-compose restart
        echo "✅ Services restarted"
        ;;
    
    "build")
        echo "🏗️ Building Godfather services..."
        docker-compose build --no-cache
        echo "✅ Build complete"
        ;;
    
    "logs")
        service=${2:-""}
        if [ -n "$service" ]; then
            echo "📋 Showing logs for $service..."
            docker-compose logs -f "$service"
        else
            echo "📋 Showing all logs..."
            docker-compose logs -f
        fi
        ;;
    
    "shell")
        service=${2:-"backend"}
        echo "🐚 Opening shell in $service container..."
        docker-compose exec "$service" /bin/bash
        ;;
    
    "reset")
        echo "⚠️  Resetting all data (this will delete everything)..."
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            docker system prune -f
            echo "✅ Reset complete"
        else
            echo "❌ Reset cancelled"
        fi
        ;;
    
    "update")
        echo "📦 Updating Godfather..."
        git pull
        docker-compose build --no-cache
        docker-compose up -d
        echo "✅ Update complete"
        ;;
    
    "status")
        echo "📊 Godfather Service Status:"
        docker-compose ps
        echo
        echo "🔍 Health Checks:"
        curl -sf http://localhost/health > /dev/null && echo "✅ Nginx: Healthy" || echo "❌ Nginx: Down"
        curl -sf http://localhost:3000 > /dev/null && echo "✅ Frontend: Healthy" || echo "❌ Frontend: Down"
        curl -sf http://localhost:5000/health > /dev/null && echo "✅ Backend: Healthy" || echo "❌ Backend: Down"
        docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1 && echo "✅ MongoDB: Healthy" || echo "❌ MongoDB: Down"
        ;;
    
    "cli")
        echo "🔧 Installing/updating Godfather CLI..."
        cd cli
        pip install -e . --force-reinstall
        cd ..
        echo "✅ CLI updated"
        echo "   Run 'godfather' to use the CLI"
        ;;
    
    "backup")
        backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        echo "💾 Creating backup in $backup_dir..."
        
        # Backup MongoDB
        docker-compose exec -T mongodb mongodump --out /tmp/backup
        docker-compose exec -T mongodb tar czf /tmp/mongodb_backup.tar.gz -C /tmp backup
        docker cp $(docker-compose ps -q mongodb):/tmp/mongodb_backup.tar.gz "$backup_dir/"
        
        # Backup environment files
        cp .env "$backup_dir/" 2>/dev/null || echo "No .env file to backup"
        cp frontend/.env.local "$backup_dir/frontend.env" 2>/dev/null || echo "No frontend .env.local to backup"
        
        echo "✅ Backup created: $backup_dir"
        ;;
    
    "help"|*)
        echo "🎯 Godfather Development Helper"
        echo
        echo "Usage: $0 <command> [options]"
        echo
        echo "Commands:"
        echo "  start          Start all services"
        echo "  stop           Stop all services"
        echo "  restart        Restart all services"
        echo "  build          Build all Docker images"
        echo "  logs [service] Show logs (optionally for specific service)"
        echo "  shell [service] Open shell in container (default: backend)"
        echo "  reset          Reset all data (dangerous!)"
        echo "  update         Update from git and rebuild"
        echo "  status         Show service status and health"
        echo "  cli            Install/update CLI tool"
        echo "  backup         Create backup of data and config"
        echo "  help           Show this help message"
        echo
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs backend"
        echo "  $0 shell frontend"
        ;;
esac