# SSH Access Setup for Godfather CLI

## Quick Start

When you create a pod and try to connect via CLI, you'll need SSH authentication. Here's how to set it up:

### Option 1: Set a Password (Quick but less secure)

1. Go to [RunPod Console](https://runpod.io/console/pods)
2. Find your pod and click "Connect" → "Web Terminal"
3. In the terminal, set a root password:
   ```bash
   passwd
   ```
4. Enter your desired password twice
5. Now you can use this password when connecting via the Godfather CLI

### Option 2: Use SSH Keys (Recommended)

#### Step 1: Generate SSH Key (if you don't have one)
```bash
# Generate a new SSH key pair
ssh-keygen -t ed25519 -C "your_email@example.com"

# Press Enter to accept default location (~/.ssh/id_ed25519)
# Optionally enter a passphrase
```

#### Step 2: Add Your Public Key to RunPod

1. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. Go to [RunPod Settings → SSH Keys](https://www.runpod.io/console/user/settings)

3. Click "Add SSH Key" and paste your public key

4. Name it (e.g., "My Laptop")

#### Step 3: Add Key to Existing Pod (One-time setup)

If your pod is already created without SSH keys:

1. Go to RunPod Console → Your Pod → "Web Terminal"
2. Run these commands:
   ```bash
   # Create .ssh directory if it doesn't exist
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   
   # Add your public key (replace with your actual public key)
   echo "ssh-ed25519 AAAAC3Nza... your_email@example.com" >> ~/.ssh/authorized_keys
   
   # Set correct permissions
   chmod 600 ~/.ssh/authorized_keys
   ```

#### Step 4: Connect via CLI

Now you can connect without a password:
```bash
godfather
# Choose option 2: Connect to a pod
# Select your pod
# SSH will connect automatically using your key
```

## Future Enhancement

In future versions, the Godfather portal will:
- Allow you to upload your SSH public key in settings
- Automatically add your key to all pods you create
- Support passwordless SSH from the first connection

## Troubleshooting

### "Permission denied (publickey,password)"
- Make sure you've added your SSH key to RunPod settings
- Verify the key is in the pod's `~/.ssh/authorized_keys`
- Or set a password using `passwd` command

### "Connection refused"
- Check if the pod is running (not stopped)
- Verify the pod has SSH enabled (port 22)

### "Host key verification failed"
- Remove the old host key: `ssh-keygen -R [host]:port`
- Try connecting again

## Security Best Practices

1. ✅ **Use SSH keys instead of passwords**
2. ✅ **Keep your private key secure** (never share it)
3. ✅ **Use different keys for different machines**
4. ✅ **Set strong passwords** if you must use password auth
5. ✅ **Regularly rotate your SSH keys**

---

For questions or issues, contact the AI Society technical team.
