#!/bin/bash
# Pre-start script for docker-compose
# Generates frontend/.env.local from root .env before starting containers

set -e

echo "🔄 Preparing environment for Docker Compose..."

# Load BACKEND_URL from .env
if [ -f .env ]; then
    source .env
fi

# Set default if not provided
BACKEND_URL=${BACKEND_URL:-http://localhost}

# Generate frontend/.env.local
echo "📝 Generating frontend/.env.local from BACKEND_URL..."
cat > frontend/.env.local << EOF
# Auto-generated from BACKEND_URL in root .env for Docker Compose
# DO NOT EDIT MANUALLY - This file is regenerated on docker-compose up

NEXT_PUBLIC_BACKEND_URL=${BACKEND_URL}
NEXT_PUBLIC_APP_URL=${BACKEND_URL}
NEXT_PUBLIC_API_URL=${BACKEND_URL}/api

# Clerk Configuration
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
CLERK_SECRET_KEY=${CLERK_SECRET_KEY}
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
EOF

echo "✅ Frontend .env.local created with BACKEND_URL: ${BACKEND_URL}"
echo ""
echo "Starting Docker Compose..."
echo ""

# Start docker compose
docker-compose "$@"
