# Architecture

Godfather is a CLI and a pod image. Platform's `godfather` module manages the pods.

## CLI (`cli/godfather_cli`)

- `cli.py`: argument parsing, the interactive menu, and the server and org. A flag or env var wins, then the values saved at the last login, then `DEFAULT_API_URL` and `DEFAULT_ORG`.
- `auth.py`: sign-in. When `POST .../cli/token` with an empty body answers 400, it opens `<api>/api/compute/<org>/cli/login` with `port`, `state` and an S256 `code_challenge`, takes the code from the loopback callback, and posts it with the verifier to `.../cli/token`. Otherwise, or with `--paste`, it takes the pasted `plat_` token. Both check the token with `GET .../me/pods`.
- `login_server.py`: a one-request HTTP server on `127.0.0.1` (port from the OS) that accepts `GET /callback` with the right `state`. Stores `token`, `api_url` and `org` in `~/.godfather/config.json` (mode 600). A token counts only for the server and org it was issued for.
- `pod_manager.py`: `GET .../me/pods` and `POST .../me/pods/<id>/connect` with `{"public_key"}`. The response's `ssh_info` has `host`, `port`, `username`, `user_folder`, `is_admin` and `certificate`.
- `ssh_connector.py`: makes the ed25519 key once, saves the certificate, and runs the system `ssh`. Officers run `godfather-login --admin <user>` as the remote command.
- `update_checker.py`: compares the installed version with PyPI on the interactive menu only.

## Pod image (`docker-images/godfather-base`)

Built on `runpod/base`. At start `setup-ssh.sh` reads `GODFATHER_SSH_PUBLIC_KEY` (the platform's key for the officer file manager) and `GODFATHER_SSH_CA_PUBLIC_KEY` (the org's user CA), configures sshd to trust the CA for principal `gf-<pod id>`, and creates `/workspace/users` and `/workspace/shared`. `/workspace/users` is mode 711. `godfather-login` creates `godfather_<username>` with a private folder and home (mode 700) and switches to it with umask 077. The image has no sudo. The label `com.ais-asu.godfather.base-version` and the file `/etc/godfather/version` hold the image version from `VERSION`.

## Platform side

The `godfather` module stores pods per org, signs certificates, runs the officer file manager over SFTP, and starts and stops pods for scheduled sessions. See `docs/modules/godfather.md` in the Platform repo.
