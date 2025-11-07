# 🌐 Custom Domain Setup Guide
## Setting up admin.ais-asu.com for Godfather

---

## Part 1: GoDaddy DNS Configuration

### Step 1: Log into GoDaddy
1. Go to https://godaddy.com
2. Sign in to your account
3. Go to "My Products" → Find "ais-asu.com"
4. Click "DNS" or "Manage DNS"

### Step 2: Add DNS Record

You'll add an **A Record** or **CNAME Record** depending on your RunPod setup:

#### **Option A: If you have a static IP (recommended)**

1. Click "Add" or "Add Record"
2. Select **Type: A**
3. Fill in:
   - **Name/Host:** `admin` (or `pods` if you prefer)
   - **Value/Points to:** Your RunPod instance IP address
   - **TTL:** 600 seconds (or leave default)
4. Click "Save"

**Finding your RunPod IP:**
```bash
# In your RunPod instance, run:
curl ifconfig.me
```

#### **Option B: If you have a RunPod proxy URL**

1. Click "Add" or "Add Record"
2. Select **Type: CNAME**
3. Fill in:
   - **Name/Host:** `admin` (or `pods`)
   - **Value/Points to:** `xxxxx-80.proxy.runpod.net` (your RunPod URL without https://)
   - **TTL:** 600 seconds
4. Click "Save"

### Step 3: Verify DNS Propagation

DNS changes can take 5-60 minutes to propagate. Check status:

```bash
# On your local machine or RunPod instance:
nslookup admin.ais-asu.com
# or
dig admin.ais-asu.com
```

You should see it pointing to your RunPod IP/URL.

---

## Part 2: Configure Godfather Application

### Step 1: Update Environment Variables

Edit `.env.production` in your RunPod instance:

```bash
cd /godfather
nano .env.production
```

Update these lines:
```bash
# Replace with your custom domain
PUBLIC_URL=https://admin.ais-asu.com
NEXT_PUBLIC_API_URL=https://admin.ais-asu.com/api
DOMAIN=admin.ais-asu.com
```

Save (Ctrl+X, Y, Enter)

### Step 2: Update Nginx Configuration

The nginx configuration will automatically use your domain. No changes needed if you're using the production config!

### Step 3: Redeploy Application

```bash
cd /godfather
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up --build -d
```

---

## Part 3: SSL Certificate Setup

You have two options for HTTPS:

### **Option A: Let's Encrypt (Free, Recommended)**

Install Certbot in your RunPod instance:

```bash
# Install certbot
apt-get update
apt-get install -y certbot python3-certbot-nginx

# Stop nginx temporarily
docker compose -f docker-compose.prod.yml stop nginx

# Get certificate
certbot certonly --standalone \
  -d admin.ais-asu.com \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive

# Copy certificates
mkdir -p /godfather/nginx/ssl
cp /etc/letsencrypt/live/admin.ais-asu.com/fullchain.pem /godfather/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/admin.ais-asu.com/privkey.pem /godfather/nginx/ssl/key.pem

# Restart with HTTPS config
docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml up -d
```

### **Option B: Use RunPod's Proxy (Easier)**

If your RunPod URL already has HTTPS (like `https://xxxxx.proxy.runpod.net`), you can:

1. Keep using the RunPod proxy with HTTPS
2. Use CNAME to point your domain to it
3. Users access via `https://admin.ais-asu.com` but it proxies through RunPod's SSL

---

## Part 4: Update Clerk Redirect URLs

### Important: Update Clerk Dashboard

1. Go to https://dashboard.clerk.com/
2. Select your application
3. Go to "Authentication" → "Social Connections" → "Discord"
4. Update **Redirect URIs:**
   - Add: `https://admin.ais-asu.com`
   - Add: `https://admin.ais-asu.com/api/auth/callback/discord`
5. Go to "Paths" settings
6. Update **Allowed Redirect URLs:**
   - Add: `https://admin.ais-asu.com/*`
7. Save changes

---

## Part 5: Update Discord OAuth

### Update Discord Application

1. Go to https://discord.com/developers/applications
2. Select your bot application
3. Go to "OAuth2" → "General"
4. Update **Redirects:**
   - Add: `https://admin.ais-asu.com/api/auth/callback/discord`
5. Save changes

---

## Verification Checklist

After setup, verify everything works:

- [ ] DNS resolves: `nslookup admin.ais-asu.com` shows correct IP
- [ ] HTTP works: Visit `http://admin.ais-asu.com`
- [ ] HTTPS works: Visit `https://admin.ais-asu.com` (if SSL configured)
- [ ] Login works: Discord authentication redirects properly
- [ ] API works: Check browser console for API calls
- [ ] CLI works: `GODFATHER_API_URL=https://admin.ais-asu.com/api godfather connect`

---

## Troubleshooting

### DNS not resolving
```bash
# Check DNS
dig admin.ais-asu.com

# Wait up to 1 hour for propagation
# Clear your DNS cache (on your computer):
# Mac: sudo dscacheutil -flushcache
# Linux: sudo systemd-resolve --flush-caches
# Windows: ipconfig /flushdns
```

### SSL Certificate Issues
```bash
# Check certificate expiry
openssl x509 -in /godfather/nginx/ssl/cert.pem -noout -dates

# Renew Let's Encrypt certificate
certbot renew
```

### Clerk Authentication Fails
- Make sure you added the domain to Clerk's allowed redirect URLs
- Check browser console for CORS errors
- Verify environment variables are loaded

### Can't Access Application
```bash
# Check nginx logs
docker compose -f docker-compose.prod.yml logs nginx

# Check if port 80/443 are exposed
# In RunPod dashboard, verify port mappings

# Test locally first
curl http://localhost/health
```

---

## Port Configuration for RunPod

RunPod requires you to expose ports. In your RunPod pod settings:

1. **Expose Port 80** (HTTP)
2. **Expose Port 443** (HTTPS, if using SSL)

RunPod will give you:
- `xxxxx-80.proxy.runpod.net` for port 80
- `xxxxx-443.proxy.runpod.net` for port 443

Your domain will point to these!

---

## Quick Reference

| Service | URL |
|---------|-----|
| Main App | `https://admin.ais-asu.com` |
| API | `https://admin.ais-asu.com/api` |
| Health Check | `https://admin.ais-asu.com/health` |
| CLI API URL | `https://admin.ais-asu.com/api` |

---

## DNS Record Summary

What you're creating in GoDaddy:

```
Type: A (or CNAME)
Name: admin
Value: [Your RunPod IP or xxxxx-80.proxy.runpod.net]
TTL: 600

Result: admin.ais-asu.com → Your RunPod Instance
```

---

## Need Help?

Common issues:
1. **"Site can't be reached"** → DNS not propagated yet, wait 30-60 minutes
2. **"Connection refused"** → Port 80 not exposed in RunPod
3. **"SSL handshake failed"** → Certificate not configured correctly
4. **"Authentication error"** → Update Clerk redirect URLs
5. **"CORS error"** → Check nginx CORS headers in logs

Run diagnostics:
```bash
# In RunPod instance
cd /godfather
docker compose -f docker-compose.prod.yml ps  # Check services
docker compose -f docker-compose.prod.yml logs -f  # View logs
curl http://localhost/health  # Test locally
```
