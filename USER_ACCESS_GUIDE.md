# User Access Control Guide

## Overview
The Godfather platform now supports fine-grained access control for pods. Admins can assign specific Discord users to pods, and those users will automatically see and connect to allowed pods via the CLI - no manual SSH setup required!

## Features

### 🔑 Automatic SSH Authentication
- **No Password Required**: SSH keys are automatically generated and managed by the system
- **Seamless Connection**: Users can connect to pods without any manual SSH configuration
- **Secure**: Each organization has a unique SSH key pair stored securely in the database

### 👥 User-Based Access Control
Admins have two options when creating pods:

1. **Public Pods**: All Discord members with valid authentication can access
2. **Private Pods**: Only selected Discord users can access

### 📁 Isolated Workspaces
- Each user gets their own workspace folder: `/workspace/{username}`
- Users are automatically placed in their folder when connecting
- Prevents accidental file conflicts between users

## For Admins: Creating Pods with User Access

### Step 1: Create a Pod
1. Go to Dashboard → Create Pod
2. Fill in pod configuration (name, GPU, resources, etc.)

### Step 2: Configure Access Control

#### Option A: Make it Public
- ✅ Check "Make this pod public (accessible to all Discord members)"
- All Discord members who authenticate can see and connect to this pod

#### Option B: Assign Specific Users
- ❌ Leave "Make this pod public" unchecked
- 📝 Select Discord users from the list
- ✨ Features:
  - Search through all Discord guild members
  - See usernames, nicknames, and avatars
  - Multi-select users
  - Real-time selection count

### Step 3: Create the Pod
- Click "Create Pod"
- SSH keys are automatically configured
- Selected users immediately see the pod in CLI

## For Users: Connecting to Pods

### Step 1: Authenticate
```bash
godfather auth
# or just run any command and authenticate when prompted
godfather list
```

Visit the admin portal at `/cli-auth` to get your authentication token.

### Step 2: List Available Pods
```bash
godfather list
```

You'll only see:
- Public pods
- Pods where you're in the allowed_users list

### Step 3: Connect to a Pod
```bash
godfather connect
# Select from interactive list

# OR connect directly
godfather connect <pod-id>
```

The CLI will:
1. 🔑 Fetch the SSH key automatically
2. 🔗 Connect to the pod
3. 📁 Create your workspace folder
4. 🚪 Drop you into `/workspace/{your-username}`

**No password prompt, no manual setup!**

## How It Works

### Backend Architecture

#### SSH Key Management
```python
# Organization-wide SSH key pair
ssh_keys_collection = db.ssh_keys
{
  'key_type': 'organization',
  'public_key': '...', 
  'private_key': '...',
  'created_at': datetime
}
```

#### Pod Access Control
```python
# MongoDB pod document
{
  'runpod_id': 'abc123',
  'name': 'ML Training Pod',
  'is_public': False,
  'allowed_users': ['discord_id_1', 'discord_id_2'],
  'created_by': 'clerk_user_id',
  'created_at': datetime
}
```

### Access Check Logic
```python
# User can access pod if:
is_public OR discord_user_id in allowed_users
```

### Endpoints

#### `GET /api/discord/members` (Admin only)
Fetches all Discord guild members for user selection.

**Response:**
```json
{
  "members": [
    {
      "discord_id": "123456789",
      "username": "john_doe",
      "global_name": "John Doe",
      "nickname": "Johnny",
      "avatar": "a_123abc",
      "display_name": "Johnny"
    }
  ]
}
```

#### `GET /api/pods/public` (Authenticated users)
Lists pods accessible to the current user.

**Logic:**
- Gets Discord ID from Clerk token
- Queries MongoDB for pods where `is_public=true` OR `discord_id in allowed_users`
- Returns only running pods

#### `GET /api/ssh-key` (Authenticated users)
Returns the organization's SSH private key for CLI authentication.

**Security:**
- Requires valid Clerk token
- Key stored encrypted in database
- Key permissions set to 600 in CLI

#### `POST /api/pods/<pod_id>/connect` (Authenticated users)
Gets SSH connection info for a pod.

**Access Check:**
1. Verify token
2. Get Discord ID from Clerk API
3. Check pod access: `is_public OR discord_id in allowed_users`
4. Return SSH connection details

### CLI Workflow
1. User runs `godfather connect`
2. CLI fetches SSH key from `/api/ssh-key`
3. Saves key to `~/.godfather/ssh/godfather_key` (permissions 600)
4. Gets connection info from `/api/pods/<id>/connect`
5. Runs SSH with auto-authentication: `ssh -i <key> -t root@host 'cd /workspace/{user} && bash'`

## Migration from Old System

### Before (Manual SSH Setup)
1. ❌ Admin creates pod (no SSH key)
2. ❌ User connects via CLI
3. ❌ Gets password prompt
4. ❌ Admin sets password in RunPod terminal
5. ❌ Admin shares password with user
6. ❌ User retries connection with password

### After (Automatic)
1. ✅ Admin creates pod → SSH key automatically added
2. ✅ Admin selects allowed Discord users (optional)
3. ✅ User runs `godfather connect`
4. ✅ Instantly connected, placed in personal workspace

## Security Considerations

### SSH Key Security
- **Single Org Key**: One key pair per organization
- **Secure Storage**: Private key encrypted in MongoDB
- **CLI Storage**: Key stored with 600 permissions in user's home directory
- **No Password**: SSH key authentication only, no password fallback

### Access Control
- **Discord-Based**: All access tied to Discord identities
- **Admin Role**: Only Discord users with "Admin" role can manage pods
- **Per-Pod Control**: Each pod has its own access list
- **Real-Time Updates**: Access changes take effect immediately

### Workspace Isolation
- **User Folders**: Each user gets `/workspace/{username}`
- **Automatic Creation**: Folders created on first connection
- **Ownership**: Folders owned by root but accessible to user
- **No Cross-Access**: Users cannot see other users' folders

## Troubleshooting

### "SSH key not configured"
- First pod creation triggers key generation
- Check backend logs for SSH key generation errors
- Ensure `ssh-keygen` is available in backend container

### "Pod not accessible"
- Check if pod is public OR you're in allowed_users
- Verify Discord account is linked to Clerk
- Ask admin to add you to pod's allowed users

### "SSH connection failed"
- Check pod is running (status should be RUNNING)
- Verify SSH key exists: `ls ~/.godfather/ssh/`
- Check backend logs for SSH key initialization errors
- Ensure pod's docker args include SSH key setup

### Users Don't See Discord Members
- Check `DISCORD_BOT_TOKEN` environment variable
- Verify bot has "Read Members" permission in Discord
- Check `DISCORD_GUILD_ID` is correct
- Check backend logs for Discord API errors

## Best Practices

### For Admins
1. **Test with Public First**: Create a test pod as public to verify SSH key setup works
2. **Small Groups**: For sensitive work, use private pods with specific users
3. **Clear Naming**: Use descriptive pod names so users know which to connect to
4. **Monitor Usage**: Check logs to see who's connecting to pods

### For Users
1. **Personal Workspace**: Always work in your `/workspace/{username}` folder
2. **No Root Changes**: Don't modify system files or other users' folders
3. **Clean Up**: Remove large files when done to save disk space
4. **Report Issues**: If connection fails, contact admin with error message

## Future Enhancements

Potential improvements:
- [ ] Per-user SSH keys (more secure but complex)
- [ ] SSH key rotation
- [ ] Audit logging for pod connections
- [ ] Web-based terminal (no SSH client needed)
- [ ] User groups (assign groups instead of individual users)
- [ ] Resource quotas per user
- [ ] Connection time limits
- [ ] Automatic workspace cleanup
