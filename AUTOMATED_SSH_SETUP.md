# Godfather Automated SSH Setup Guide

This guide explains how to enable fully automated, password-free SSH access for all users.

## 🎯 Goal

After setup:
- ✅ Admins create pods with one click
- ✅ Users run `godfather connect` and instantly access pods
- ✅ No password prompts
- ✅ No manual SSH configuration

## 📋 Prerequisites

- Docker Hub account (or other container registry)
- Docker installed locally
- Access to push images to a registry

## 🚀 Setup Steps

### Step 1: Build the Custom Docker Image

```bash
cd docker-images/godfather-base

# Set your Docker Hub username
export DOCKER_USERNAME=yourdockerhubusername

# Build the image
./build.sh
```

This creates an image based on `runpod/base:0.4.0-cuda11.8.0` with automatic SSH key setup.

### Step 2: Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push the image
docker push $DOCKER_USERNAME/godfather-base:latest
```

Make note of your image name: `yourdockerhubusername/godfather-base:latest`

### Step 3: Update Frontend Default Image

Edit `frontend/app/dashboard/create-pod/page.tsx`:

```typescript
const defaultConfig: PodConfig = {
  name: '',
  image_name: 'yourdockerhubusername/godfather-base:latest', // 👈 Update this
  gpu_type_id: 'NVIDIA RTX A4000',
  // ... rest of config
};
```

Also update the Docker Image dropdown options:

```typescript
<select value={config.image_name} ...>
  <option value="yourdockerhubusername/godfather-base:latest">
    Godfather Base (Auto SSH) - Recommended ⭐
  </option>
  <option value="runpod/base:0.4.0-cuda11.8.0">
    Base CUDA 11.8 (Manual Setup Required)
  </option>
  {/* ... other options */}
</select>
```

### Step 4: Rebuild and Restart Containers

```bash
docker compose down
docker compose up -d --build
```

## ✅ Testing

### Test 1: Create a Pod

1. Go to admin dashboard → Create Pod
2. Use the default image (should be your custom image now)
3. Make it public or assign users
4. Click "Create Pod"
5. Wait for pod to start (1-2 minutes)

### Test 2: Connect via CLI

```bash
godfather connect
```

Select your pod. You should:
- ✅ See "SSH key ready"
- ✅ Connect without password prompt
- ✅ Land in `/workspace/your-username`

## 🔧 Creating Image Variants

You can create specialized images for different use cases:

### PyTorch Image

Create `docker-images/godfather-pytorch/Dockerfile`:
```dockerfile
FROM runpod/pytorch:2.0.0-py3.10-cuda11.8.0-devel

COPY setup-ssh.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]
```

### TensorFlow Image

Create `docker-images/godfather-tensorflow/Dockerfile`:
```dockerfile
FROM runpod/tensorflow:2.11.0-py3.10-cuda11.8.0-devel-ubuntu22.04

COPY setup-ssh.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]
```

Then build and push each variant:
```bash
docker build -t $DOCKER_USERNAME/godfather-pytorch:latest -f godfather-pytorch/Dockerfile .
docker push $DOCKER_USERNAME/godfather-pytorch:latest
```

## 🐛 Troubleshooting

### "Pod is still initializing"
- Wait 1-2 minutes for the pod to fully start
- The startup script needs time to run

### "SSH key authentication failed"
- Check pod logs in RunPod dashboard
- Verify `GODFATHER_SSH_PUBLIC_KEY` environment variable is set
- Check `/start.sh` executed (look for "🚀 Godfather Pod Initialization" in logs)

### "Load key error in libcrypto"
- This happens with old images that don't have the SSH key set up
- Make sure you're using the custom image

### Image pull errors
- Verify image name is correct
- Check image is public on Docker Hub (or RunPod has credentials)
- Ensure image was successfully pushed

## 🔄 Updating the Image

When you update the startup script:

```bash
cd docker-images/godfather-base

# Rebuild
./build.sh

# Push updated image
docker push $DOCKER_USERNAME/godfather-base:latest

# New pods will use the updated image automatically
# Existing pods need to be recreated
```

## 📊 Monitoring

Check if SSH keys are being set up:

```bash
# In pod terminal (RunPod web console)
cat /root/.ssh/authorized_keys
# Should show: ssh-ed25519 AAAA... godfather-org-key
```

## 🎉 Success!

Once setup is complete:
1. Admins create pods with zero SSH configuration
2. Users connect instantly with `godfather connect`
3. No passwords, no manual setup, just works! ✨

## 📝 Notes

- The SSH key is organization-wide (one key for all pods)
- Each user still gets their own `/workspace/username` folder
- Keys are stored securely in MongoDB
- Startup script is idempotent (safe to run multiple times)
