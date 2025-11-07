# 🌐 Dual URL Setup - Custom Domain + RunPod Fallback

## Overview

Your Godfather application is configured to work with **TWO URLs simultaneously**:

1. **Primary (Custom Domain)**: `https://admin.ais-asu.com`
   - Professional branded URL
   - Requires DNS setup in GoDaddy
   - Better for users (easy to remember)

2. **Fallback (RunPod Proxy)**: `https://xxxxx-80.proxy.runpod.net`
   - Works immediately without DNS
   - Provided automatically by RunPod
   - Backup if DNS has issues

## How It Works

### Nginx Configuration

The nginx server is configured to accept requests from **any hostname**:

```nginx
server_name _ admin.ais-asu.com *.proxy.runpod.net;
```

This means:
- `_` = Accept any hostname (wildcard)
- `admin.ais-asu.com` = Your custom domain
- `*.proxy.runpod.net` = Any RunPod proxy subdomain

### Result

Both URLs point to the **same application**:
- ✅ `https://admin.ais-asu.com` → Your application
- ✅ `https://12345-80.proxy.runpod.net` → Same application
- ✅ Both work simultaneously!

---

## Setup Instructions

### Step 1: Find Your RunPod Proxy URL

1. Go to https://runpod.io/console/pods
2. Click on your running pod
3. Go to **"Connect"** tab
4. Look for **"HTTP Service"** or **"TCP Port Mappings"**
5. You'll see something like: `https://xxxxx-80.proxy.runpod.net`

### Step 2: Update `.env`

Edit your `.env` file:

```bash
cd /godfather
nano .env
```

Add your RunPod proxy URL:

```bash
RUNPOD_PROXY_URL=https://12345-80.proxy.runpod.net
```

### Step 3: Deploy

The application is already configured to accept both URLs!

```bash
cd /godfather
docker compose -f docker-compose.prod.yml up -d
```

### Step 4: Test Both URLs

**Test custom domain:**
```bash
curl https://admin.ais-asu.com/health
```

**Test RunPod fallback:**
```bash
curl https://your-id-80.proxy.runpod.net/health
```

Both should return: `healthy`

---

## Usage Scenarios

### For End Users (Recommended)

Give them the **custom domain**:
```
https://admin.ais-asu.com
```

**Why?**
- Professional
- Easy to remember
- Branded with your organization

### For Testing/Backup

Use the **RunPod proxy URL**:
```
https://xxxxx-80.proxy.runpod.net
```

**Why?**
- Works immediately (no DNS wait)
- Backup if DNS fails
- Quick testing before DNS propagates

### For CLI Users

CLI can use either URL:

```bash
# Option 1: Custom domain (recommended)
export GODFATHER_API_URL=https://admin.ais-asu.com/api
godfather connect

# Option 2: RunPod fallback
export GODFATHER_API_URL=https://xxxxx-80.proxy.runpod.net/api
godfather connect
```

---

## Benefits of Dual URL Setup

### ✅ **Immediate Access**
- RunPod URL works instantly while DNS propagates
- No downtime during DNS setup

### ✅ **Redundancy**
- If custom domain DNS fails, RunPod URL still works
- Multiple access points

### ✅ **Flexibility**
- Share custom domain publicly
- Use RunPod URL for internal testing
- Switch between URLs as needed

### ✅ **No Configuration Needed**
- Both URLs automatically routed by nginx
- Same SSL certificate works for both (RunPod provides SSL)
- Zero additional setup

---

## Authentication & Security

### Clerk OAuth

You should add **BOTH** URLs to your Clerk configuration:

1. Go to https://dashboard.clerk.com/
2. Navigate to your app → **Paths**
3. Add to **"Allowed Redirect URLs":**
   - `https://admin.ais-asu.com/*`
   - `https://xxxxx-80.proxy.runpod.net/*`

### Discord OAuth

Add **BOTH** callback URLs:

1. Go to https://discord.com/developers/applications
2. Select your bot → **OAuth2** → **General**
3. Add to **"Redirects":**
   - `https://admin.ais-asu.com/api/auth/callback/discord`
   - `https://xxxxx-80.proxy.runpod.net/api/auth/callback/discord`

---

## How to Share With Users

### Recommended Approach

**Primary:** Share the custom domain
```
🌐 Admin Portal: https://admin.ais-asu.com
```

**In Documentation:** Mention both URLs
```
Primary URL: https://admin.ais-asu.com
Fallback URL: https://xxxxx-80.proxy.runpod.net
(Use fallback if primary is unavailable)
```

### For CLI Setup

Update your README or documentation:

```bash
# Setup CLI
export GODFATHER_API_URL=https://admin.ais-asu.com/api

# Or use fallback if needed
export GODFATHER_API_URL=https://xxxxx-80.proxy.runpod.net/api

# Connect to pods
godfather connect
```

---

## Troubleshooting

### Custom Domain Not Working?

Check DNS:
```bash
nslookup admin.ais-asu.com
```

If not resolving → Use RunPod fallback URL while DNS propagates!

### RunPod URL Not Working?

1. Check if port 80 is exposed in RunPod dashboard
2. Verify the URL in RunPod "Connect" tab
3. Make sure pod is running: `docker compose ps`

### Both URLs Not Working?

Check nginx logs:
```bash
docker compose -f docker-compose.prod.yml logs nginx
```

---

## SSL/HTTPS Configuration

### RunPod Proxy (No Setup Needed!)

RunPod automatically provides HTTPS for their proxy URLs:
- `https://xxxxx-80.proxy.runpod.net` ✅ Already has SSL
- RunPod manages the certificate
- Zero configuration required!

### Custom Domain (Requires SSL Setup)

For your custom domain, you need to set up SSL:

```bash
cd /godfather
chmod +x setup-ssl.sh
sudo ./setup-ssl.sh
```

This gets a free Let's Encrypt certificate for `admin.ais-asu.com`.

**Result:**
- Custom domain: Uses your Let's Encrypt cert
- RunPod URL: Uses RunPod's cert
- Both work with HTTPS! 🔒

---

## Quick Reference

| Aspect | Custom Domain | RunPod Proxy |
|--------|---------------|--------------|
| URL | `https://admin.ais-asu.com` | `https://xxxxx-80.proxy.runpod.net` |
| Setup Required | Yes (DNS + SSL) | No (automatic) |
| Works Immediately | No (DNS delay) | Yes |
| Professional | ✅ Very | ❌ Technical |
| SSL Certificate | Let's Encrypt | RunPod managed |
| Best For | Public users | Testing/backup |

---

## Port Exposure

Make sure these ports are exposed in your RunPod pod settings:

- **Port 80** (HTTP) → Gets RunPod proxy URL
- **Port 443** (HTTPS) → Optional, for direct HTTPS

The proxy URLs automatically handle HTTPS through RunPod's infrastructure!

---

## Example: Complete User Journey

### Scenario 1: User with Custom Domain
```
1. User visits https://admin.ais-asu.com
2. DNS resolves to your RunPod IP
3. Nginx accepts request (server_name matches)
4. User logs in with Discord OAuth
5. Creates and manages pods
✅ Perfect!
```

### Scenario 2: User with RunPod URL (Fallback)
```
1. User visits https://12345-80.proxy.runpod.net
2. RunPod proxy routes to your pod
3. Nginx accepts request (server_name matches)
4. User logs in with Discord OAuth
5. Creates and manages pods
✅ Also perfect!
```

### Scenario 3: DNS Propagating
```
1. Custom domain not working yet (DNS delay)
2. Share RunPod URL with user temporarily
3. User can access immediately
4. Once DNS propagates, switch to custom domain
✅ No downtime!
```

---

## Summary

🎯 **You now have TWO working URLs with ONE deployment:**

1. **Primary**: `https://admin.ais-asu.com`
   - Professional, branded, memorable
   - Requires DNS + SSL setup

2. **Fallback**: `https://xxxxx-80.proxy.runpod.net`
   - Automatic, instant, no setup
   - Backup access point

Both URLs:
- Work simultaneously
- Point to same application
- Support full authentication
- Require no additional configuration in nginx (already set up!)

Share the custom domain publicly, keep the RunPod URL as a backup! 🚀
