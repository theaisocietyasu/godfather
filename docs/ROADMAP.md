# Godfather roadmap

What to build next and in what order. Each phase ends with something students can use. Items are small enough for one PR unless marked otherwise. ARCHITECTURE.md explains the current system and its known limits; most items here answer one of those limits.

Status as of v1.1.0 (September 2026): the code is released, but the 1.1.0 server deploy and the new pod image are not done yet.

## Phase 0: get 1.1.0 running

Nothing else matters until students can connect.

- [ ] Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` repo secrets and publish `godfather-base`, or push it by hand.
- [ ] Deploy 1.1.0 on the server: set `GODFATHER_TOKEN_SECRET` and `ADMIN_ROLE_ID`, pull, restart (DEPLOYMENT.md).
- [ ] Recreate every pod made before 1.1.0. They still trust the old shared key.
- [ ] Test end to end on a real RunPod pod: a member and an admin each connect, a member cannot read another member's workspace, the file manager works.
- [ ] Serve HTTPS for `admin.ais-asu.com`. `nginx.conf` only listens on 80 today: add a 443 server block using `nginx/ssl/`, or put Caddy or a Cloudflare tunnel in front.
- [ ] Make both GHCR packages public so the server pulls without logging in.
- [ ] Nightly `mongodump` of the `Godfather` database to storage off the server. Losing `ssh_keys` means recreating every pod.
- [ ] Write a one-page runbook for officers: create a pod for a workshop, share it, shut it down.

Exit: a student with only a Discord account runs `pip install godfather-cli`, `godfather auth`, `godfather connect` and gets a shell on a GPU.

## Phase 1: better CLI

The CLI is what students see most. Today it is an interactive menu wrapped around `ssh`.

- [ ] Direct commands that work without the menu and in scripts: `godfather ls`, `godfather ssh <pod-name>`, `godfather whoami`. Accept pod names, not only ids, and support tab completion.
- [ ] `godfather login` opens the browser to `/cli-auth` and receives the token through a localhost callback or a device code, so students do not copy and paste tokens.
- [ ] `godfather cp` and `godfather sync` for moving files to and from a workspace (scp or rsync with the same certificate).
- [ ] `godfather code <pod>` writes an entry to `~/.ssh/config` and opens VS Code or Cursor Remote-SSH on the workspace. Most students want an editor, not a bare shell.
- [ ] `godfather jupyter <pod>` starts JupyterLab in the member's workspace and forwards the port to localhost.
- [ ] Refresh the certificate automatically when it is close to expiring, instead of failing at the next connect.
- [ ] Verify host keys. Sign pod host keys with a host CA at boot and add a `@cert-authority` line locally, so `StrictHostKeyChecking=no` can go.
- [ ] Clear errors for common failures: pod stopped, not in the Discord server, token expired, pod still booting. Each one says what to do next.
- [ ] Recommend `pipx install godfather-cli` or `uv tool install godfather-cli` in the docs; drop Python 3.8 once RunPod and ASU lab machines allow it.
- [ ] Windows: test on PowerShell with the built-in OpenSSH client and fix path and permission issues on the key files.
- [ ] Record a short asciinema or GIF of the connect flow for the README.

## Phase 2: students can serve themselves

The portal is admin-only, so every pod needs an officer. That does not scale past a few workshops.

- [ ] Member view in the portal: pods I can use, their status, and a "Connect" panel with the exact CLI command.
- [ ] Requests: a member asks for a pod (GPU type, hours, reason); an admin approves in the portal or with a Discord button, and the pod is created on approval.
- [ ] Time limits: each pod gets an expiry. A worker stops it at expiry and terminates it after a grace period. Owners can extend once.
- [ ] Idle shutdown: stop a pod when GPU use and SSH sessions have been zero for N minutes. Read GPU use from `nvidia-smi` through a small agent on the pod or from RunPod's metrics.
- [ ] Budget: a monthly spend limit in config, a live spend total on the dashboard from RunPod billing, and new pods refused when the limit is reached.
- [ ] Discord bot: `/godfather status`, `/godfather request`, and DMs when a pod is about to expire. Reuse the bot token the backend already has.
- [ ] Workshop mode: create N identical pods or one large shared pod for an event, add everyone with a given Discord role, and tear it all down with one click afterwards.

## Phase 3: reliable and observable

- [ ] Background worker (a second backend process or an APScheduler job) for expiry, idle checks, and syncing RunPod state into Mongo, so page loads stop calling RunPod.
- [ ] Cache Discord membership and roles for a short time (for example 60 seconds) to cut Discord API calls and avoid rate limits.
- [ ] Rate-limit `/api/pods/<id>/connect` and `/api/auth/token` per user.
- [ ] Audit log collection: who created, stopped, shared or terminated a pod, who connected where and when (the certificate key id already names the user). Show it on the pod page.
- [ ] Usage stats page: GPU hours per month, per pod, unique students served. This is the number to show sponsors and the club.
- [ ] Error reporting (Sentry or GlitchTip) for backend and frontend, and uptime checks on `/health`.
- [ ] Revoke access on the pod when a member is removed: keep a revoked key-id list the pod pulls, or drop certificate validity to 1 hour.
- [ ] Page through Discord members past 1000.
- [ ] Integration tests that run the backend against a fake RunPod and a real sshd in CI, like the manual test done for 1.1.0.
- [ ] Type-check the backend (mypy or pyright) and pin the ruff rule set wider over time.

## Phase 4: more useful pods

- [ ] Update the base image to a current CUDA and Ubuntu, and publish variants: `godfather-base` (plain), `godfather-pytorch`, `godfather-llm` (vLLM, transformers, a Hugging Face cache on the volume).
- [ ] Per-user disk quotas in `/workspace/users`, and a size readout at login.
- [ ] Persistent workspaces across pods: keep member folders on a RunPod network volume so a student's files survive when a pod is recreated.
- [ ] Pre-download common models and datasets to a shared read-only cache on the volume.
- [ ] Optional per-member GPU sharing limits (MIG on A100 or H100 where available, or time slots).
- [ ] Templates in the create form: "Intro workshop (CPU)", "Fine-tuning (A100)", "Hackathon team (A6000)".

## Phase 5: growth

- [ ] Public status page: how many GPUs are free right now and how to get access. Link it from the club website and Discord.
- [ ] Getting-started guide for students with no SSH experience, and a workshop slide deck that uses Godfather live.
- [ ] Credits: apply for RunPod, NVIDIA, or cloud education credits and track them next to the budget in Phase 2.
- [ ] Let other ASU clubs use it: per-club Discord server and role config, separate budgets, one deployment.
- [ ] Contributor setup: `docker compose up` with a mock RunPod backend so new maintainers can run the full stack without a RunPod key (the screenshot mock is a starting point).
- [ ] Good-first-issue labels on Phase 1 and Phase 3 items for new contributors.

## Later, by decision only

- Merge into Bedrock as its compute module. Worth doing once Bedrock has auth and a module system that fits; until then Godfather stays standalone.
- Support providers other than RunPod (Lambda, Vast.ai, ASU's own cluster) behind one provider interface.
- A browser terminal (xterm.js over a websocket to the pod) for students who cannot install anything.
