# Fixing Clerk Redirect Loop Issue

## Problem
When signing in/up with Discord on the deployed portal, you're experiencing an infinite redirect loop with URLs like:
```
https://100.65.19.4/sign-in?redirect_url=...&__clerk_hs_reason=dev-browser-missing
```

This happens because Clerk's **development instance** is being used in a deployed environment (not localhost).

## Root Cause
The issue is caused by:
1. ❌ Using Clerk's dev instance on a non-localhost domain
2. ❌ Missing `CLERK_TRUST_HOST=true` environment variable
3. ❌ `NODE_ENV` set to `production` instead of `development`

## Solution

### Strategy: Use Development Mode Everywhere
We're using Clerk's **dev instance** everywhere (local + deployed). This requires:
- ✅ `NODE_ENV=development` 
- ✅ `CLERK_TRUST_HOST=true` (to allow dev instance on non-localhost domains)

### Step 1: Update Your Deployment

I've already updated the following files to use `NODE_ENV=development` everywhere:
- ✅ `deploy-direct.sh` - Sets `NODE_ENV=development` and `CLERK_TRUST_HOST=true`
- ✅ `ecosystem.config.js` - PM2 config uses `NODE_ENV=development`
- ✅ `docker-compose.yml` - Local dev uses `NODE_ENV=development`
- ✅ `docker-compose.prod.yml` - Production deployment uses `NODE_ENV=development`
- ✅ `frontend/middleware.ts` - Simplified Clerk middleware configuration
- ✅ `frontend/app/layout.tsx` - Proper ClerkProvider setup

### Step 2: Configure Clerk Dashboard (Optional but Recommended)

Since you're using Clerk's dev instance, you don't *need* to configure production domains, but it's still good practice:

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
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...  # Note: pk_test_ for dev instance
CLERK_SECRET_KEY=sk_test_...                    # Note: sk_test_ for dev instance

# Your backend URL (whatever your actual deployment URL is)
BACKEND_URL=https://100.65.19.4
# OR
BACKEND_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net
# OR
BACKEND_URL=https://admin.ais-asu.com
```

**Note:** Dev instance keys start with `pk_test_` and `sk_test_`. Production keys start with `pk_live_` and `sk_live_`.

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

### Using Clerk Dev Instance Everywhere
We're using Clerk's **development instance** in all environments:
- ✅ Local development (localhost)
- ✅ Deployed VM (IP address or domain)

**Benefits:**
- ✅ Free tier
- ✅ Same auth across all environments
- ✅ Simplified configuration

**Limitations:**
- ⚠️ Rate limits (100 MAUs for free)
- ⚠️ Dev instance not meant for high-traffic production
- ⚠️ Some advanced features require production instance

**When to upgrade to production instance:**
- When you have real users (not just testing)
- When you need more than 100 monthly active users
- When you need production-level SLAs

### Environment Configuration
All environments now use:
```bash
NODE_ENV=development       # Tell Next.js and Clerk we're in dev mode
CLERK_TRUST_HOST=true     # Allow dev instance on non-localhost
```

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
