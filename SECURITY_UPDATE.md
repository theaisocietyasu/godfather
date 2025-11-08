# Critical Security Update - User Isolation

## 🔒 Security Issue Fixed

**Problem:** Non-admin users connecting via CLI had full root access with sudo privileges, allowing them to execute any system command and potentially compromise the entire pod.

**Solution:** Implemented proper user isolation at the system level.

## ✅ What Changed

### For Non-Admin Users (Regular Members):
- **Before:** Connected as `root` user with full sudo access ❌
- **After:** Connected as restricted user `godfather_<username>` with NO sudo access ✅

### For Admin Users:
- **No Change:** Still connect as `root` with full sudo access ✅

## 🔧 Technical Implementation

### 1. Docker Image Updates (`theaisocietyasu/godfather-base:latest`)
- Creates separate user accounts for non-admin users
- Users named: `godfather_<discord_username>`
- These accounts have **no sudo privileges** at the system level
- File permissions properly isolated per user workspace

### 2. SSH Connection Flow
**Admin Users:**
```bash
SSH → root user → Full system access ✅
```

**Non-Admin Users:**
```bash
SSH → root (initial) → su to godfather_<username> → Restricted access ✅
```

### 3. Workspace Structure
```
/workspace/
├── users/
│   ├── <discord_user_1>/     # Personal workspace (restricted users can only access their own)
│   ├── <discord_user_2>/
│   └── admin_user/           # Admin workspace
└── shared/                    # Collaborative space (all users can access)
```

### 4. Permission Model

**Non-Admin Users Can:**
- ✅ Read/write in their personal workspace: `/workspace/users/<their_username>/`
- ✅ Read/write in shared folder: `/workspace/shared/`
- ✅ Run basic Linux commands (ls, cat, vim, python, etc.)
- ✅ Install user-level packages (pip install --user, npm install, etc.)

**Non-Admin Users CANNOT:**
- ❌ Use sudo or su
- ❌ Access other users' workspaces
- ❌ Access system directories (/root, /etc, etc.)
- ❌ Install system-level packages (apt, yum, etc.)
- ❌ Modify system configuration
- ❌ Change file ownership or permissions outside their workspace

**Admin Users Can:**
- ✅ Everything non-admin users can do
- ✅ Full root access with sudo
- ✅ System administration
- ✅ Access all workspaces
- ✅ Install system packages

## 📋 Deployment Instructions

### For New Pods:
1. Use the updated Docker image: `theaisocietyasu/godfather-base:latest`
2. The security restrictions will apply automatically

### For Existing Pods:
**Option 1: Recreate the pod (Recommended)**
1. Terminate the existing pod
2. Create a new pod with the updated image
3. Security restrictions will apply automatically

**Option 2: Update running pod (Advanced)**
1. SSH into the pod as admin
2. Pull and run the new setup script:
```bash
curl -o /start.sh https://raw.githubusercontent.com/theaisocietyasu/godfather/main/docker-images/godfather-base/setup-ssh.sh
chmod +x /start.sh
pkill -f "tail -f /dev/null"  # Kill old process
/start.sh &  # Start new process
```

## 🧪 Testing the Security

### Test Non-Admin Restrictions:
1. Log in via CLI as a non-admin user
2. Try these commands - they should all fail:
```bash
sudo ls              # Should show: Permission denied
/usr/bin/sudo ls     # Should also fail (not an alias bypass)
su                   # Should fail
cd /root             # Should be restricted
```

### Test Admin Access:
1. Log in via CLI as an admin user
2. All sudo commands should work normally

## 🔐 Security Checklist

- [x] Non-admin users run in separate system accounts
- [x] No sudo access for non-admin users
- [x] File permissions isolated per user
- [x] Admin users maintain full access
- [x] Docker image built and pushed to registry
- [x] Changes committed to repository

## 📝 Notes

- The restriction happens at the **system level**, not just with bash aliases
- Even if a user tries to bypass with `/usr/bin/sudo`, it will fail due to lack of system permissions
- Admin detection is automatic based on Discord role ID
- User workspaces persist across reconnections

## 🚀 Version

- **Docker Image:** `theaisocietyasu/godfather-base:latest`
- **Digest:** `sha256:54dcfa8191ddf0980def50ec735c3060151f494e53c0004bbb9401f617df0073`
- **Updated:** November 8, 2025

---

**Impact:** This is a critical security fix. All existing pods should be recreated with the new image to ensure proper user isolation.
