# Deploying and releasing Godfather

Production is one Linux server running docker compose: `nginx` (ports 80 and 443), `frontend`, `backend`, and `mongo`. Everything is defined in `docker-compose.yml`. The portal is served at admin.ais-asu.com.

## First deploy on a new server

1. Install Docker Engine with the compose plugin (`curl -fsSL https://get.docker.com | sh`).
2. Clone the repo and `cd` into it.
3. `cp .env.example .env` and fill in every value. See the configuration table in the README.
4. Terminate TLS in front of nginx (Cloudflare, the RunPod proxy, or Caddy). `nginx/nginx.conf` serves plain HTTP on port 80 and has no 443 server block yet.
5. Start it:

   ```
   docker compose pull          # released images from GHCR
   docker compose up -d
   ```

   If the images are not reachable (private packages, no release yet), build locally instead: `docker compose up -d --build`.
6. Check it: `docker compose ps` shows backend and frontend as healthy, and `curl http://localhost/health` returns `healthy`.

## Updating to a new release

```
git pull
# set GODFATHER_VERSION in .env to the release, e.g. 1.1.0, or leave it at latest
docker compose pull
docker compose up -d
```

Logs: `docker compose logs -f backend` (or frontend, nginx, mongo). Restart one service with `docker compose restart backend`.

## Upgrading from 1.0.x to 1.1.0

1.1.0 replaces the old login and SSH scheme, which was not secure. Do these steps once:

1. Add `GODFATHER_TOKEN_SECRET` to `.env` (`openssl rand -hex 32`). Make sure `ADMIN_ROLE_ID` is set; it is now required.
2. Publish the new pod image (see below) before recreating pods.
3. Deploy the new frontend and backend as above.
4. Recreate every pod from the portal: note its settings, terminate it, create it again. Old pods trust the old shared key, which every CLI user downloaded, so they stay open to anyone who has it until they are terminated. New pods only accept 12-hour certificates.
5. Tell members to run `pip install -U godfather-cli` and log in again with a token from `/cli-auth`. Old CLI versions and old tokens no longer work.
6. Optional cleanup once no old pods remain: `docker compose exec mongo mongosh Godfather --eval 'db.ssh_keys.deleteOne({key_type: "organization"})'`.

## Releasing

There are four things that ship, each from its own workflow in `.github/workflows/`:

| What | Workflow | Trigger | Publishes to |
| --- | --- | --- | --- |
| Backend and frontend images | `build-and-push-images.yml` | push to `main` touching `backend/` or `frontend/`, a new release, or a `v*.*.*` tag | `ghcr.io/theaisocietyasu/godfather-backend` and `-frontend`, tagged `latest`, short sha, and the version |
| CLI | `publish-cli.yml` | push to `main` changing `cli/pyproject.toml`, or a `v*.*.*` or `cli-v*.*.*` tag | PyPI `godfather-cli` (TestPyPI first) |
| GitHub release | `release.yml` | push to `main` changing `cli/pyproject.toml` or `docs/releases/` | release `v<version>` with notes from `docs/releases/v<version>.md` |
| Pod image | `build-pod-base-image.yml` | push to `main` touching `docker-images/godfather-base/`, or run it by hand from the Actions tab | Docker Hub `theaisocietyasu/godfather-base:latest` |

To cut a release, open one PR that:

1. Bumps `version` in `cli/pyproject.toml` and `__version__` in `cli/godfather_cli/__init__.py`, for example to `1.2.0`.
2. Adds `docs/releases/v1.2.0.md` with the release notes. Without it the notes are generated from merged PRs.

Merge it with CI green. The merge creates the `v1.2.0` tag and release, builds images tagged `1.2.0`, and publishes the CLI. If the release for the current version already exists, nothing new is created and the CLI publish skips the existing version. Any of the three workflows can also be run by hand from the Actions tab.

Pushing a `v*.*.*` tag by hand still works and does the same. Use a `cli-v` tag only to publish the CLI alone.

PyPI never accepts the same version twice. If a publish fails after upload, bump the version and tag again.

## Secrets CI needs

Set these under the repository's Settings, Secrets and variables, Actions:

- `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`: a Docker Hub account with push access to `theaisocietyasu/godfather-base`. Without them the pod image workflow fails at login. The image can also be pushed by hand:

  ```
  cd docker-images/godfather-base
  docker build -t theaisocietyasu/godfather-base:latest .
  docker push theaisocietyasu/godfather-base:latest
  ```

- PyPI publishing uses trusted publishing, so there is no token. The `godfather-cli` project on PyPI (and TestPyPI) must list this repository and `publish-cli.yml` as a trusted publisher.
- GHCR uses the built-in `GITHUB_TOKEN`. For `docker compose pull` to work without logging in, set both GHCR packages to public in the organization's Packages settings, or run `docker login ghcr.io` on the server.
