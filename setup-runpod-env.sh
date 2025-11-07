#!/bin/bash
# Quick script to set up .env file on RunPod instance

cat > .env << 'EOF'
# Environment variables for Godfather project

# RunPod API
RUNPOD_API_KEY=rpa_KZJCHLQRKKGCPAFD9BZ14473IB2VW8VA10T6M04V1o6nbo

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_MtLh94NRsqqdHV0A873RX8FSGCg6hNJqluwN3Msyu1
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_aW52aXRpbmctdG9ydG9pc2UtNzAuY2xlcmsuYWNjb3VudHMuZGV2JA

# Discord Bot
DISCORD_BOT_TOKEN=MTQzMjYzMjExMDIzMjg5OTY4Ng.G-CkdT.rWEhZ4MFRU3HGx9vF9aRou5wbbvXZg2Urqh_XU
DISCORD_GUILD_ID=1142945652834304100
ADMIN_ROLE_ID=1407280036742041660

# MongoDB (Production - MongoDB Atlas)
MONGODB_URI=mongodb+srv://softwareTeam:Wt4qADxB0WsNK3tQ@cluster0.pj0m3k9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

# JWT Secret
JWT_SECRET=godfather_jwt_secret_change_in_production_2024

# Backend API URL (for frontend)
NEXT_PUBLIC_API_URL=http://localhost:5000

# Public URLs (both custom domain and RunPod fallback)
# Primary: Custom domain (requires DNS setup)
PUBLIC_URL=https://admin.ais-asu.com
DOMAIN=admin.ais-asu.com

# Fallback: RunPod proxy URL (works without DNS)
RUNPOD_PROXY_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net/
EOF

echo "✅ .env file created successfully!"
echo ""
echo "📁 File location: $(pwd)/.env"
echo ""
echo "🔍 Verifying required variables..."
source .env
if [ -n "$MONGODB_URI" ]; then
    echo "✅ MONGODB_URI is set"
else
    echo "❌ MONGODB_URI is missing!"
fi

if [ -n "$CLERK_SECRET_KEY" ]; then
    echo "✅ CLERK_SECRET_KEY is set"
else
    echo "❌ CLERK_SECRET_KEY is missing!"
fi

if [ -n "$RUNPOD_API_KEY" ]; then
    echo "✅ RUNPOD_API_KEY is set"
else
    echo "❌ RUNPOD_API_KEY is missing!"
fi

echo ""
echo "Now you can run: ./deploy-direct.sh"
