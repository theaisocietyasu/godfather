# 🔧 Environment Configuration Guide

## Single Source of Truth: `BACKEND_URL`

Just change **one variable** in `.env` to switch environments:

```bash
# .env (root directory)
BACKEND_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net  # RunPod
# OR
BACKEND_URL=https://admin.ais-asu.com                    # Custom domain
```

## How It Works

### 📂 Root `.env` (for backend & deployment)
```bash
BACKEND_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net
```

### 📂 `frontend/.env.local` (for frontend)
```bash
NEXT_PUBLIC_BACKEND_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net
```

**Just keep these two in sync manually** - that's it!

---

## 🚀 Deployment

### Local Development (Docker)
```bash
docker-compose up
```
- Uses `docker-compose.yml`
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

### RunPod Production (Direct)
```bash
./deploy-direct.sh
```
- Reads `BACKEND_URL` from `.env`
- Auto-generates `frontend/.env.local` with all derived URLs
- No manual sync needed on RunPod!

---

## 🔄 Switching Environments

### To RunPod Proxy:
```bash
# In .env
BACKEND_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net

# In frontend/.env.local
NEXT_PUBLIC_BACKEND_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net
```

### To Custom Domain:
```bash
# In .env
BACKEND_URL=https://admin.ais-asu.com

# In frontend/.env.local
NEXT_PUBLIC_BACKEND_URL=https://admin.ais-asu.com
```

---

## 🛠️ CLI Auto-Detection

The CLI automatically detects the backend URL from:
1. `GODFATHER_API_URL` env var
2. `BACKEND_URL` env var
3. `NEXT_PUBLIC_BACKEND_URL` env var
4. Fallback: `https://8bzhwve1ri5cw2-80.proxy.runpod.net`

So just export in your shell:
```bash
# Fish
set -Ux BACKEND_URL https://8bzhwve1ri5cw2-80.proxy.runpod.net

# Bash/Zsh
export BACKEND_URL=https://8bzhwve1ri5cw2-80.proxy.runpod.net
```

---

## 📋 Summary

**What you need to change when switching URLs:**
1. `.env` → `BACKEND_URL`
2. `frontend/.env.local` → `NEXT_PUBLIC_BACKEND_URL`

**What happens automatically:**
- ✅ `deploy-direct.sh` generates frontend env with all derived URLs
- ✅ CLI auto-detects from env vars
- ✅ Nginx uses the URL from env
- ✅ Clerk URLs are auto-configured

**No sync scripts needed!** 🎉
