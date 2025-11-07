# 🚀 Accessing Godfather

## Available URLs

Godfather is accessible through **TWO URLs** for maximum flexibility:

### 1. **Primary: Custom Domain**
```
https://admin.ais-asu.com
```
- ✨ Professional branded URL
- 📝 Easy to remember and share
- 🔒 Custom SSL certificate
- ⏱️ Requires DNS setup (one-time)

### 2. **Fallback: RunPod Proxy**
```
https://xxxxx-80.proxy.runpod.net
```
- ⚡ Works instantly (no DNS needed)
- 🔄 Automatic SSL from RunPod
- 🆘 Backup if custom domain has issues
- 🧪 Perfect for testing

## Which URL Should I Use?

### For End Users
👉 **Use the custom domain:** `https://admin.ais-asu.com`
- More professional
- Easier to remember
- Branded experience

### For Development/Testing
👉 **Use the RunPod URL:** `https://xxxxx-80.proxy.runpod.net`
- No DNS wait time
- Quick testing
- Always available

### For CLI
Both work! Choose based on your preference:

```bash
# Option 1: Custom domain (recommended)
export GODFATHER_API_URL=https://admin.ais-asu.com/api
godfather connect

# Option 2: RunPod fallback
export GODFATHER_API_URL=https://xxxxx-80.proxy.runpod.net/api
godfather connect
```

## How Does This Work?

Both URLs point to the **same application**:
- Nginx is configured to accept requests from any hostname
- Both URLs route to the same backend services
- Authentication works the same on both
- All features available on both URLs

## Benefits

✅ **Zero Downtime**: Use RunPod URL while DNS propagates
✅ **Redundancy**: Multiple access points
✅ **Flexibility**: Switch between URLs as needed
✅ **No Extra Config**: Both work out of the box

## More Info

See [DUAL_URL_SETUP.md](./DUAL_URL_SETUP.md) for detailed documentation.
