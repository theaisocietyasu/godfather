#!/bin/bash
# Check Clerk environment variables configuration

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           Clerk Environment Variables Check                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "🔍 Checking root .env file..."
if [ -f .env ]; then
    echo "✅ .env exists"
    
    if grep -q "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" .env; then
        CLERK_KEY=$(grep "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" .env | cut -d '=' -f2)
        if [ -n "$CLERK_KEY" ]; then
            echo "✅ NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is set (${CLERK_KEY:0:10}...)"
        else
            echo "❌ NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is empty"
        fi
    else
        echo "❌ NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY not found"
    fi
    
    if grep -q "CLERK_SECRET_KEY" .env; then
        SECRET_KEY=$(grep "CLERK_SECRET_KEY" .env | cut -d '=' -f2)
        if [ -n "$SECRET_KEY" ]; then
            echo "✅ CLERK_SECRET_KEY is set (${SECRET_KEY:0:10}...)"
        else
            echo "❌ CLERK_SECRET_KEY is empty"
        fi
    else
        echo "❌ CLERK_SECRET_KEY not found"
    fi
else
    echo "❌ .env file not found"
fi

echo ""
echo "🔍 Checking frontend/.env.local..."
if [ -f frontend/.env.local ]; then
    echo "✅ frontend/.env.local exists"
    
    if grep -q "CLERK_TRUST_HOST" frontend/.env.local; then
        TRUST_HOST=$(grep "CLERK_TRUST_HOST" frontend/.env.local | cut -d '=' -f2)
        echo "✅ CLERK_TRUST_HOST is set to: $TRUST_HOST"
    else
        echo "❌ CLERK_TRUST_HOST not found - THIS IS THE PROBLEM!"
        echo "   You need to redeploy with ./deploy-direct.sh"
    fi
    
    if grep -q "NODE_ENV" frontend/.env.local; then
        NODE_ENV_VAL=$(grep "NODE_ENV" frontend/.env.local | cut -d '=' -f2)
        echo "✅ NODE_ENV is set to: $NODE_ENV_VAL"
    else
        echo "⚠️  NODE_ENV not found in .env.local"
    fi
    
    echo ""
    echo "📄 Full frontend/.env.local contents:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat frontend/.env.local
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ frontend/.env.local NOT FOUND"
    echo "   This means the deploy script hasn't run yet!"
    echo "   Run: ./deploy-direct.sh"
fi

echo ""
echo "🔍 Checking if PM2 is running frontend with correct env..."
if command -v pm2 &> /dev/null; then
    echo "PM2 frontend process info:"
    pm2 describe frontend 2>/dev/null || echo "❌ Frontend not running in PM2"
else
    echo "⚠️  PM2 not installed or not in PATH"
fi

echo ""
echo "📋 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ ! -f frontend/.env.local ] || ! grep -q "CLERK_TRUST_HOST=true" frontend/.env.local 2>/dev/null; then
    echo "❌ You need to redeploy:"
    echo "   1. Run: ./deploy-direct.sh"
    echo "   2. Clear browser cache/cookies"
    echo "   3. Try signing in again"
else
    echo "✅ Environment looks good!"
    echo "   If you're still having issues:"
    echo "   1. Clear browser cache and cookies for the site"
    echo "   2. Check Clerk Dashboard has correct domain configured"
    echo "   3. Check PM2 logs: pm2 logs frontend"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
