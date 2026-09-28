# Godfather

Godfather is how the AI Society at ASU hands out GPU time. Officers create and manage RunPod pods from a web portal. Members install a CLI and SSH into the pods they have been given access to, each with a private workspace and no root access.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## How it fits together

```
 officer's browser ──> nginx ──> frontend (Next.js)   Discord login, dashboard, /api/auth/*
                         │
 member's CLI ───────────┴────> backend (Flask)       /api/*: pods, files, SSH certificates
                                   │      │
                                MongoDB  RunPod API ──> pods running the godfather-base image
                                                          ^
 member's CLI ──── ssh (short-lived certificate) ─────────┘
```

There are four pieces, each in its own folder:

| Folder | What it is | Runs where |
| --- | --- | --- |
| `frontend/` | Next.js admin portal. Discord login, pod dashboard, file manager, the `/cli-auth` token page. | docker compose on the Godfather server |
| `backend/` | Flask API. Talks to RunPod, Discord, and MongoDB. Signs SSH certificates. | docker compose on the Godfather server |
| `cli/` | `godfather-cli` on PyPI. Members log in and connect with it. | members' laptops |
| `docker-images/godfather-base/` | The image every pod runs. Sets up sshd, user accounts and workspaces. | each RunPod pod |

`nginx/` is the reverse proxy in front of the frontend and backend. `.github/workflows/` holds CI and the release pipelines.

## How login and access work

Read this before changing anything under `auth` or `ssh`.

1. A person signs in to the portal with Discord (NextAuth, `frontend/lib/auth.ts`).
2. The frontend issues a signed API token for that Discord user (`frontend/app/api/auth/token/route.ts`). The token is HMAC-signed with `GODFATHER_TOKEN_SECRET`, which only the frontend and backend know. Browser tokens last 1 hour. CLI tokens, shown on `/cli-auth`, last 30 days.
3. Every backend request sends `Authorization: Bearer <token>`. The backend checks the signature and expiry (`backend/domains/auth/tokens.py`), then asks Discord whether the user is still in the server and whether they hold `ADMIN_ROLE_ID` (`backend/domains/auth/middleware.py`). Removing someone from the Discord server or the role cuts off access right away.
4. To connect, the CLI makes its own SSH key once (`~/.godfather/ssh/id_ed25519`) and sends the public half to `POST /api/pods/<id>/connect`. The backend checks access and returns a certificate signed by its user CA, valid for 12 hours and for that one pod only.
5. The pod trusts the CA (`TrustedUserCAKeys`) and only accepts certificates naming its own pod ID. A member's certificate forces the command `godfather-login <username>`, which creates their account and drops them into it without sudo. An admin's certificate is plain root.

Private keys never leave the backend. The backend has its own key in root's `authorized_keys` on each pod, used only by the web file manager.

## Where to make common changes

| I want to... | Edit |
| --- | --- |
| Add a backend endpoint | `backend/domains/<area>/routes.py` (HTTP) and `service.py` (logic). Register a new area's blueprint in `backend/app.py`. Protect it with `@require_auth` (admins) or `@require_token` (any server member). |
| Call a new endpoint from the portal | Add a function to `frontend/features/<area>/api.ts` using `apiJson`/`apiFetch` from `frontend/lib/api-client.ts`. They attach the token for you. |
| Change a portal page | `frontend/app/<route>/page.tsx` is a thin wrapper; the UI lives in `frontend/features/<area>/components/`. Shared UI pieces are in `frontend/components/`. |
| Change pod defaults (GPU type, disk, image) | `create_pod` in `backend/domains/pods/routes.py` and the form defaults in `frontend/features/pods/components/CreatePodForm.tsx`. |
| Change who counts as an admin | The `ADMIN_ROLE_ID` env var. The check is `AuthService.verify_discord_admin` in `backend/domains/auth/service.py`. |
| Change what members can do on a pod | Certificate options in `SSHService.sign_user_key` (`backend/domains/ssh/service.py`) and the login script `docker-images/godfather-base/rootfs/usr/local/bin/godfather-login`. |
| Change how long tokens or certificates last | Tokens: `frontend/lib/api-token.ts`. Certificates: `CERT_VALIDITY` in `backend/domains/ssh/service.py`. |
| Change the pod shell, banner, or installed tools | `docker-images/godfather-base/` (Dockerfile, `setup-ssh.sh`, `rootfs/`). Pods pick it up when they are created, so recreate pods after publishing. |
| Add a CLI command | `main()` and `GodfatherCLI` in `cli/godfather_cli/cli.py`. API calls go in `pod_manager.py`, SSH logic in `ssh_connector.py`. |
| Add a setting or secret | Backend: `backend/shared/config.py` (add to `validate()` if required). Frontend: read `process.env` server-side only. Add it to `.env.example`, `docker-compose.yml`, and the table below. |

## Configuration

All settings come from a single `.env` file in the repo root. Copy `.env.example` and fill it in. docker compose passes each value to the service that needs it.

| Variable | Used by | Notes |
| --- | --- | --- |
| `GODFATHER_TOKEN_SECRET` | frontend, backend | Required. At least 32 characters: `openssl rand -hex 32`. Changing it logs everyone out. |
| `RUNPOD_API_KEY` | backend | Required. RunPod console, Settings, API Keys. |
| `DISCORD_BOT_TOKEN` | backend | Required. The bot must be in the server with the Server Members intent enabled. |
| `DISCORD_GUILD_ID` | backend | Required. The Discord server ID. |
| `ADMIN_ROLE_ID` | backend | Required. Members with this role are admins. |
| `MONGODB_URI` | backend | Defaults to the compose `mongo` container. |
| `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET` | frontend | Discord OAuth app. Add `<NEXTAUTH_URL>/api/auth/callback/discord` as a redirect. |
| `NEXTAUTH_SECRET` | frontend | Required. `openssl rand -hex 32`. |
| `NEXTAUTH_URL` | frontend | Public URL of the portal. |
| `GODFATHER_VERSION` | docker compose | Image tag to pull. Defaults to `latest`. |
| `LOG_LEVEL` | backend | Defaults to `INFO`. |

The backend refuses to start if a required value is missing.

## Running it locally

You need Docker, Python 3.11+, and Node 22.

```bash
cp .env.example .env        # fill in the values
docker compose up -d --build
```

The portal is then at http://localhost. To work on one piece with live reload:

```bash
# backend, on :5000
cd backend && pip install -r requirements-dev.txt && python app.py

# frontend, on :3000 (sends /api calls to BACKEND_URL, default http://localhost:5000)
cd frontend && npm install && npm run dev

# CLI against a local stack
cd cli && pip install -e . && godfather --api-url http://localhost list
```

Pods are real RunPod machines and cost money. Terminate test pods when you are done.

## Checks

CI runs these on every pull request. Run them before pushing.

```bash
cd backend && ruff check . && pytest -q
cd cli && pytest -q tests
cd frontend && npm run lint && npm run build
```

## Deploying and releasing

See [DEPLOYMENT.md](DEPLOYMENT.md). It covers the server setup, upgrades, publishing the CLI and pod image, and the secrets CI needs.

## Troubleshooting

- CLI says the token is invalid or expired: open `<portal>/cli-auth`, copy a new token, run `godfather auth`.
- CLI says SSH could not log in: the pod was created before 1.1.0 or with another image. Recreate it from the portal.
- Portal shows "Admin role required": the Discord account does not have `ADMIN_ROLE_ID`, or the bot cannot see server members.
- Web file manager cannot connect: the pod must run `theaisocietyasu/godfather-base` and be in the RUNNING state.
- RunPod errors on create: check account credit and that the GPU type is available in the chosen cloud.

## License

MIT. See [LICENSE](LICENSE).
