# godfather-base

The image every Godfather pod runs, built on `runpod/base`. It runs sshd, trusts the backend's user CA, and gives each member a private account and workspace.

## Files

- `Dockerfile`: installs tools and openssh-server, copies `rootfs/` into the image, sets `setup-ssh.sh` as the entrypoint.
- `setup-ssh.sh`: runs when the pod starts. It reads three environment variables:
  - `GODFATHER_SSH_PUBLIC_KEY`: the backend's key, added to root's `authorized_keys` for the web file manager.
  - `GODFATHER_SSH_CA_PUBLIC_KEY`: the user CA, written to `/etc/ssh/godfather_user_ca.pub`.
  - `RUNPOD_POD_ID`: set by RunPod. Root accepts only certificates with the principal `gf-<pod id>`, so a certificate for one pod does not open another.
  The backend sets the first two when it creates the pod. Then it starts sshd, creates `/workspace/users` and `/workspace/shared`, and writes the login banner.
- `rootfs/etc/ssh/sshd_config.d/godfather.conf`: key-only root login, CA trust, principals file.
- `rootfs/usr/local/bin/godfather-login`: runs on every CLI connection. Members reach it as the forced command in their certificate; it creates `godfather_<username>` without sudo, gives them `/workspace/users/<username>` (mode 700), and switches to that account. Admins run it with `--admin` and stay root.
- `rootfs/etc/godfather/*.bashrc`: prompt and aliases (`workspace`, `shared`, `ll`) for member and admin shells.

## Changing it

Edit the files above, merge to `main`, and the `build-pod-base-image` workflow pushes `theaisocietyasu/godfather-base:latest` to Docker Hub. Existing pods keep the image they started with; recreate them to pick up changes.

Build and push by hand:

```
docker build -t theaisocietyasu/godfather-base:latest .
docker push theaisocietyasu/godfather-base:latest
```
