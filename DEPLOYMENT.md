# Deployment

Godfather runs as four containers behind nginx: `backend` (Flask/gunicorn),
`frontend` (Next.js), `mongo`, and `nginx` itself terminating traffic on
80/443. Everything is defined in `docker-compose.yml` at the repo root.

## Prerequisites

- Docker Engine and the Docker Compose plugin (`docker compose version`) on
  the host. If you're deploying on a RunPod VM, install Docker there first -
  RunPod's stock images don't ship it by default.
- A Discord application (bot token + OAuth client) and a RunPod API key,
  same as before - see `.env.example` for the full list.
- A MongoDB instance. The compose file includes a `mongo` container with a
  named volume, which is enough for a single-host deployment. Point
  `MONGODB_URI` at an external cluster instead if you need one.
- TLS certificates if you're serving HTTPS directly from this nginx
  container (see the TLS section below).

## First deploy

1. Clone the repo onto the host and `cd` into it.
2. Copy the env template and fill in real values:

   ```
   cp .env.example .env
   ```

   Fill in `RUNPOD_API_KEY`, `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`,
   `ADMIN_ROLE_ID`, `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`,
   `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, and
   `NEXT_PUBLIC_APP_URL`. Leave `MONGODB_URI` as-is unless you're using an
   external database.

3. Build and start everything:

   ```
   docker compose up -d --build
   ```

   This builds the backend and frontend images locally from source and
   starts all four services. First build takes a few minutes (Next.js
   build + Python wheel build).

4. Confirm it's healthy:

   ```
   docker compose ps
   curl http://localhost/health
   ```

   `docker compose ps` should show `backend` and `frontend` as `healthy`
   once their healthchecks pass.

## Updating

Once CI has published images (see below), you don't need to rebuild locally.
Pull the latest tags and recreate the containers:

```
docker compose pull
docker compose up -d
```

If you're still building locally instead of pulling from the registry, use
`docker compose up -d --build` again - compose only rebuilds layers that
changed.

## Logs and troubleshooting

```
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f nginx
docker compose logs -f mongo
```

Drop `-f` for a one-shot dump. `docker compose ps` shows container and
healthcheck status. `docker compose restart <service>` restarts a single
service without touching the others.

## TLS

`nginx/nginx.conf` is mounted read-only into the nginx container along with
`nginx/ssl/`. Place your certificate and key there as `cert.pem` and
`key.pem` (these paths are gitignored - never commit real certs). If you're
running behind a proxy that already terminates TLS (e.g. Cloudflare or
RunPod's own proxy domain), you can serve plain HTTP from nginx and let the
upstream proxy handle certificates instead; the existing `server_name`
block already accepts both a custom domain and `*.proxy.runpod.net`.

## CI-published images

Two workflows build and push images automatically; you don't need to run
either by hand:

- `.github/workflows/build-and-push-images.yml` builds `backend/` and
  `frontend/` on every push to `main` that touches those directories (or the
  compose file), and on version tags. Images land in GitHub Container
  Registry as `ghcr.io/theaisocietyasu/godfather-backend` and
  `ghcr.io/theaisocietyasu/godfather-frontend`, tagged with both the git
  short sha and `latest`.
- `.github/workflows/build-pod-base-image.yml` builds the GPU pod image
  members SSH into (`docker-images/godfather-base/`) and pushes it to
  Docker Hub as `theaisocietyasu/godfather-base:latest` and
  `:<short-sha>`. It needs `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
  configured as repository secrets in GitHub settings; it does nothing
  useful without them.

To run against the CI-built images instead of building locally, either
point `docker-compose.yml`'s `build:` blocks at `image:` references for
those tags, or pull and re-tag them manually before `docker compose up -d`.

The CLI has its own release flow and is unrelated to this: it publishes to
PyPI from `.github/workflows/publish-cli.yml` on tags matching `cli-v*.*.*`.
