# Godfather architecture

This document describes how Godfather works as of v1.1.0: the parts, the data each one holds, the requests between them, and the rules the code depends on. The README has the short version and the "where do I edit" table. Read this before changing auth, SSH, or the pod image.

## Goal and constraints

Godfather hands out AI Society at ASU compute on RunPod to students in the club's Discord server. The design follows from four constraints:

- Students have no cloud account and no payment method. The club's RunPod key is the only one, and it stays on the server.
- Membership lives in Discord. There is no separate user database to keep in sync; the Discord server and one admin role decide who gets in.
- Pods are shared. Several students can use one GPU pod, so each needs a private workspace and must not be able to read or break someone else's.
- The club has few maintainers. Everything runs from one docker compose file on one server, and releases are automatic.

## Parts

```
 officer's browser ──> nginx ──> frontend (Next.js)   Discord login, dashboard, /api/auth/*
                         │
 member's CLI ───────────┴────> backend (Flask)       /api/*: pods, files, SSH certificates
                                   │      │     │
                                MongoDB  RunPod  Discord API
                                           │
                                           └──> pods running godfather-base
                                                   ^
 member's CLI ──── ssh with a short-lived certificate ┘
```

| Part | Code | Runs | Holds |
| --- | --- | --- | --- |
| nginx | `nginx/nginx.conf` | compose on the server, serves HTTP on 80 | nothing |
| frontend | `frontend/` | compose, Next.js standalone on :3000 | NextAuth session cookie, `GODFATHER_TOKEN_SECRET` |
| backend | `backend/` | compose, gunicorn on :5000 | RunPod key, Discord bot token, `GODFATHER_TOKEN_SECRET`, SSH private keys (in Mongo) |
| MongoDB | `mongo:7` in `docker-compose.yml` | compose, internal only | pod metadata, SSH key pairs |
| CLI | `cli/`, `godfather-cli` on PyPI | students' laptops | a 30-day API token, a local SSH key, the latest certificate |
| pod image | `docker-images/godfather-base/` | every RunPod pod | the backend public key, the user CA public key |

### nginx

Serves plain HTTP on port 80. Compose also maps 443 and mounts `nginx/ssl/`, but `nginx.conf` has no TLS server block, so TLS has to be terminated in front (Cloudflare or the RunPod proxy). Routes by path. `/api/auth/*` goes to the frontend (NextAuth and the token endpoint). Every other `/api/*` goes to the backend. Everything else goes to the frontend. It accepts `admin.ais-asu.com` and RunPod proxy hostnames. It adds only the standard forwarding headers (`X-Forwarded-*`, `X-Real-IP`); the backend takes identity only from the bearer token.

### frontend

Next.js 15 app router with NextAuth v5 and the Discord provider.

- `lib/auth.ts` configures Discord OAuth with scopes `identify email guilds guilds.members.read` and copies the Discord id, username and avatar into the session JWT.
- `middleware.ts` redirects anyone without a session away from everything except `/`, `/cli-auth`, `/api/auth/*`, `/api/pods/public` and `/api/health`.
- `app/api/auth/token/route.ts` turns a session into a backend API token (see Tokens below). It is the only place tokens are minted.
- `lib/api-client.ts` caches the browser token, attaches it as `Authorization: Bearer`, and retries once with a fresh token on 401.
- Pages are thin. `app/<route>/page.tsx` renders a component from `features/<area>/components/`. Shared UI is in `components/`.

Pages:

| Route | Component | Who |
| --- | --- | --- |
| `/` | `features/auth/components/LandingPage.tsx` | anyone; after login, admins go to `/dashboard` and members are sent to `/cli-auth` |
| `/dashboard` | `features/pods/components/DashboardView.tsx` | admins |
| `/dashboard/create-pod` | `features/pods/components/CreatePodForm.tsx` | admins |
| `/dashboard/pods/[id]` | `features/pods/components/PodDetail.tsx`, `features/files/components/FileManager.tsx` | admins |
| `/cli-auth` | `features/auth/components/CliAuthView.tsx` | any member; shows a 30-day CLI token |

The frontend never talks to RunPod or Mongo. In development `next.config.ts` rewrites unhandled `/api/*` calls to `BACKEND_URL`; in production nginx does that.

### backend

Flask, one blueprint per area under `backend/domains/<area>/`, each with `routes.py` (HTTP) and `service.py` (logic). `app.py` validates config at import time, so gunicorn refuses to start with a missing secret.

| Area | Endpoints | Guard |
| --- | --- | --- |
| auth | `GET /api/me` | token |
| pods | `GET/POST /api/pods`, `GET/PUT /api/pods/<id>`, `POST /api/pods/<id>/action` | admin |
| pods | `GET /api/pods/public`, `POST /api/pods/<id>/connect` | token (any member) |
| files | `/api/pods/<id>/files/*` (list, upload, download, read, write, mkdir, rename, copy, delete, search) | admin |
| discord | `GET /api/discord/members` | admin |
| - | `GET /health` | none |

`require_token` (in `domains/auth/middleware.py`) verifies the bearer token and checks that the Discord user is still in the server. `require_auth` does the same and also requires `ADMIN_ROLE_ID`. Both ask Discord live on every request; there is no membership cache.

`shared/config.py` reads env vars. `shared/database.py` opens one Mongo client on the `Godfather` database.

### MongoDB

Two collections are in use.

`pods`, one document per pod Godfather created:

| Field | Meaning |
| --- | --- |
| `runpod_id` | RunPod pod id, the join key with RunPod |
| `name` | display name |
| `is_public` | any member may connect |
| `allowed_users` | Discord ids that may connect when not public |
| `custom_config` | the create request as sent to RunPod |
| `ssh_public_key` | backend public key placed on the pod |
| `created_by`, `created_at` | audit fields |

`ssh_keys`, one document per key pair, keyed by `key_type`:

| `key_type` | Use |
| --- | --- |
| `backend` | root login for the web file manager; public half goes into `authorized_keys` on each pod |
| `user_ca` | signs CLI user certificates; public half goes into `TrustedUserCAKeys` on each pod |
| `organization` | pre-1.1.0 shared key; read only as a file manager fallback for old pods |

Key pairs are created on first use (`SSHService._get_or_create_keypair`). Losing the `ssh_keys` collection means every existing pod has to be recreated. `users` is declared in `shared/database.py` but unused.

RunPod is the source of truth for pod state (status, machine, ports). Mongo is the source of truth for access (who may connect). `PodService.get_all_pods` lists RunPod pods and joins Mongo metadata onto them; a RunPod pod with no Mongo record shows as private with no allowed users.

### CLI

Python 3.8+, `requests` and `rich`. Entry point `godfather` (`cli/godfather_cli/cli.py`) with subcommands `list`, `connect`, `status`, `logout`, `auth`, `update`, or an interactive menu with none.

- `auth.py` stores the API base and token in `~/.godfather/config.json` (mode 0600) and checks it with `GET /api/me`.
- `pod_manager.py` lists pods from `GET /api/pods/public` and requests connection details.
- `ssh_connector.py` creates `~/.godfather/ssh/id_ed25519` once, saves each certificate beside it, and runs the system `ssh` client.
- `update_checker.py` compares the installed version with PyPI and can self-update with pip.

The API base comes from `GODFATHER_API_URL`, then the saved config, then `https://admin.ais-asu.com`.

### Pod image

`theaisocietyasu/godfather-base`, built from `runpod/base` with CUDA 11.8, plus sshd and common tools. At boot `setup-ssh.sh`:

1. Adds `GODFATHER_SSH_PUBLIC_KEY` to root's `authorized_keys`.
2. Writes `GODFATHER_SSH_CA_PUBLIC_KEY` to `/etc/ssh/godfather_user_ca.pub`.
3. Writes the principal `gf-$RUNPOD_POD_ID` to `/etc/ssh/godfather_principals/root`.
4. Starts sshd with `rootfs/etc/ssh/sshd_config.d/godfather.conf`: no passwords, root by key or certificate only, CA trusted, principals file per user.
5. Creates `/workspace/users` and `/workspace/shared` (sticky, world-writable).

`rootfs/usr/local/bin/godfather-login` runs on every CLI login. For a member it creates the Unix account `godfather_<username>` with a locked password, makes `/workspace/users/<username>` owned by that account with mode 700, and switches to it with `su`. For an admin (`--admin`) it stays root and opens the same workspace.

Pods are configured only through env vars set at creation, so a change to the image or the keys reaches a pod only when the pod is recreated.

## Flows

### Tokens

Format: `gf1.<base64url(json)>.<base64url(hmac_sha256(secret, "gf1." + body))>`, with body `{"sub": "<discord id>", "exp": <unix seconds>}`.

- Minted by `frontend/lib/api-token.ts`, verified by `backend/domains/auth/tokens.py`. Both use `GODFATHER_TOKEN_SECRET`, at least 32 characters.
- Browser tokens last 1 hour, CLI tokens 30 days. There is no revocation list; removing a user from the Discord server or the admin role is the revocation, because every request re-checks Discord.

### Admin signs in and creates a pod

1. Browser signs in with Discord; NextAuth stores the Discord id in the session.
2. Browser gets a 1-hour token from `/api/auth/token`.
3. Browser calls `GET /api/me`; the backend confirms membership and admin role.
4. Create form sends `POST /api/pods` with image, GPU or CPU instance, disk, visibility and allowed users.
5. Backend loads (or creates) the backend key and user CA, adds `GODFATHER_SSH_PUBLIC_KEY`, `GODFATHER_SSH_CA_PUBLIC_KEY` and `GODFATHER_SETUP` to the pod env, and calls `runpod.create_pod`. For CPU pods it passes `gpu_type_id=None` and `instance_id`.
6. Backend stores the Mongo `pods` record.

### Member connects from the CLI

1. Member opens `/cli-auth`, signs in with Discord, copies a 30-day token into `godfather auth`.
2. `godfather list` calls `GET /api/pods/public`: pods that are public or list the member, filtered to those RunPod reports as RUNNING.
3. `godfather connect` ensures the local key pair and sends its public half to `POST /api/pods/<id>/connect`.
4. Backend re-checks membership, checks pod access (admins skip this), reads the pod's SSH host and port from RunPod, and signs the key with `ssh-keygen -s`:
   - key id `discord:<id>:<username>`, principal `gf-<pod id>`, validity `-5m:+12h`
   - members: `permit-pty`, `permit-port-forwarding`, `force-command=/usr/local/bin/godfather-login <username>`
   - admins: `permit-pty`, `permit-port-forwarding`, `permit-agent-forwarding`, no forced command
5. CLI saves the certificate and runs `ssh -i <key> -o CertificateFile=<cert> root@<host> -p <port>`.
6. sshd accepts the certificate only if it is signed by the CA, unexpired, and names this pod's principal. The forced command puts members into their own account.

### Admin uses the web file manager

The backend writes the `backend` private key to a temp file, opens SFTP to the pod as root with paramiko (`domains/files/service.py`), runs the operation, and deletes the temp file. For pods created before 1.1.0 it falls back to the legacy `organization` key.

## Invariants

Changes that break one of these are security bugs.

- Private keys (`backend`, `user_ca`) never leave the backend. The API returns only certificates and public keys.
- The only identity the backend trusts is a valid `gf1` token. No header, query parameter or body field can set the user.
- Every guarded request re-checks Discord membership. Admin status comes from Discord, never from Mongo or the token.
- A certificate is valid for one pod (its principal) and at most 12 hours.
- Member certificates always carry the forced login command. Only admin certificates are unrestricted.
- Usernames reaching the pod pass `safe_username` in the backend and the regex in `godfather-login`; they become Unix account names and paths.
- `GODFATHER_TOKEN_SECRET` is the same on frontend and backend and is at least 32 characters. The backend refuses to start otherwise.

## Deployment

One server runs `docker-compose.yml`: `mongo`, `backend`, `frontend`, `nginx`. The backend and frontend images come from GHCR (`ghcr.io/theaisocietyasu/godfather-backend` and `-frontend`), tagged `latest`, short sha, and the release version; `GODFATHER_VERSION` in `.env` picks one. Mongo data lives in the `mongo-data` volume. DEPLOYMENT.md has the steps.

CI (`.github/workflows/`):

| Workflow | Does |
| --- | --- |
| `ci-backend.yml` | ruff and pytest for `backend/` |
| `ci-frontend.yml` | lint and build for `frontend/` |
| `ci-cli.yml` | pytest for `cli/` |
| `build-and-push-images.yml` | backend and frontend images to GHCR |
| `build-pod-base-image.yml` | pod image to Docker Hub; needs `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` |
| `release.yml` | on a version bump merged to main, creates the GitHub release and versioned images |
| `publish-cli.yml` | CLI to TestPyPI then PyPI, by trusted publishing |

## Known limits

These are facts about the current code, not plans. The roadmap covers what to do about them.

- The web portal is admin-only. Members cannot see or start pods from a browser.
- Nothing stops idle pods or caps spend. A forgotten GPU pod costs money until an admin terminates it.
- Every guarded request makes one or more Discord API calls, and `GET /api/pods` calls RunPod each time. There is no caching or rate limiting.
- The CLI disables host key checking (`StrictHostKeyChecking=no`), so it does not detect a spoofed pod address.
- There is no audit log beyond application logs. Mongo records who created a pod, not who connected or what an admin did.
- Members share the pod's GPU and disk with no quotas. `/workspace/shared` is writable by everyone.
- The file manager works as root, so admins can see every member's workspace.
- `GET /api/discord/members` reads at most 1000 members.
- Access changes (public, allowed users) apply at the next connect. An already-issued certificate stays valid until it expires.
