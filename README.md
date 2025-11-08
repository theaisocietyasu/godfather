# Godfather - The AI Society at ASU

**Godfather** is AI Society's comprehensive GPU pod management platform. It provides a beautiful web admin portal and powerful CLI tool for managing RunPod infrastructure, enabling seamless GPU resource allocation and user access control.

[![Documentation](https://img.shields.io/badge/docs-notion-blue)](https://www.notion.so/theaisociety/Grandfather-2668867868b480cab87ecfdb4e4a1dbe)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### Admin Portal

- 🎮 **Pod Management**: Create, start, stop, restart, and terminate RunPod GPU instances
- � **Real-time Monitoring**: View pod status, resource usage, and runtime information
- 📁 **File Manager**: Web-based file browser with upload/download capabilities
- 👥 **Access Control**: Set pods as public (accessible to all members) or private (specific users only)
- 🔐 **Discord OAuth**: Secure authentication via Discord with admin role verification
- � **Cost Optimization**: CPU-only and GPU options with resource configuration

### CLI Tool

- 💻 **Secure SSH Access**: Direct terminal access to authorized pods
- 🎨 **Beautiful Interface**: Themed welcome messages with ASCII art banners
- � **User Isolation**: Each user gets their own workspace folder in shared pods
- 🤝 **Collaboration**: Shared folders for team projects
- ⚡ **Easy Discovery**: Automatically find and connect to available public pods
- 🌐 **Cross-Platform**: Works on Windows, macOS, and Linux

### Security Features

- � **SSH Key Authentication**: Automatic SSH key setup and management
- 👑 **Role-Based Access**: Admin and user roles with different permissions
- 🛡️ **Workspace Isolation**: Restricted users cannot access system files or other users' data
- � **Token-Based Auth**: JWT authentication for API requests
- 🔒 **No Sudo for Users**: Regular users run in isolated, unprivileged accounts

## 📋 Prerequisites

Before you begin, ensure you have the following:

- **Node.js** 18+ and npm (for frontend development)
- **Python** 3.8+ (for backend and CLI)
- **RunPod Account** with API access ([Get API Key](https://www.runpod.io/console/user/settings))
- **Discord Bot** with permissions to read server roles
- **MongoDB** instance (can use Docker or MongoDB Atlas)
- **Clerk Account** for Discord OAuth integration ([Sign up](https://clerk.com))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather
```

### 2. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration (see Environment Variables section)

# Run the backend server
python app.py
```

The backend will start on `http://localhost:5000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
# Add your Clerk keys and API URL

# Run the development server
npm run dev
```

The frontend will start on `http://localhost:3000`

### 4. CLI Installation (for Users)

**For Development:**

```bash
cd cli
pip install -e .
godfather
```

**For Production (from PyPI):**

```bash
pip install godfather-cli
godfather
```

## ⚙️ Environment Variables

### Backend Configuration (`backend/.env`) -- Ask Admin

### Frontend Configuration (`frontend/.env.local`) -- Ask Admin

### Setting Up Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select existing
3. Go to **Bot** section and create a bot
4. Copy the bot token to `DISCORD_BOT_TOKEN`
5. Enable **Server Members Intent** and **Message Content Intent**
6. Go to **OAuth2** > **URL Generator**
   - Select scopes: `bot`
   - Select bot permissions: `Read Messages/View Channels`
7. Invite bot to your Discord server
8. Get your server ID (enable Developer Mode in Discord, right-click server, Copy ID)
9. Get your Admin role ID (right-click role, Copy ID)

### Setting Up Clerk

1. Sign up at [Clerk](https://clerk.com)
2. Create a new application
3. Enable **Discord** OAuth provider
4. Configure redirect URLs:
   - Development: `http://localhost:3000`
   - Production: `https://admin.ais-asu.com`
5. Copy your publishable and secret keys to frontend `.env.local`

## 📁 Project Structure

```
godfather/
├── backend/                    # Flask API Server
│   ├── api/                   # API route handlers
│   │   ├── auth_routes.py    # Authentication endpoints
│   │   ├── pod_routes.py     # Pod management endpoints
│   │   ├── file_routes.py    # File operations endpoints
│   │   ├── ssh_routes.py     # SSH connection endpoints
│   │   └── discord_routes.py # Discord integration endpoints
│   ├── services/              # Business logic layer
│   │   ├── pod_service.py    # RunPod API interactions
│   │   ├── auth_service.py   # Authentication logic
│   │   ├── discord_service.py # Discord API interactions
│   │   └── ssh_service.py    # SSH key management
│   ├── middleware/            # Request middleware
│   │   └── auth.py           # JWT authentication middleware
│   ├── config/                # Configuration
│   │   ├── settings.py       # App settings
│   │   └── database.py       # MongoDB connection
│   ├── utils/                 # Utility functions
│   │   └── logger.py         # Logging configuration
│   ├── app.py                # Main application entry point
│   ├── file_manager.py       # SSH/SFTP file operations
│   └── requirements.txt      # Python dependencies
│
├── frontend/                  # Next.js Admin Portal
│   ├── app/                  # Next.js 15 App Router
│   │   ├── api/             # API routes
│   │   │   └── auth/        # NextAuth configuration
│   │   ├── dashboard/       # Main dashboard pages
│   │   │   ├── page.tsx    # Pod list view
│   │   │   ├── create-pod/ # Pod creation form
│   │   │   └── pods/[id]/  # Pod detail view
│   │   ├── cli-auth/        # CLI authentication page
│   │   └── settings/        # User settings
│   ├── components/           # Reusable React components
│   │   ├── Navbar.tsx       # Navigation bar
│   │   └── FileManager.tsx  # File browser component
│   ├── lib/                 # Utilities and configurations
│   │   ├── auth.ts         # Auth helper functions
│   │   └── auth-client.ts  # Client-side auth
│   ├── types/               # TypeScript type definitions
│   │   └── next-auth.d.ts  # NextAuth type extensions
│   └── package.json         # Node.js dependencies
│
├── cli/                      # Python CLI Tool
│   ├── godfather_cli/       # CLI package
│   │   ├── __init__.py     # Package initialization
│   │   ├── cli.py          # Main CLI interface
│   │   ├── auth.py         # CLI authentication
│   │   ├── pod_manager.py  # Pod listing and selection
│   │   └── ssh_connector.py # SSH connection handler
│   ├── pyproject.toml       # Python package configuration
│   ├── README.md            # CLI-specific documentation
│   └── publish.sh           # PyPI publishing script
│
├── docker-images/            # Custom Docker Images
│   └── godfather-base/      # Custom RunPod base image
│       ├── Dockerfile       # Image definition
│       ├── setup-ssh.sh     # SSH setup and theming script
│       └── build.sh         # Build script for Docker Hub
│
├── nginx/                    # Nginx Reverse Proxy
│   ├── nginx.direct.conf    # Production configuration (used by deploy-direct.sh)
│   └── ssl/                 # SSL certificates directory
│
├── docker-compose.yml        # Docker Compose for development
├── docker-compose.prod.yml   # Docker Compose for production
├── .env.example             # Example environment variables
└── README.md                # This file
```

## 🎯 Usage

### Admin Portal

1. **Login**

   - Visit `http://localhost:3000` (or your production URL)
   - Click "Sign in with Discord"
   - Authenticate via Discord OAuth
   - Only users with the configured Admin role can access
2. **Create a Pod**

   - Navigate to Dashboard
   - Click "Create Pod"
   - Configure pod settings:
     - **Name**: Unique identifier for the pod
     - **Image**: Docker image (recommended: `theaisocietyasu/godfather-base:latest`)
     - **Compute Type**: Choose CPU-only or GPU
     - **Resources**: Set vCPU, memory, disk space
     - **Access Control**: Make public or select specific users
   - Click "Create Pod"
3. **Manage Pods**

   - View all pods on the dashboard
   - Start/Stop/Restart/Terminate pods
   - Monitor resource usage and status
   - Access file manager for running pods
4. **Access Control**

   - **Public Pods**: Any Discord member can connect via CLI
   - **Private Pods**: Only selected users can access
   - Each user gets isolated workspace in `/workspace/users/<username>`

### CLI Tool

#### Authentication

```bash
# First time setup - authenticate via web browser
godfather auth login

# Check authentication status
godfather auth status

# Logout
godfather auth logout
```

#### Pod Management

```bash
# Interactive mode (recommended for beginners)
godfather

# List available pods
godfather list

# Connect to a pod (interactive selection)
godfather connect

# Connect to specific pod
godfather connect <pod-id>

# Show pod details
godfather status <pod-id>
```

#### Inside a Pod

Once connected, you'll see a beautiful themed interface:

- Your personal workspace: `/workspace/users/<your-username>`
- Shared collaboration folder: `/workspace/shared`
- Useful aliases: `workspace`, `shared`, `ll`
- Type `exit` to disconnect

### API Usage

#### Authentication

All API requests require Discord user ID header for authentication:

```bash
curl -X GET http://localhost:5000/api/pods \
  -H "X-Discord-User-ID: your_discord_user_id"
```

#### Create a Pod

```bash
curl -X POST http://localhost:5000/api/pods \
  -H "Content-Type: application/json" \
  -H "X-Discord-User-ID: your_discord_user_id" \
  -d '{
    "name": "my-gpu-pod",
    "image_name": "theaisocietyasu/godfather-base:latest",
    "gpu_type_id": "NVIDIA RTX A4000",
    "cloud_type": "COMMUNITY",
    "volume_in_gb": 10,
    "is_public": true
  }'
```

#### Control a Pod

```bash
# Start pod
curl -X POST http://localhost:5000/api/pods/{pod_id}/action \
  -H "Content-Type: application/json" \
  -H "X-Discord-User-ID: your_discord_user_id" \
  -d '{"action": "start"}'

# Stop pod
curl -X POST http://localhost:5000/api/pods/{pod_id}/action \
  -H "Content-Type: application/json" \
  -H "X-Discord-User-ID: your_discord_user_id" \
  -d '{"action": "stop"}'

# Terminate pod
curl -X POST http://localhost:5000/api/pods/{pod_id}/action \
  -H "Content-Type: application/json" \
  -H "X-Discord-User-ID: your_discord_user_id" \
  -d '{"action": "terminate"}'
```

## 📦 Publishing to Production

### Deployment Scripts Overview

Godfather provides three main deployment scripts:

1. **`./deploy-portal.sh`** - Deploy the web portal (frontend + backend)
   - Sets up and deploys the admin portal to RunPod
   - Handles both frontend and backend services
   - Configures Nginx reverse proxy

2. **`./deploy-cli.sh`** - Deploy the CLI tool to PyPI
   - Build and publish the CLI package to PyPI
   - Test the CLI locally before publishing
   - Supports both Test PyPI and Production PyPI

3. **`./deploy-docker.sh`** - Deploy the Docker base image
   - Build and push the `godfather-base` image to Docker Hub
   - Tag images with versions and 'latest'
   - Test images locally before pushing

### Publishing Docker Image to Docker Hub

The `godfather-base` Docker image provides automatic SSH setup, themed CLI interface, and user isolation for RunPod instances.

**Using the deployment script (recommended):**

```bash
# Run the interactive deployment script
./deploy-docker.sh

# The script will guide you through:
# 1. Building the image
# 2. Tagging versions (including 'latest')
# 3. Testing locally (optional)
# 4. Pushing to Docker Hub
```

**Manual steps:**

```bash
# Navigate to the Docker image directory
cd docker-images/godfather-base

# Build the image (replace with your Docker Hub username)
docker build -t theaisocietyasu/godfather-base:latest .

# Login to Docker Hub
docker login

# Push the image to Docker Hub
docker push theaisocietyasu/godfather-base:latest

# Optional: Tag and push a specific version
docker tag theaisocietyasu/godfather-base:latest theaisocietyasu/godfather-base:v1.0.0
docker push theaisocietyasu/godfather-base:v1.0.0
```

**After publishing:**

1. Update the default image in `frontend/app/dashboard/create-pod/page.tsx`
2. Change `theaisocietyasu/godfather-base:latest` to your image name
3. Users can now select your custom image when creating pods

### Publishing CLI to PyPI

**Using the deployment script (recommended):**

```bash
# Run the interactive deployment script
./deploy-cli.sh

# The script provides options to:
# 1. Build & Publish to PyPI (Test or Production)
# 2. Test locally before publishing
# 3. Build only without publishing
# 4. Update version numbers interactively
```

**Manual Publishing:**

```bash
cd cli

# Install publishing tools
pip install build twine

# Update version in pyproject.toml
# Edit the version field: version = "1.0.3"

# Build the package
python -m build

# Test locally (optional)
pip install --force-reinstall dist/godfather_cli-*.whl

# Upload to Test PyPI (recommended for testing)
twine upload --repository testpypi dist/*

# Upload to Production PyPI
twine upload dist/*
# Use __token__ as username and your API token as password
```

**Via GitHub Actions (Alternative):**

```bash
# 1. Update version in pyproject.toml
# 2. Commit your changes
git add .
git commit -m "Release CLI v1.0.3"

# 3. Create and push a version tag
git tag cli-v1.0.3
git push origin cli-v1.0.3

# GitHub Actions will automatically build and publish
```

**Setting up PyPI credentials for GitHub Actions:**

1. Create PyPI account at https://pypi.org
2. Generate API token at https://pypi.org/manage/account/token/
3. Add token to GitHub repository secrets as `PYPI_API_TOKEN`
4. The workflow uses trusted publishing (no token needed with proper setup)

### Publishing Checklist

**Before Docker Image Release:**

- [ ] Test the image locally with SSH connection
- [ ] Verify themed welcome messages display correctly
- [ ] Check user isolation and workspace creation
- [ ] Test with both admin and regular users
- [ ] Run: `./deploy-docker.sh` and follow the prompts
- [ ] Update default image in `frontend/app/dashboard/create-pod/page.tsx`

**Before CLI Release:**

- [ ] Update version number in `cli/pyproject.toml`
- [ ] Update `cli/README.md` or CHANGELOG with changes
- [ ] Test CLI commands locally: `cd cli && pip install -e .`
- [ ] Verify authentication flow works
- [ ] Test SSH connection to pods
- [ ] Run: `./deploy-cli.sh` and choose "Test CLI locally"
- [ ] Run: `./deploy-cli.sh` and choose "Build & Publish to PyPI"
- [ ] Verify package on PyPI
- [ ] Create GitHub release with notes (optional)

**Before Web App Deployment:**

- [ ] Update environment variables for production
- [ ] Configure SSL certificates
- [ ] Update domain in nginx configuration
- [ ] Test authentication flow
- [ ] Verify API endpoints work correctly
- [ ] Test pod creation and management
- [ ] Check file manager functionality

## 🔒 API Reference

### Authentication

All API endpoints require the `X-Discord-User-ID` header for authentication. Admin endpoints also verify the user has the Admin role in Discord.

### Endpoints

#### **Authentication**

- `POST /api/auth/verify`
  - Verify Discord user has admin access
  - Body: `{ "discord_user_id": "string" }`
  - Returns: `{ "is_admin": boolean, "user": {...} }`

#### **Pod Management**

- `GET /api/pods`

  - List all pods for admin
  - Headers: `X-Discord-User-ID`
  - Returns: Array of pod objects
- `POST /api/pods`

  - Create a new pod
  - Headers: `X-Discord-User-ID`
  - Body: Pod configuration object
  - Returns: Created pod details
- `GET /api/pods/<pod_id>`

  - Get specific pod details
  - Headers: `X-Discord-User-ID`
  - Returns: Pod object with full details
- `PUT /api/pods/<pod_id>`

  - Update pod configuration (access control)
  - Headers: `X-Discord-User-ID`
  - Body: `{ "is_public": boolean, "allowed_users": ["user_id", ...] }`
- `POST /api/pods/<pod_id>/action`

  - Control pod (start/stop/restart/terminate)
  - Headers: `X-Discord-User-ID`
  - Body: `{ "action": "start" | "stop" | "restart" | "terminate" }`

#### **CLI Access**

- `GET /api/pods/public`

  - List public pods accessible to user
  - Headers: `X-Discord-User-ID`
  - Returns: Array of accessible pods
- `POST /api/pods/<pod_id>/connect`

  - Get SSH connection information
  - Headers: `X-Discord-User-ID`
  - Returns: `{ "host": string, "port": number, "username": string, "is_admin": boolean }`
- `GET /api/ssh-key`

  - Get user's SSH private key for pod access
  - Headers: `X-Discord-User-ID`
  - Returns: `{ "private_key": string }`

#### **File Management**

- `GET /api/pods/<pod_id>/files`

  - List files in pod
  - Headers: `X-Discord-User-ID`
  - Query: `?path=/workspace`
  - Returns: Array of file objects
- `POST /api/pods/<pod_id>/files/upload`

  - Upload file to pod
  - Headers: `X-Discord-User-ID`
  - Body: FormData with file
  - Returns: Upload confirmation

#### **Discord Integration**

- `GET /api/discord/members`
  - Get all Discord server members
  - Headers: `X-Discord-User-ID`
  - Returns: Array of member objects with avatars and names

## 🛠️ Development

### Running in Development Mode

**Backend:**

```bash
cd backend
# Set Flask environment
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

**Frontend:**

```bash
cd frontend
npm run dev
```

**With Hot Reload:**

- Backend: Flask auto-reloads on file changes when `FLASK_DEBUG=1`
- Frontend: Next.js has built-in hot reload

### Testing

**Backend Tests:**

```bash
cd backend
pytest tests/
```

**Frontend Tests:**

```bash
cd frontend
npm test
```

### Code Style

**Python (Backend & CLI):**

- Follow PEP 8 style guide
- Use Black for formatting: `black .`
- Use flake8 for linting: `flake8 .`

**TypeScript/JavaScript (Frontend):**

- Use ESLint: `npm run lint`
- Use Prettier for formatting: `npm run format`

## 🐛 Troubleshooting

### Common Issues

**CLI not found after installation:**

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Make permanent (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Make permanent (zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Authentication fails:**

- Verify Discord bot is in the server
- Check bot has "Server Members Intent" enabled
- Confirm Discord user has the Admin role
- Verify `DISCORD_GUILD_ID` and `ADMIN_ROLE_ID` are correct
- Check Clerk configuration and redirect URLs

**Can't connect to pod via CLI:**

- Ensure pod is running (status: RUNNING)
- Verify you're using the `godfather-base` Docker image
- Check pod has SSH enabled (port 22)
- Confirm you have access (public pod or you're in allowed_users)
- Try restarting the pod

**MongoDB connection errors:**

- Check MongoDB is running: `mongosh` or `docker ps`
- Verify `MONGODB_URI` in `.env`
- For Atlas, check IP whitelist and credentials

**RunPod API errors:**

- Verify `RUNPOD_API_KEY` is valid
- Check RunPod account has sufficient credits
- Ensure pod template/GPU type is available

**Frontend build errors:**

```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run dev
```

**Port already in use:**

```bash
# Find process using port 3000 (frontend)
lsof -i :3000
kill -9 <PID>

# Find process using port 5000 (backend)
lsof -i :5000
kill -9 <PID>
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**: `git commit -m 'Add amazing feature'`
6. **Push to your fork**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Contribution Guidelines

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Keep commits focused and atomic
- Write descriptive commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AI Society ASU** - For sponsoring and supporting this project
- **RunPod** - For providing GPU infrastructure
- **Clerk** - For authentication services
- **Discord** - For OAuth integration and community platform

## 📞 Support

Need help? Here's how to get support:

- **Documentation**: [Notion Docs](https://www.notion.so/theaisociety/Grandfather-2668867868b480cab87ecfdb4e4a1dbe)
- **Issues**: [GitHub Issues](https://github.com/theaisocietyasu/godfather/issues)
- **Discord**: AI Society ASU Discord Server
- **Email**: Contact AI Society administrators
