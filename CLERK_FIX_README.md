# 🔧 Clerk Redirect Fix - Quick Guide

## Problem
The app was redirecting to internal IP `http://100.65.19.4/` instead of staying on the RunPod proxy URL, causing connection timeouts.

## What We Fixed

### 1. **Environment Variables** (`.env.local`)
Added Clerk-specific URLs to tell it to use the RunPod proxy:
```bash
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
NEXT_PUBLIC_APP_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net
```

### 2. **Middleware** (`middleware.ts`)
- Added sign-in/sign-up routes to public routes
- Configured Clerk with proper settings

### 3. **Next.js Config** (`next.config.ts`)
- Disabled API rewrites in production (nginx handles routing)
- Added security headers

### 4. **Nginx Config** (`nginx.direct.conf`)
- Changed `X-Forwarded-Proto` from `$scheme` to `https` (forces HTTPS)
- This ensures Clerk generates HTTPS URLs instead of HTTP

## 🚀 Deployment Instructions

### Option A: Automated Deployment (Recommended)

1. **First, commit and push your changes:**
   ```bash
   git add .
   git commit -m "Fix Clerk redirect issue for RunPod proxy"
   git push
   ```

2. **SSH into your RunPod instance:**
   ```bash
   ssh root@ssh.8bzhwve1ri5cw2-80.proxy.runpod.net
   ```

3. **Pull the changes:**
   ```bash
   cd ~/godfather
   git pull
   ```

4. **Run the fix script:**
   ```bash
   ./fix-clerk-redirect.sh
   ```

### Option B: Manual Deployment

If the script fails, follow these steps manually:

```bash
# 1. SSH into RunPod
ssh root@ssh.8bzhwve1ri5cw2-80.proxy.runpod.net

# 2. Pull changes
cd ~/godfather
git pull

# 3. Stop services
pm2 stop all

# 4. Update nginx
sudo cp nginx/nginx.direct.conf /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl reload nginx

# 5. Rebuild frontend
cd frontend
npm install
npm run build

# 6. Restart services
cd ..
pm2 restart all

# 7. Check status
pm2 list
./check-status.sh
```

## ⚙️ Update Clerk Dashboard (IMPORTANT!)

**You MUST do this or the fix won't work:**

1. Go to https://dashboard.clerk.com
2. Select your application
3. Navigate to **Settings** → **General** → **URLs**
4. Update these fields:
   - **Home URL**: `https://8bzhwve1ri5cw2-80.proxy.runpod.net`
   - **Sign-in URL**: `https://8bzhwve1ri5cw2-80.proxy.runpod.net/sign-in`
   - **Sign-up URL**: `https://8bzhwve1ri5cw2-80.proxy.runpod.net/sign-up`
   - **After sign-in URL**: `/dashboard`
   - **After sign-up URL**: `/dashboard`

5. Under **Allowed Origins**, add:
   - `https://8bzhwve1ri5cw2-80.proxy.runpod.net`

6. Click **Save Changes**

## ✅ Verification

After deployment, test the app:

1. Visit: `https://8bzhwve1ri5cw2-80.proxy.runpod.net/`
2. You should see the homepage without any redirect issues
3. Try accessing `/dashboard` - it should redirect to Clerk sign-in
4. The URL should stay on `8bzhwve1ri5cw2-80.proxy.runpod.net` domain

## 🐛 Troubleshooting

### Still redirecting to internal IP?

```bash
# 1. Check if .env.local has the new variables
cd ~/godfather/frontend
cat .env.local | grep NEXT_PUBLIC_APP_URL

# 2. Rebuild frontend (important!)
npm run build

# 3. Restart PM2
pm2 restart frontend

# 4. Check PM2 logs
pm2 logs frontend --lines 50
```

### Nginx errors?

```bash
# Test config
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

### Frontend not building?

```bash
cd ~/godfather/frontend
rm -rf .next
npm install
npm run build
```

## 📊 Files Modified

- ✅ `frontend/.env.local` - Added Clerk URL config
- ✅ `frontend/middleware.ts` - Updated Clerk middleware
- ✅ `frontend/next.config.ts` - Fixed rewrites for production
- ✅ `nginx/nginx.direct.conf` - Force HTTPS scheme
- ✅ `fix-clerk-redirect.sh` - Automated deployment script

## 🎯 Expected Behavior

**Before Fix:**
```
https://8bzhwve1ri5cw2-80.proxy.runpod.net/
  ↓
Redirect to: http://100.65.19.4/?__clerk_handshake=...
  ↓
ERR_CONNECTION_TIMED_OUT ❌
```

**After Fix:**
```
https://8bzhwve1ri5cw2-80.proxy.runpod.net/
  ↓
Loads homepage ✅
  ↓
Click dashboard → Clerk auth (stays on proxy URL) ✅
```

## 📞 Need Help?

Check logs in real-time:
```bash
pm2 logs
```

Run health check:
```bash
./check-status.sh
```

View nginx status:
```bash
sudo systemctl status nginx
curl -I http://localhost:80/
```
