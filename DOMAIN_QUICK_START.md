# 🎯 Quick Domain Setup - Copy & Paste Guide

## Step 1: Configure DNS in GoDaddy (Do this FIRST!)

1. **Go to GoDaddy:** https://dcc.godaddy.com/domains/
2. **Find ais-asu.com** → Click "DNS"
3. **Click "Add New Record"**
4. **Fill in:**
   ```
   Type: A
   Name: admin
   Value: [Paste your RunPod IP here - see below]
   TTL: 600 (default is fine)
   ```
5. **Click Save**

### 🔍 How to Find Your RunPod IP:

In your RunPod instance terminal:
```bash
curl ifconfig.me
```

OR find it in RunPod dashboard under "Connect" tab.

### ⏰ Wait Time: 
DNS takes **5-60 minutes** to propagate. Go grab coffee! ☕

---

## Step 2: Update Godfather Configuration

In your RunPod instance:

```bash
cd /godfather
nano .env
```

**Change these lines:**
```bash
PUBLIC_URL=https://admin.ais-asu.com
NEXT_PUBLIC_API_URL=https://admin.ais-asu.com/api
DOMAIN=admin.ais-asu.com
```

**Save:** `Ctrl+X` → `Y` → `Enter`

---

## Step 3: Get SSL Certificate (HTTPS)

```bash
cd /godfather
chmod +x setup-ssl.sh
sudo ./setup-ssl.sh
```

**You'll be asked for:**
- Your email (for certificate expiry notifications)
- Confirmation to proceed

**The script will:**
- Install certbot
- Get free SSL certificate from Let's Encrypt
- Configure nginx for HTTPS
- Restart services
- Set up auto-renewal

---

## Step 4: Update Clerk Dashboard

1. **Go to:** https://dashboard.clerk.com/
2. **Select your app** → **Paths**
3. **Add to "Allowed Redirect URLs":**
   - `https://admin.ais-asu.com/*`
4. **Save**

---

## Step 5: Update Discord OAuth

1. **Go to:** https://discord.com/developers/applications
2. **Select your bot**
3. **OAuth2** → **General**
4. **Add to "Redirects":**
   - `https://admin.ais-asu.com/api/auth/callback/discord`
5. **Save**

---

## ✅ Verification

Test your setup:

```bash
# Check DNS resolves
nslookup admin.ais-asu.com

# Check HTTPS works
curl https://admin.ais-asu.com/health

# View logs
docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml logs -f
```

Visit in browser: **https://admin.ais-asu.com**

---

## 🚨 Troubleshooting

### DNS not working?
```bash
# Check if DNS has propagated
dig admin.ais-asu.com

# Should show your RunPod IP
# If not, wait longer (up to 1 hour)
```

### SSL certificate failed?
**Most common reason:** DNS not propagated yet!

Wait 30-60 minutes after adding DNS record, then run `setup-ssl.sh` again.

### Port 80 blocked?
Check RunPod pod settings - make sure port 80 is exposed!

### Services won't start?
```bash
# Check what's wrong
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs

# Restart everything
docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml restart
```

---

## 📋 Final Checklist

- [ ] DNS record added in GoDaddy (admin.ais-asu.com → your RunPod IP)
- [ ] DNS propagated (test with `nslookup admin.ais-asu.com`)
- [ ] `.env` updated with domain
- [ ] SSL certificate obtained (ran `setup-ssl.sh`)
- [ ] Clerk redirect URLs updated
- [ ] Discord OAuth redirect URLs updated
- [ ] Website accessible at `https://admin.ais-asu.com`
- [ ] Login works with Discord OAuth
- [ ] CLI works: `GODFATHER_API_URL=https://admin.ais-asu.com/api godfather connect`

---

## 🎉 You're Done!

Your Godfather admin panel is now live at:
### **https://admin.ais-asu.com**

Users can connect via CLI:
```bash
export GODFATHER_API_URL=https://admin.ais-asu.com/api
godfather connect
```

---

## 📞 Need Help?

**DNS Issues:** https://www.whatsmydns.net/ (check propagation)
**SSL Issues:** Run `sudo certbot certificates` to check status
**Service Issues:** `docker compose -f docker-compose.prod.yml logs`
