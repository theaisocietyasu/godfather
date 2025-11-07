# 🚀 RunPod Deployment Guide

## Prerequisites
- RunPod CPU instance running
- Git installed
- Your API keys ready (RunPod, Clerk, Discord)

## Step 1: Get Your RunPod Public URL

Your RunPod instance will have a public URL. To find it:

1. Go to your RunPod dashboard
2. Click on your instance
3. Look for "Connect" or "HTTP Service" 
4. The URL will look like: `https://xxxxx-3000.proxy.runpod.net` or an IP address

**Note the port exposure:**
- Port 80 needs to be exposed for HTTP traffic
- RunPod might assign it to a different external port (like 3000 or 8080)

## Step 2: Configure Environment Variables

Edit `.env.production` in your RunPod instance:

```bash
cd /godfather
nano .env.production
```

Replace these values:

```bash
# MongoDB (keep as is)
MONGODB_URI=mongodb://admin:password@mongodb:27017/godfather?authSource=admin

# Get from https://runpod.io/console/user/settings
RUNPOD_API_KEY=your_actual_runpod_api_key

# Get from https://dashboard.clerk.com/
CLERK_SECRET_KEY=sk_live_xxxxx
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxx

# Get from Discord Developer Portal
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_discord_server_id

# Replace with YOUR RunPod URL
PUBLIC_URL=https://your-instance-id.proxy.runpod.net
NEXT_PUBLIC_API_URL=https://your-instance-id.proxy.runpod.net/api
```

Save and exit (Ctrl+X, then Y, then Enter)

## Step 3: Deploy

Run the deployment script:

```bash
cd /godfather
chmod +x deploy-runpod.sh
./deploy-runpod.sh
```

This will:
- Install Docker and Docker Compose if needed
- Load environment variables
- Build and start all services
- Show you the deployment status

## Step 4: Verify Deployment

Check if services are running:

```bash
docker compose -f docker-compose.prod.yml ps
```

You should see 4 containers running:
- `godfather_mongo` - Database
- `godfather_backend` - Python Flask API
- `godfather_frontend` - Next.js app
- `godfather_nginx` - Web server

## Step 5: Access Your Application

Open your browser and go to your RunPod URL:
```
https://your-instance-id.proxy.runpod.net
```

## Troubleshooting

### View Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f backend
```

### Restart Services
```bash
docker compose -f docker-compose.prod.yml restart
```

### Rebuild After Code Changes
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### Stop Everything
```bash
docker compose -f docker-compose.prod.yml down
```

### Complete Reset (removes data!)
```bash
docker compose -f docker-compose.prod.yml down -v
```

## Port Configuration

If RunPod exposes a different port (e.g., 3000 instead of 80):

1. Update `docker-compose.prod.yml`:
```yaml
nginx:
  ports:
    - "3000:80"  # Change first port to match RunPod's exposed port
```

2. Rebuild:
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## CLI Configuration

For users to connect via the Godfather CLI:

```bash
export GODFATHER_API_URL=https://your-instance-id.proxy.runpod.net/api
godfather connect
```

## Security Notes

1. **Change MongoDB Password**: Edit `docker-compose.prod.yml` and update the MongoDB password
2. **Keep .env.production Secret**: Never commit this file to git
3. **Use HTTPS**: RunPod provides HTTPS by default through their proxy

## Updating the Application

1. Pull latest code:
```bash
cd /godfather
git pull
```

2. Rebuild and restart:
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## Monitoring

Check resource usage:
```bash
docker stats
```

Check disk space:
```bash
df -h
```

## Support

If you encounter issues:
1. Check logs: `docker compose -f docker-compose.prod.yml logs`
2. Verify environment variables: `cat .env.production`
3. Check if ports are accessible: `curl http://localhost/health`
