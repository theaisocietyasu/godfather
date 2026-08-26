# Godfather - The AI Society at ASU

Godfather is AI Society's GPU pod management platform. It provides a web admin portal and a CLI tool for managing RunPod infrastructure, GPU resource allocation, and member access control.

[![Documentation](https://img.shields.io/badge/docs-notion-blue)](https://www.notion.so/theaisociety/Grandfather-2668867868b480cab87ecfdb4e4a1dbe)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

### Admin Portal

- Pod management: create, start, stop, restart, and terminate RunPod GPU instances
- Pod status, resource usage, and runtime information
- Web-based file manager with upload/download
- Access control: pods can be public (all members) or private (specific users)
- Discord OAuth login with admin role verification
- CPU-only and GPU instance options with configurable resources

### CLI Tool

- SSH access to authorized pods
- Themed welcome banner and terminal interface on connect
- Per-user workspace folder in shared pods, plus a shared collaboration folder
- Discovery of available public pods

### Security

- Automatic SSH key setup and management
- Admin/user roles with different permissions
- Workspace isolation - restricted users cannot access system files or other users' data
- JWT-based API authentication
- Non-admin users run in unprivileged accounts with no sudo access

## Prerequisites

- Node.js 20+ and npm (frontend)
- Python 3.11+ (backend and CLI)
- A RunPod account with API access ([get an API key](https://www.runpod.io/console/user/settings))
- A Discord bot with permission to read server roles
- A MongoDB instance (local, Docker, or MongoDB Atlas)
- A Discord application configured as an OAuth provider (used by NextAuth.js on the frontend)

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt

# Create .env in the repo root (see Environment Variables below)
python app.py
```

The backend is a Flask app and starts on `http://localhost:5000` by default. It's organized as a domain per feature under `backend/domains/`:

```
backend/
├── app.py                  # Flask app entry point, blueprint registration
├── domains/
│   ├── pods/                # Pod CRUD and lifecycle (RunPod API calls)
│   ├── auth/                 # Discord-based auth/authorization, JWT middleware
│   ├── discord/               # Discord bot/API integration (guild members, roles)
│   ├── ssh/                   # SSH key issuance and pod connection info
│   └── files/                  # SSH/SFTP-backed file manager for pods
└── shared/
    ├── config.py             # Settings loaded from environment variables
    ├── database.py            # MongoDB connection
    └── logger.py               # Logging configuration
```

Each domain has its own `routes.py` (Flask blueprint) and `service.py` (business logic / external API calls).

### 3. Frontend

```bash
cd frontend
npm install

# Create .env.local (see Environment Variables below)
npm run dev
```

The frontend is a Next.js 15 app (App Router) and starts on `http://localhost:3000`. Authentication uses [NextAuth.js](https://authjs.dev/) with a Discord provider, configured in `frontend/lib/auth.ts`.

### 4. CLI (for members)

For development:

```bash
cd cli
pip install -e .
godfather
```

From PyPI:

```bash
pip install godfather-cli
godfather
```

See [`cli/README.md`](cli/README.md) for CLI usage and commands.

## Environment Variables

### Backend (`.env` in repo root, loaded by `backend/shared/config.py`)

| Variable | Required | Description |
| --- | --- | --- |
| `RUNPOD_API_KEY` | yes | RunPod API key used for pod operations |
| `DISCORD_BOT_TOKEN` | yes | Discord bot token, used to look up guild members/roles |
| `DISCORD_GUILD_ID` | yes | Discord server (guild) ID |
| `ADMIN_ROLE_ID` | no | Discord role ID that grants admin access |
| `MONGODB_URI` | no | MongoDB connection string (defaults to `mongodb://localhost:27017/godfather`) |
| `LOG_LEVEL` | no | Logging level (defaults to `INFO`) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
| --- | --- | --- |
| `DISCORD_CLIENT_ID` | yes | Discord OAuth application client ID |
| `DISCORD_CLIENT_SECRET` | yes | Discord OAuth application client secret |
| `NEXTAUTH_URL` | yes | Base URL of the frontend (e.g. `http://localhost:3000`) |
| `NEXTAUTH_SECRET` | yes | Secret used by NextAuth.js to sign session tokens |
| `BACKEND_URL` | no | URL of the backend API (defaults to `http://localhost:8000`) |
| `NEXT_PUBLIC_APP_URL` | no | Public URL of the frontend app, exposed to the browser |

### Setting up the Discord bot and OAuth app

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create an application.
2. Under **Bot**, create a bot and copy its token to `DISCORD_BOT_TOKEN`. Enable the **Server Members Intent**.
3. Under **OAuth2**, copy the client ID and secret to `DISCORD_CLIENT_ID` / `DISCORD_CLIENT_SECRET`, and add `http://localhost:3000/api/auth/callback/discord` (and your production equivalent) as a redirect URL.
4. Invite the bot to your server with the `bot` scope.
5. Enable Developer Mode in Discord to copy your server ID (`DISCORD_GUILD_ID`) and admin role ID (`ADMIN_ROLE_ID`).

## Project Structure

```
godfather/
├── backend/                    # Flask API server (see backend/domains/ layout above)
├── frontend/                   # Next.js 15 admin portal
│   ├── app/                     # App Router pages and API routes
│   ├── features/                 # Feature-organized modules (pods, auth, files)
│   ├── components/               # Shared UI components
│   └── lib/                      # Auth and API client helpers
├── cli/                        # Python CLI tool, published to PyPI as godfather-cli
├── docker-images/
│   └── godfather-base/          # Custom RunPod base image with SSH + user isolation
└── nginx/                      # Reverse proxy configuration for production
```

## Usage

### Admin Portal

1. Visit `http://localhost:3000` (or your deployed URL) and sign in with Discord. Only accounts with the configured admin role can access the dashboard.
2. Create a pod from the dashboard: set a name, Docker image (default `theaisocietyasu/godfather-base:latest`), compute type (CPU or GPU), resources, and access control (public or specific users).
3. Manage pods from the dashboard: start, stop, restart, terminate, and view resource usage. Open the file manager for a running pod to browse, upload, or edit files.
4. Public pods are reachable by any member via the CLI. Private pods are restricted to the configured `allowed_users`. Each user gets an isolated workspace at `/workspace/users/<username>`.

### CLI Tool

```bash
# Authenticate via browser
godfather auth login
godfather auth status
godfather auth logout

# Interactive mode
godfather

# List and connect to pods
godfather list
godfather connect
godfather connect <pod-id>
godfather status <pod-id>
```

Once connected to a pod you get your own workspace at `/workspace/users/<your-username>`, a shared folder at `/workspace/shared`, and a themed shell with a few convenience aliases (`workspace`, `shared`, `ll`). Type `exit` to disconnect.

### API

All API requests require the `X-Discord-User-ID` header. Admin-only endpoints additionally verify the caller has the configured Discord admin role.

```bash
curl -X GET http://localhost:5000/api/pods \
  -H "X-Discord-User-ID: your_discord_user_id"
```

#### Create a pod

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

#### Control a pod

```bash
curl -X POST http://localhost:5000/api/pods/{pod_id}/action \
  -H "Content-Type: application/json" \
  -H "X-Discord-User-ID: your_discord_user_id" \
  -d '{"action": "start"}'
```

`action` can be `start`, `stop`, `restart`, or `terminate`.

### Endpoints

**Authentication**

- `POST /api/auth/verify` - verify a Discord user has admin access. Body: `{ "discord_user_id": "string" }`. Returns `{ "is_admin": boolean, "user": {...} }`.

**Pod management**

- `GET /api/pods` - list all pods (admin).
- `POST /api/pods` - create a pod.
- `GET /api/pods/<pod_id>` - get pod details.
- `PUT /api/pods/<pod_id>` - update access control (`is_public`, `allowed_users`).
- `POST /api/pods/<pod_id>/action` - start/stop/restart/terminate.

**CLI access**

- `GET /api/pods/public` - list pods accessible to the requesting user.
- `POST /api/pods/<pod_id>/connect` - get SSH connection info (`host`, `port`, `username`, `is_admin`).
- `GET /api/ssh-key` - get the user's SSH private key.

**File management**

- `GET /api/pods/<pod_id>/files?path=/workspace` - list files.
- `POST /api/pods/<pod_id>/files/upload` - upload a file (multipart form data).

**Discord integration**

- `GET /api/discord/members` - list Discord server members.

All endpoints above require the `X-Discord-User-ID` header unless noted otherwise.

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for building the `godfather-base` Docker image, deploying the backend and frontend, and publishing the CLI to PyPI.

## Development

**Backend:**

```bash
cd backend
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

**Frontend:**

```bash
cd frontend
npm run dev
```

No automated test suite exists yet for the backend or frontend. CI (see `.github/workflows/`) runs import/compile checks and linting on push and pull request.

### Code style

- Python (backend and CLI): PEP 8; `ruff` is used for linting in CI.
- TypeScript/JavaScript (frontend): ESLint (`npm run lint`).

## Troubleshooting

**CLI not found after installation**

```bash
export PATH="$HOME/.local/bin:$PATH"
# add the line above to ~/.bashrc or ~/.zshrc to make it permanent
```

**Authentication fails**

- Verify the Discord bot is in the server and has the Server Members Intent enabled.
- Confirm the Discord user has the configured admin role.
- Verify `DISCORD_GUILD_ID` and `ADMIN_ROLE_ID` are correct.
- Verify `NEXTAUTH_URL` matches the URL you're accessing the frontend from, and that the Discord OAuth redirect URL is registered.

**Can't connect to a pod via CLI**

- Ensure the pod status is `RUNNING`.
- Verify the pod is using the `godfather-base` Docker image with SSH enabled on port 22.
- Confirm you have access (public pod, or you're in `allowed_users`).

**MongoDB connection errors**

- Check MongoDB is running (`mongosh`, or `docker ps` if running it in a container).
- Verify `MONGODB_URI`.
- For Atlas, check IP whitelist and credentials.

**RunPod API errors**

- Verify `RUNPOD_API_KEY` is valid and the account has sufficient credits.
- Ensure the requested GPU type is available.

**Frontend build errors**

```bash
rm -rf node_modules .next
npm install
npm run dev
```

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Make your changes and test them locally.
4. Commit with a clear message and push to your fork.
5. Open a pull request.

## License

MIT - see [LICENSE](LICENSE).

## Acknowledgments

- AI Society ASU, for sponsoring and supporting this project
- RunPod, for GPU infrastructure
- Discord, for OAuth and the community platform

## Support

- Documentation: [Notion](https://www.notion.so/theaisociety/Grandfather-2668867868b480cab87ecfdb4e4a1dbe)
- Issues: [GitHub Issues](https://github.com/theaisocietyasu/godfather/issues)
- Discord: AI Society ASU Discord server
