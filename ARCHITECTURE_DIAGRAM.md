# 🏗️ Domain Setup Architecture

## How Everything Connects

```
┌─────────────────────────────────────────────────────────────┐
│                         INTERNET                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ User visits
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     GoDaddy DNS                             │
│                                                             │
│   ais-asu.com                                              │
│   └── admin.ais-asu.com (A Record)                         │
│       └── Points to: [Your RunPod IP]                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ DNS Resolution
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 RunPod Instance (Your Server)               │
│                                                             │
│   IP: XXX.XXX.XXX.XXX                                      │
│   Port 80 (HTTP) → exposed                                 │
│   Port 443 (HTTPS) → exposed                               │
│                                                             │
│   ┌─────────────────────────────────────────────┐          │
│   │          Nginx (Reverse Proxy)              │          │
│   │                                             │          │
│   │  • Handles SSL/HTTPS                        │          │
│   │  • Routes /api/* → Backend                  │          │
│   │  • Routes /* → Frontend                     │          │
│   └─────────────────────────────────────────────┘          │
│            │                        │                       │
│            ▼                        ▼                       │
│   ┌────────────────┐      ┌────────────────┐              │
│   │   Backend      │      │   Frontend     │              │
│   │   (Flask)      │      │   (Next.js)    │              │
│   │   Port 5000    │      │   Port 3000    │              │
│   └────────────────┘      └────────────────┘              │
│            │                                                │
│            ▼                                                │
│   ┌────────────────┐                                       │
│   │   MongoDB      │                                       │
│   │   Port 27017   │                                       │
│   └────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Backend creates pods
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      RunPod API                             │
│                                                             │
│   Creates GPU pods with:                                    │
│   • Image: theaisocietyasu/godfather-base:latest          │
│   • SSH keys configured                                     │
│   • User isolation enabled                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Pods created
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    User's GPU Pods                          │
│                                                             │
│   Each pod has:                                             │
│   • SSH access (port 22)                                    │
│   • Godfather CLI can connect                               │
│   • User workspaces isolated                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Request Flow Example

### When a user visits https://admin.ais-asu.com:

```
1. Browser → GoDaddy DNS
   "What's the IP for admin.ais-asu.com?"
   
2. GoDaddy DNS → Browser
   "It's XXX.XXX.XXX.XXX"
   
3. Browser → RunPod Instance (XXX.XXX.XXX.XXX:443)
   "GET / (HTTPS request)"
   
4. Nginx → SSL Certificate
   "Decrypt HTTPS, route to frontend"
   
5. Nginx → Frontend (localhost:3000)
   "GET /"
   
6. Frontend → Nginx → Browser
   "Here's the React/Next.js app"
   
7. Browser runs JavaScript → API calls
   "POST /api/pods/create"
   
8. Nginx → Backend (localhost:5000)
   "POST /api/pods/create"
   
9. Backend → RunPod API
   "Create a pod with these specs"
   
10. RunPod API → New Pod Created
    "Pod created at 87.197.146.56:40062"
    
11. Backend → MongoDB
    "Save pod info and SSH keys"
    
12. Backend → Nginx → Browser
    "Pod created successfully!"
```

---

## DNS Record Breakdown

What you create in GoDaddy:

```
┌──────────────────────────────────────────────────────────┐
│ Type: A                                                  │
│ Name: admin                                              │
│ Value: [Your RunPod Instance IP]                         │
│ TTL: 600 seconds (10 minutes)                            │
└──────────────────────────────────────────────────────────┘

Result:
admin.ais-asu.com → Resolves to → Your RunPod IP

Example:
admin.ais-asu.com → 203.0.113.45
```

---

## SSL Certificate Flow

### Let's Encrypt Certificate Setup:

```
1. setup-ssl.sh runs
   └── Stops nginx temporarily
   
2. Certbot (standalone mode)
   └── Listens on port 80
   
3. Let's Encrypt servers
   └── Visit http://admin.ais-asu.com/.well-known/acme-challenge/...
   └── Verify you control the domain
   
4. Certificate issued! 🎉
   └── Saved to: /etc/letsencrypt/live/admin.ais-asu.com/
   
5. Copy certificates to nginx/ssl/
   └── cert.pem (public certificate)
   └── key.pem (private key)
   
6. Nginx starts with HTTPS
   └── Listens on port 443 (HTTPS)
   └── Redirects port 80 (HTTP) → 443
   
7. Auto-renewal cron job
   └── Runs daily at midnight
   └── Renews if expiring within 30 days
```

---

## Authentication Flow (Discord OAuth)

```
1. User clicks "Login with Discord"
   ↓
2. Clerk redirects to Discord
   https://discord.com/oauth2/authorize?client_id=...
   ↓
3. User approves on Discord
   ↓
4. Discord redirects back to Clerk
   https://admin.ais-asu.com/api/auth/callback/discord?code=...
   ↓
5. Clerk exchanges code for Discord token
   ↓
6. Clerk creates session
   ↓
7. User logged in! Backend verifies admin status via Discord API
```

**Important:** All redirect URLs must use `https://admin.ais-asu.com`!

---

## CLI Connection Flow

```
User's Computer                    Your Server
──────────────                     ───────────

$ godfather connect
     │
     ├─→ API: GET /api/pods/public
     │   (with auth token)
     │
     ←── [List of pods]
     │
     ├─→ Select pod
     │
     ├─→ API: POST /api/pods/{id}/connect
     │
     ←── SSH connection info:
     │   • Host: 87.197.146.56
     │   • Port: 40062
     │   • User: root
     │   • Is Admin: true
     │
     ├─→ API: GET /api/ssh-key
     │
     ←── Private SSH key
     │
     ├─→ SSH connection to pod
     │   ssh -i key root@87.197.146.56 -p 40062
     │
     ←── Connected to pod! 🎉
         /workspace/users/yourname$
```

---

## Port Mapping

### Development (localhost):
```
Port 80   → Nginx → Routes to frontend/backend
Port 3000 → Frontend (Next.js dev server)
Port 5000 → Backend (Flask API)
Port 27017 → MongoDB
```

### Production (RunPod):
```
Public Port 80/443 → Nginx (in Docker)
                      ├─→ Frontend (Docker, port 3000)
                      ├─→ Backend (Docker, port 5000)
                      └─→ MongoDB (Docker, port 27017)

All in same Docker network: godfather_network
```

---

## File Structure After Setup

```
/godfather/
├── .env.production                    ← Your config (secrets!)
├── docker-compose.prod.yml            ← Production Docker config
├── docker-compose.ssl.yml             ← HTTPS overlay config
├── setup-ssl.sh                       ← SSL setup script
├── DOMAIN_SETUP_GUIDE.md              ← Detailed guide
├── DOMAIN_QUICK_START.md              ← Quick reference
│
├── nginx/
│   ├── nginx.prod.conf                ← HTTP config
│   ├── nginx.ssl.conf                 ← HTTPS config
│   └── ssl/
│       ├── cert.pem                   ← Public certificate
│       └── key.pem                    ← Private key
│
└── [rest of your application files]
```

---

## Summary

**What happens:**
1. User types `admin.ais-asu.com` in browser
2. DNS lookup → finds your RunPod IP
3. Browser connects to your RunPod instance
4. Nginx handles HTTPS and routes requests
5. Frontend serves the UI
6. Backend manages pods via RunPod API
7. Users can SSH into pods via CLI

**Key files you created:**
- DNS A record in GoDaddy
- `.env.production` with domain config
- SSL certificates in `nginx/ssl/`
- All services running with HTTPS

🎉 **Result:** Professional domain with HTTPS!
