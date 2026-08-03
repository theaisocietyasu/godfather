# godfather-base

Custom RunPod base image used for all pods created through Godfather. It adds SSH access, per-user workspace isolation, and a themed shell, on top of `runpod/base:0.4.0-cuda11.8.0`.

## What it does

`setup-ssh.sh` runs as the container entrypoint and:

1. Starts `sshd`.
2. If `GODFATHER_SSH_PUBLIC_KEY` is set, appends it to `/root/.ssh/authorized_keys`. The backend sets this env var when creating a pod (`backend/domains/pods/service.py`) so the platform's SSH key can connect as root.
3. Creates `/workspace/users` (per-user workspaces) and `/workspace/shared` (shared collaboration folder, world-writable).
4. Installs a custom MOTD.
5. Installs `/usr/local/bin/godfather-user-setup.sh`, which is invoked over SSH on every connection (see `cli/godfather_cli/ssh_connector.py`) as:

   ```
   SCRIPT=$(/usr/local/bin/godfather-user-setup.sh <username> <is_admin>) && bash $SCRIPT
   ```

   `godfather-user-setup.sh` creates the user's workspace directory and, depending on `is_admin`:
   - **Admin**: writes and returns a wrapper script that drops into a root bash shell in the user's workspace, with an admin-themed prompt.
   - **Non-admin**: creates (if needed) a locked, sudo-less Linux user `godfather_<username>`, owns their workspace, and returns a wrapper script that `su`s into that account with a restricted-themed prompt. Restricted users cannot use sudo and are not added to `sudo`/`admin`/`wheel` groups.

Both wrapper scripts are written to `/tmp` and executed once per connection, so the shell setup happens fresh each time a user connects rather than being baked into the image at build time.

## Building and publishing

```bash
cd docker-images/godfather-base
docker build -t theaisocietyasu/godfather-base:latest .
docker push theaisocietyasu/godfather-base:latest
```

See the root [`DEPLOYMENT.md`](../../DEPLOYMENT.md) for the full release process, including tagging and updating the default image reference used when creating pods.
