# Architecture

Godfather is a CLI and a pod image. Pod management lives in the AI Society platform's compute module.

## CLI (`cli/godfather_cli`)

- `cli.py`: argument parsing, the interactive menu, and the server and org. A flag or env var wins, then the values saved at the last login, then `DEFAULT_API_URL` and `DEFAULT_ORG`.
- `auth.py`: opens `<api>/api/compute/<org>/cli/login`, takes the pasted `plat_` token, and checks it with `GET .../me/pods`. Stores `token`, `api_url` and `org` in `~/.godfather/config.json` (mode 600). A token counts only for the server and org it was issued for.
- `pod_manager.py`: `GET .../me/pods` and `POST .../me/pods/<id>/connect` with `{"public_key"}`. The response's `ssh_info` has `host`, `port`, `username`, `user_folder`, `is_admin` and `certificate`.
- `ssh_connector.py`: makes the ed25519 key once, saves the certificate, and runs the system `ssh`. Officers run `godfather-login --admin <user>` as the remote command.
- `update_checker.py`: compares the installed version with PyPI on the interactive menu only.

## Pod image (`docker-images/godfather-base`)

Built on `runpod/base`. At start `setup-ssh.sh` reads `GODFATHER_SSH_PUBLIC_KEY` (the platform's key for the officer file manager) and `GODFATHER_SSH_CA_PUBLIC_KEY` (the org's user CA), configures sshd to trust the CA for principal `gf-<pod id>`, and creates `/workspace/users` and `/workspace/shared`. `godfather-login` creates `godfather_<username>` with a private folder (mode 700) and switches to it.

## Platform side

The compute module stores pods per org, signs certificates, runs the officer file manager over SFTP, and starts and stops pods for scheduled sessions. See `docs/compute.md` in the platform repo.
