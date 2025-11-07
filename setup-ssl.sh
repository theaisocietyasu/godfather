#!/bin/bash
# SSL Certificate Setup Script for Godfather
# This script helps you set up HTTPS using Let's Encrypt

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Godfather SSL Certificate Setup (HTTPS)            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root or with sudo"
    echo "Usage: sudo ./setup-ssl.sh"
    exit 1
fi

# Load environment variables
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create it first with your configuration."
    exit 1
fi

source .env

# Extract domain from PUBLIC_URL or DOMAIN variable
if [ -n "$DOMAIN" ]; then
    DOMAIN_NAME="$DOMAIN"
elif [ -n "$PUBLIC_URL" ]; then
    DOMAIN_NAME=$(echo "$PUBLIC_URL" | sed -e 's|^https\?://||' -e 's|/.*||')
else
    echo "❌ No domain configured in .env"
    echo "Please set DOMAIN or PUBLIC_URL variable"
    exit 1
fi

echo "🌐 Configuring SSL for: $DOMAIN_NAME"
echo ""

# Prompt for email
read -p "📧 Enter your email for Let's Encrypt notifications: " EMAIL

if [ -z "$EMAIL" ]; then
    echo "❌ Email is required"
    exit 1
fi

echo ""
echo "📝 Configuration:"
echo "   Domain: $DOMAIN_NAME"
echo "   Email: $EMAIL"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

# Install certbot
echo ""
echo "📦 Installing certbot..."
apt-get update -qq
apt-get install -y certbot python3-certbot-nginx

# Stop nginx temporarily
echo "🛑 Stopping nginx temporarily..."
docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true

# Wait for port 80 to be free
sleep 3

# Obtain certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
echo "    This may take a minute..."
echo ""

certbot certonly --standalone \
    -d "$DOMAIN_NAME" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --preferred-challenges http

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Certificate generation failed!"
    echo ""
    echo "Common issues:"
    echo "1. Domain not pointing to this server yet (check DNS)"
    echo "2. Port 80 not accessible from internet"
    echo "3. Firewall blocking connections"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check DNS: nslookup $DOMAIN_NAME"
    echo "  - Should point to: $(curl -s ifconfig.me)"
    echo ""
    exit 1
fi

# Create SSL directory
echo "📁 Setting up SSL certificates..."
mkdir -p ./nginx/ssl

# Copy certificates
cp "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ./nginx/ssl/cert.pem
cp "/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem" ./nginx/ssl/key.pem

# Set permissions
chmod 644 ./nginx/ssl/cert.pem
chmod 600 ./nginx/ssl/key.pem

echo "✅ Certificates installed"

# Update environment variables for HTTPS
echo "📝 Updating environment variables for HTTPS..."
sed -i "s|^PUBLIC_URL=http://|PUBLIC_URL=https://|g" .env
sed -i "s|^NEXT_PUBLIC_API_URL=http://|NEXT_PUBLIC_API_URL=https://|g" .env

# Start services with SSL
echo "🚀 Starting services with HTTPS..."
docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 10

# Test HTTPS
echo ""
echo "🔍 Testing HTTPS connection..."
if curl -k -s "https://localhost/health" > /dev/null 2>&1; then
    echo "✅ HTTPS is working locally!"
else
    echo "⚠️  Could not connect to HTTPS locally"
    echo "    Check logs: docker compose -f docker-compose.prod.yml logs nginx"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  SSL Setup Complete! ✅                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Your site should now be accessible at:"
echo "   https://$DOMAIN_NAME"
echo ""
echo "📋 Next Steps:"
echo "   1. Visit https://$DOMAIN_NAME to verify HTTPS works"
echo "   2. Update Clerk redirect URLs to use https://"
echo "   3. Update Discord OAuth redirect URLs to use https://"
echo ""
echo "🔄 Certificate Renewal:"
echo "   Certificates auto-renew. To manually renew:"
echo "   sudo certbot renew"
echo ""
echo "📝 Certificate expires in 90 days"
echo "   Location: /etc/letsencrypt/live/$DOMAIN_NAME/"
echo ""
echo "🛑 To stop services:"
echo "   docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml down"
echo ""

# Set up auto-renewal cron job
echo "⏰ Setting up automatic certificate renewal..."
(crontab -l 2>/dev/null; echo "0 0 * * * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem $(pwd)/nginx/ssl/cert.pem && cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem $(pwd)/nginx/ssl/key.pem && docker compose -f $(pwd)/docker-compose.prod.yml -f $(pwd)/docker-compose.ssl.yml restart nginx") | crontab -

echo "✅ Auto-renewal configured (runs daily at midnight)"
echo ""
echo "🎉 Setup complete!"
