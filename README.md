# Godfather - AI Society Admin Portal

The mastermind backend that's powered by GPU, will be the main platform for all our tools.

A comprehensive admin dashboard for managing RunPod services/environments, built for AI Society ASU. This system provides secure authentication, pod management, file operations, and CLI access.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin Portal  │    │      CLI        │    │   Discord       │
│   (Next.js)     │    │   (Python)      │    │     OAuth       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     Backend API           │
                    │     (Flask)               │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
    ┌─────────▼─────────┐ ┌───────▼───────┐ ┌─────────▼─────────┐
    │    MongoDB        │ │   RunPod API  │ │   Discord API     │
    │   (Database)      │ │    (Pods)     │ │   (Auth Check)    │
    └───────────────────┘ └───────────────┘ └───────────────────┘
```

## 🚀 Features

### Admin Portal
- **🔐 Secure Authentication**: Discord OAuth with Admin role verification
- **🖥️ Pod Management**: Create, monitor, start, stop, and terminate pods
- **📁 File Management**: Web-based file browser with upload/download
- **👥 Access Control**: Public/private pod settings for CLI access
- **📊 Monitoring**: Real-time pod status and resource monitoring
- **🎨 Modern UI**: Clean, responsive design with dark/light themes

### CLI Tool
- **🔑 Secure Access**: Token-based authentication
- **🔍 Pod Discovery**: List and connect to available public pods
- **🚪 SSH Integration**: Direct terminal access to pod environments
- **👤 User Isolation**: Each user gets their own workspace folder
- **🌐 Cross-Platform**: Works on Windows, macOS, and Linux

### Security
- **🛡️ Role-Based Access**: Discord Admin role required
- **🔒 JWT Authentication**: Secure token-based API access
- **🔐 SSL/TLS**: HTTPS encryption for production
- **🚫 Rate Limiting**: API protection against abuse
- **🏠 User Isolation**: Secure workspace separation

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.7+ (for CLI)
- OpenSSH client (for pod connections)
- Discord account with Admin role in AI Society server
- RunPod API key
- Clerk account for authentication

## 🛠️ Quick Setup

### 1. Clone and Setup
```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment
Edit `.env` file with your credentials:
```bash
RUNPOD_API_KEY=your_runpod_api_key
CLERK_SECRET_KEY=your_CLERK_SECRET_KEY
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_discord_guild_id
```

Edit `frontend/.env.local`:
```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_CLERK_SECRET_KEY
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### 3. Start Services
```bash
./dev.sh start
```

### 4. Install CLI
```bash
cd cli
pip install -e .
# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

## 🎯 Usage

### Admin Portal
1. Visit `http://localhost` (or `https://admin.ais-asu.com` in production)
2. Sign in with Discord (Admin role required)
3. Create and manage RunPod environments
4. Configure public access for CLI users

### CLI Tool
```bash
# Interactive mode
godfather

# List available pods
godfather list

# Connect to a pod
godfather connect

# Check status
godfather status
```

## 🔧 Development

### Development Commands
```bash
# Start all services
./dev.sh start

# View logs
./dev.sh logs

# Open shell in backend
./dev.sh shell backend

# Build and restart
./dev.sh build && ./dev.sh restart

# Show service status
./dev.sh status
```

### Project Structure
```
godfather/
├── backend/              # Flask API server
│   ├── app.py           # Main application
│   ├── file_manager.py  # SSH/SFTP utilities
│   └── requirements.txt # Python dependencies
├── frontend/            # Next.js admin portal
│   ├── app/            # App router pages
│   ├── components/     # React components
│   └── middleware.ts   # Clerk middleware
├── cli/                # Python CLI tool
│   ├── godfather_cli/  # CLI package
│   └── pyproject.toml  # Package configuration
├── nginx/              # Reverse proxy
│   └── nginx.conf      # Configuration
├── docker-compose.yml  # Service orchestration
├── setup.sh           # Installation script
└── dev.sh             # Development helper
```

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/verify` - Verify Discord admin access

### Pod Management
- `GET /api/pods` - List all pods
- `POST /api/pods` - Create new pod
- `GET /api/pods/{id}` - Get pod details
- `PUT /api/pods/{id}` - Update pod settings
- `POST /api/pods/{id}/action` - Control pod (start/stop/restart/terminate)

### CLI Access
- `GET /api/pods/public` - List public pods for CLI
- `POST /api/pods/{id}/connect` - Get SSH connection details

### File Management
- `GET /api/pods/{id}/files` - List pod files
- `POST /api/pods/{id}/files/upload` - Upload files

## 🚀 Production Deployment

### 1. Server Setup
```bash
# On your Ubuntu server
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather
```

### 2. Configure Production Environment
```bash
# Update .env with production values
cp .env.example .env
# Edit .env with production credentials

# Update domain in nginx config
# Edit nginx/nginx.conf for your domain
```

### 3. SSL Certificates
```bash
# For Let's Encrypt (recommended)
certbot certonly --webroot -w /var/www/html -d admin.ais-asu.com

# Copy certificates to nginx/ssl/
cp /etc/letsencrypt/live/admin.ais-asu.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/admin.ais-asu.com/privkey.pem nginx/ssl/key.pem
```

### 4. Deploy
```bash
./setup.sh
# Follow the prompts for production setup
```

### 5. DNS Configuration
Point `admin.ais-asu.com` to your server's IP address.

## 🔧 Configuration

### Clerk Setup
1. Create a Clerk application
2. Enable Discord OAuth provider
3. Configure redirect URLs:
   - Development: `http://localhost:3000`
   - Production: `https://admin.ais-asu.com`
4. Set up webhooks for user management

### Discord Bot Setup
1. Create Discord application and bot
2. Add bot to AI Society server with read permissions
3. Note the bot token and guild ID
4. Ensure "Admin" role exists in your Discord server

### RunPod API
1. Get API key from RunPod dashboard
2. Ensure sufficient credits for pod creation
3. Configure default pod templates as needed

## 📊 Monitoring

### Health Checks
```bash
# Check all services
./dev.sh status

# Individual service health
curl http://localhost/health
curl http://localhost:5000/health
```

### Logs
```bash
# All logs
./dev.sh logs

# Specific service
./dev.sh logs backend
./dev.sh logs frontend
```

### Backup
```bash
# Create backup
./dev.sh backup

# Backups stored in backups/ directory
```

## 🔒 Security Considerations

- **Discord Authentication**: Only users with Admin role can access
- **API Rate Limiting**: Protects against abuse
- **Environment Variables**: Keep secrets secure
- **SSL/TLS**: Always use HTTPS in production
- **User Isolation**: Each CLI user has separate workspace
- **Token Expiration**: JWT tokens have reasonable expiry times

## 🛟 Troubleshooting

### Common Issues

**CLI not found after installation:**
```bash
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

**Services not starting:**
```bash
# Check logs
./dev.sh logs

# Reset everything
./dev.sh reset
./setup.sh
```

**Authentication issues:**
1. Verify Discord Admin role
2. Check Clerk configuration
3. Ensure Discord bot has proper permissions

**Pod connection failures:**
1. Verify RunPod API key
2. Check pod status (must be running)
3. Ensure SSH client is installed

### Getting Help
- Check the logs: `./dev.sh logs`
- Verify configuration: `./dev.sh status`
- Contact AI Society administrators
- Create an issue on GitHub

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## � License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- AI Society ASU team
- RunPod for GPU infrastructure
- Clerk for authentication services
- Discord for OAuth integration

---

Built with ❤️ by AI Society ASU

[Documentation](https://www.notion.so/theaisociety/Grandfather-2668867868b480cab87ecfdb4e4a1dbe?source=copy_link)

## 🏗️ Architecture

The Godfather system consists of several interconnected components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Frontend    │    │     Backend     │    │    Database     │
│   (Next.js)     │◄──►│    (Flask)      │◄──►│   (MongoDB)     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Nginx      │    │   RunPod API    │    │ Discord OAuth   │
│ (Reverse Proxy) │    │                 │    │   (via Clerk)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲
         │
         ▼
┌─────────────────┐
│       CLI       │
│    (Python)     │
└─────────────────┘
```

## 🚀 Features

### Admin Dashboard
- **Discord OAuth Authentication**: Secure login via AI Society Discord server
- **RunPod Management**: Create, monitor, and manage GPU environments
- **Access Control**: Set pods as public/private for user access
- **Real-time Monitoring**: View pod status, resource usage, and health
- **File Management**: Browse and manage files in running pods
- **User Management**: Control who can access specific environments

### CLI Tool
- **Secure Connection**: Direct SSH access to authorized pods
- **Isolated Workspaces**: Each user gets their own folder in shared pods
- **Easy Discovery**: Automatically find available public pods
- **Cross-Platform**: Works on Windows, macOS, and Linux

### Security Features
- **Role-Based Access**: Only Discord server admins can manage pods
- **Token-Based Auth**: Secure JWT authentication via Clerk
- **Isolated Environments**: User workspaces are strictly separated
- **SSL/TLS**: Encrypted connections in production

## 📋 Prerequisites

- **Docker & Docker Compose**: For containerized deployment
- **RunPod Account**: With API access for pod management
- **Clerk Account**: For Discord OAuth integration
- **Discord Bot**: With permissions to check user roles
- **Domain & SSL**: For production deployment (optional for development)

## 🛠️ Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather
```

### 2. Run Setup Script

```bash
./setup.sh
```

The setup script will:
- Check Docker installation
- Create environment files
- Generate SSL certificates
- Build and start all services
- Install the CLI tool

### 3. Configure Environment Variables

Edit `.env` with your API keys:

```bash
# RunPod API Configuration
RUNPOD_API_KEY=your_runpod_api_key_here

# Clerk Authentication
CLERK_SECRET_KEY=sk_live_your_CLERK_SECRET_KEY
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_your_clerk_public_key

# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_discord_server_id
```

Edit `frontend/.env.local`:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_your_clerk_public_key
CLERK_SECRET_KEY=sk_live_your_CLERK_SECRET_KEY
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### 4. Access the Portal

- **Local Development**: http://localhost
- **Production**: https://admin.ais-asu.com

## 🔧 Manual Setup

If you prefer manual setup or need to customize the installation:

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### CLI Setup

```bash
cd cli
pip install -e .
godfather --help
```

## 🎯 Usage

### Admin Dashboard

1. **Login**: Visit the portal and sign in with Discord
2. **Create Pods**: Click "Create Pod" and configure your environment
3. **Manage Access**: Toggle public/private access for each pod
4. **Monitor**: View real-time status and resource usage
5. **File Management**: Browse and edit files in running pods

### CLI Usage

```bash
# Interactive mode
godfather

# List available pods
godfather list

# Connect to a pod
godfather connect

# Connect to specific pod
godfather connect <pod-id>

# Check status
godfather status

# Logout
godfather logout
```

## 🔐 Authentication & Security

### Discord OAuth Setup

1. **Create Clerk Application**:
   - Sign up at [clerk.com](https://clerk.com)
   - Create a new application
   - Enable Discord OAuth provider

2. **Discord Bot Setup**:
   - Create bot at [Discord Developer Portal](https://discord.com/developers/applications)
   - Add bot to your Discord server
   - Grant necessary permissions to read roles

3. **Configure Role Checking**:
   - Ensure users have "Admin" role in Discord server
   - Bot will verify role before granting access

### Security Best Practices

- **Use SSL/TLS** in production environments
- **Rotate API keys** regularly
- **Monitor access logs** for suspicious activity
- **Limit pod exposure** to trusted networks
- **Regular security audits** of configurations

## 🏗️ Development

### Project Structure

```
godfather/
├── backend/           # Flask API server
│   ├── app.py        # Main application
│   ├── file_manager.py # SSH/SFTP utilities
│   └── requirements.txt
├── frontend/          # Next.js web interface
│   ├── app/          # App router pages
│   ├── components/   # Reusable components
│   └── package.json
├── cli/              # Python CLI tool
│   ├── godfather_cli/
│   └── pyproject.toml
├── nginx/            # Reverse proxy config
├── docker-compose.yml
└── setup.sh
```

### API Endpoints

#### Authentication
- `POST /api/auth/verify` - Verify Discord admin status

#### Pod Management
- `GET /api/pods` - List all pods
- `POST /api/pods` - Create new pod
- `GET /api/pods/<id>` - Get pod details
- `PUT /api/pods/<id>` - Update pod configuration
- `POST /api/pods/<id>/action` - Start/stop/restart pod

#### Public Access
- `GET /api/pods/public` - List public pods for CLI
- `POST /api/pods/<id>/connect` - Get SSH connection info

#### File Management
- `GET /api/pods/<id>/files` - List files in pod
- `POST /api/pods/<id>/files/upload` - Upload file to pod

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RUNPOD_API_KEY` | RunPod API authentication | Yes |
| `CLERK_SECRET_KEY` | Clerk authentication secret | Yes |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk public key | Yes |
| `DISCORD_BOT_TOKEN` | Discord bot token | Yes |
| `DISCORD_GUILD_ID` | Discord server ID | Yes |
| `MONGODB_URI` | MongoDB connection string | Auto |

## 🐳 Docker Deployment

The system uses Docker Compose for easy deployment:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

### Production Deployment

For production deployment:

1. **Domain Setup**: Point `admin.ais-asu.com` to your server
2. **SSL Certificates**: Replace self-signed certs with valid ones
3. **Environment Security**: Use production-grade secrets
4. **Monitoring**: Set up logging and monitoring systems
5. **Backups**: Configure MongoDB backups

## 🔍 Troubleshooting

### Common Issues

#### Authentication Problems
```bash
# Check Clerk configuration
curl -X POST http://localhost:5000/api/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token":"your_token"}'
```

#### Pod Connection Issues
```bash
# Check RunPod API connectivity
curl -H "Authorization: Bearer $RUNPOD_API_KEY" \
  https://api.runpod.io/v1/user/pods
```

#### Docker Issues
```bash
# Check container status
docker-compose ps

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb
```

### Debug Mode

Enable debug mode for additional logging:

```bash
# Backend debug
FLASK_DEBUG=1 python backend/app.py

# Frontend debug
npm run dev -- --debug

# CLI debug
godfather --debug list
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with detailed description

### Development Guidelines

- Follow Python PEP 8 for backend code
- Use TypeScript for frontend development
- Write comprehensive tests for new features
- Update documentation for API changes
- Follow security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- **GitHub Issues**: Report bugs and feature requests
- **Discord**: Join AI Society ASU Discord server
- **Email**: Contact AI Society administrators
- **Documentation**: Check the Notion documentation link

## 🎯 Roadmap

- [ ] **Advanced Monitoring**: Resource usage metrics and alerts
- [ ] **Multi-Cloud Support**: Integration with other GPU providers
- [ ] **Advanced File Management**: Web-based file editor
- [ ] **User Quotas**: Resource limits per user
- [ ] **Audit Logging**: Comprehensive activity logs
- [ ] **API Rate Limiting**: Enhanced security controls
- [ ] **Webhook Integration**: Slack/Discord notifications
- [ ] **Backup Management**: Automated pod backups

---

**Built with ❤️ by AI Society ASU**

For the latest updates and documentation, visit our [Notion page](https://www.notion.so/theaisociety/Grandfather-2668867868b480cab87ecfdb4e4a1dbe?source=copy_link).dfather
The mastermind backend that’s powered by GPU, will be the main platform for all our t ools.

[Documentation](https://www.notion.so/theaisociety/Grandfather-2668867868b480cab87ecfdb4e4a1dbe?source=copy_link)
