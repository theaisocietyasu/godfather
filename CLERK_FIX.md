# Fixing Clerk Redirect Loop Issue

## Problem
When signing in/up with Discord on the deployed portal, you're experiencing an infinite redirect loop with URLs like:
```
https://100.65.19.4/sign-in?redirect_url=...&__clerk_hs_reason=dev-browser-missing
```

This happens because Clerk detects it's running in production but can't verify the browser session due to missing configuration.

## Root Cause
The issue is caused by:
1. ❌ Clerk thinking it's in development mode when it's actually production
2. ❌ Missing `CLERK_TRUST_HOST=true` environment variable
3. ❌ Incorrect domain configuration in Clerk Dashboard

## Solution

### Step 1: Update Your Deployment

I've already updated the following files:
- ✅ `deploy-direct.sh` - Now sets `CLERK_TRUST_HOST=true`
- ✅ `frontend/middleware.ts` - Simplified Clerk middleware configuration
- ✅ `frontend/app/layout.tsx` - Proper ClerkProvider setup

### Step 2: Configure Clerk Dashboard (CRITICAL)

Go to your Clerk Dashboard and configure the following:

#### 2.1 Add Your Production Domain

1. Go to: **Configure** → **Domains**
2. Add your production domain(s):
   - If using IP address: `100.65.19.4` (not recommended for production)
   - If using RunPod proxy: `8bzhwve1ri5cw2-80.proxy.runpod.net`
   - If using custom domain: `admin.ais-asu.com`

#### 2.2 Update OAuth Callback URLs

1. Go to: **User & Authentication** → **Social Connections** → **Discord**
2. Update the **Authorized redirect URIs** to include:
   ```
   https://100.65.19.4/sign-in
   https://8bzhwve1ri5cw2-80.proxy.runpod.net/sign-in
   https://admin.ais-asu.com/sign-in
   ```

#### 2.3 Update Environment Variables

Make sure your `.env` file includes:
```bash
# In root .env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
CLERK_TRUST_HOST=true

# Your backend URL (whatever your actual production URL is)
BACKEND_URL=https://100.65.19.4
# OR
BACKEND_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net
# OR
BACKEND_URL=https://admin.ais-asu.com
```

### Step 3: Redeploy

Run the deployment script again:
```bash
cd /home/ash/student_orgs/AIS/godfather
./deploy-direct.sh
```

### Step 4: Verify

1. Clear your browser cache and cookies for the site
2. Try signing in with Discord again
3. Check that the redirect URL is clean (no repeating parameters)

## Additional Notes

### Using IP Addresses (Not Recommended)
If you're using `https://100.65.19.4`, be aware that:
- ❌ IP addresses don't work well with OAuth providers
- ❌ SSL certificates typically don't work with IP addresses
- ❌ Clerk may have issues with IP-based domains
- ✅ **Solution**: Use a proper domain name (like `admin.ais-asu.com`)

### Recommended Setup
1. Use your custom domain: `admin.ais-asu.com`
2. Or use the RunPod proxy URL: `8bzhwve1ri5cw2-80.proxy.runpod.net`
3. Configure Clerk to use that domain
4. Update `BACKEND_URL` in `.env` to match

## Debugging

If issues persist, check the following:

### 1. Browser Console
Look for Clerk errors in the browser console (F12)

### 2. Check Environment Variables
In the deployed frontend container:
```bash
pm2 logs frontend
```

### 3. Verify Nginx Headers
Check that nginx is passing the correct headers:
```bash
curl -I http://localhost
```

Should include:
- `X-Forwarded-Proto: https`
- `X-Forwarded-Host: <your-domain>`

### 4. Clerk Middleware Debug
The middleware has been updated to:
- ✅ Trust the host
- ✅ Use proper sign-in/sign-up URLs
- ✅ Disable dev browser checks

## Quick Fix Checklist

- [ ] Add production domain to Clerk Dashboard
- [ ] Update Discord OAuth redirect URIs in Clerk
- [ ] Set `CLERK_TRUST_HOST=true` in environment (✅ already done in deploy script)
- [ ] Use a proper domain name instead of IP address (recommended)
- [ ] Redeploy with `./deploy-direct.sh`
- [ ] Clear browser cache and test
- [ ] Verify no redirect loops

## Support

If you continue to have issues:
1. Check Clerk Dashboard logs
2. Check PM2 logs: `pm2 logs frontend`
3. Check nginx logs: `cat /var/log/nginx/error.log`
4. Verify environment variables are correct in deployed container
