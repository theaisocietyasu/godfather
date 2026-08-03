# backend

Flask API server for Godfather. See the root [`README.md`](../README.md) for setup, environment variables, and the full API reference. This file covers backend-specific structure that isn't obvious from the code layout alone.

## Layout

- `app.py` - creates the Flask app, registers each domain's blueprint, and defines `/health`. Config validation (`settings.validate()`, which requires `RUNPOD_API_KEY`, `DISCORD_BOT_TOKEN`, and `DISCORD_GUILD_ID`) only runs when `app.py` is executed directly (`python app.py`), not on import - so importing `app` for tooling/CI doesn't require those secrets to be set.
- `domains/<name>/routes.py` - Flask blueprint with the HTTP routes for that domain.
- `domains/<name>/service.py` - business logic and external API calls (RunPod, Discord, SSH/SFTP) for that domain.
- `shared/config.py` - `Settings`, populated from environment variables (loaded from a `.env` file in the repo root).
- `shared/database.py` - the `pymongo.MongoClient` and collections (`pods`, `users`, `ssh_keys`) shared across domains. The client is created at import time but doesn't connect until first used.
- `shared/logger.py` - logging setup, shared by all domains via `get_logger(__name__)`.

## Running

```bash
pip install -r requirements.txt
python app.py
```

Runs on `http://localhost:5000`. Set `FLASK_DEBUG=1` for auto-reload during development.
