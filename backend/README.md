# backend

Flask API for Godfather. The root README explains how auth and SSH access work and where to make common changes; this file is the map of this folder.

## Layout

- `app.py`: creates the app, registers each area's blueprint, serves `/health`. Validates required settings on import, so it will not start without them.
- `domains/<area>/routes.py`: HTTP routes for that area (a Flask blueprint).
- `domains/<area>/service.py`: logic and external calls for that area.
- `shared/config.py`: settings read from the environment (the repo root `.env`).
- `shared/database.py`: MongoDB client and collections (`pods`, `users`, `ssh_keys`).
- `shared/logger.py`: logging. Use `get_logger(__name__)`, not `print`.
- `tests/`: pytest. `conftest.py` sets fake settings, so tests need no real secrets or database.

| Area | Routes | What it does |
| --- | --- | --- |
| `auth` | `GET /api/me` | Token checks (`tokens.py`), the `require_auth` and `require_token` decorators (`middleware.py`), live Discord role checks (`service.py`). |
| `pods` | `/api/pods`, `/api/pods/<id>`, `/action`, `/public`, `/connect` | Create, list, start, stop, terminate pods on RunPod, access lists in MongoDB, SSH certificates for the CLI. |
| `files` | `/api/pods/<id>/files/*` | Web file manager over SFTP as root, using the backend key. |
| `ssh` | none | Backend key, user CA, certificate signing. Needs `ssh-keygen` (installed in the Docker image). |
| `discord` | `GET /api/discord/members` | Server member list for the access picker. |

## Rules

- Every route except `/health` needs `@require_auth` (admins only) or `@require_token` (any Discord server member). Both read the bearer token; never trust a user ID from a header or request body.
- Keep private keys inside the backend. Only public keys and certificates go out.

## Running

```
pip install -r requirements-dev.txt
python app.py        # http://localhost:5000, needs the repo root .env
ruff check . && pytest -q
```
