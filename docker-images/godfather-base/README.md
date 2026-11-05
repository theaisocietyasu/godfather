# godfather-base

The image every Godfather pod runs, built on `runpod/base`. It runs sshd, trusts the org's user CA from Platform's `godfather` module, and gives each member a private account and workspace.

## Files

- `Dockerfile`: installs tools and openssh-server, copies `rootfs/` into the image, sets `setup-ssh.sh` as the entrypoint.
- `setup-ssh.sh`: runs when the pod starts. It reads three environment variables:
  - `GODFATHER_SSH_PUBLIC_KEY`: the platform's key, added to root's `authorized_keys` for the officer file manager.
  - `GODFATHER_SSH_CA_PUBLIC_KEY`: the user CA, written to `/etc/ssh/godfather_user_ca.pub`.
  - `RUNPOD_POD_ID`: set by RunPod. Root accepts only certificates with the principal `gf-<pod id>`, so a certificate for one pod does not open another.
  Platform sets the first two when it creates the pod. The image does not read `GODFATHER_SETUP`, which Platform also sends. Then it starts sshd, creates `/workspace/users` and `/workspace/shared`, and writes the login banner.
- `rootfs/etc/ssh/sshd_config.d/godfather.conf`: key-only root login, CA trust, principals file, forwarding and login limits.
- `rootfs/usr/local/bin/godfather-login`: runs on every CLI connection. Members reach it as the forced command in their certificate. It creates `godfather_<username>`, gives them `/workspace/users/<username>` and a home folder (both mode 700), and switches to that account with umask 077. When the client sends a command (VS Code Remote-SSH, scp, sftp), sshd puts it in `SSH_ORIGINAL_COMMAND`, and `godfather-login` runs it as that account in the workspace, with no banner. With a terminal, the member shell gets its own (`su --pty`), so job control works. Admins run it with `--admin` and stay root.
- Member setup (2.4.0): when `/workspace/.godfather/member-setup/repo` or `script` exists, `godfather-login` sets up each member's workspace once for each version of these files, on the member's next connection. `repo` is a public https git URL; it is cloned into the workspace unless a folder of that name exists. `script` runs as the member in the workspace with `bash`. Each step stops after 300 seconds. The output goes to `~/godfather-setup.log`. `/workspace/.godfather` is mode 700, so members cannot read the setup. Platform writes the files from the pod's Member setup on the dashboard. With no files, nothing runs.
- `VERSION`: the image version. `tests/run.sh`: the image tests.
- `rootfs/etc/godfather/*.bashrc`: prompt and aliases (`workspace`, `shared`, `ll`) for member and admin shells.

## Security

Members on one pod share one container. The image limits what one member can do to another:

| Item | Setting |
| --- | --- |
| `/workspace/users` | mode 711, owner root. A member enters their own folder but cannot list the others. |
| `/workspace/users/<username>`, `/home/godfather_<username>` | mode 700 |
| Member shells | `umask 077`. To share a file, copy it to `/workspace/shared` and run `chmod o+r` on it. |
| sudo | Not installed. Admin shells are root. |
| root password | `*`, so `su` to root fails. Key and certificate logins as root work. |
| `/proc` | `hidepid=2` if the container allows the remount. `/etc/godfather/hidepid` is `on` or `off`. Without `CAP_SYS_ADMIN` it is `off`, and members see each other's processes. |
| sshd | `AllowTcpForwarding local`, no X11, tunnels, socket forwarding, user environment or user rc. `MaxAuthTries 3`, `LoginGraceTime 30`. |
| Backend key | `restrict`: no pty and no forwarding. Platform uses it for SFTP and `ps`. |

Member certificates carry `permit-port-forwarding`, because VS Code Remote-SSH reaches its server through a local forward. sshd allows only local forwards, so a member can open no listening port and no Unix socket. A local forward reaches only addresses that a member's shell can already reach on the pod, so services on `127.0.0.1` are shared by every member of the pod.

## Version

`VERSION` holds the image version. The build passes it as `GODFATHER_BASE_VERSION`. The image has the labels `com.ais-asu.godfather.base-version` (Platform reads it), `org.opencontainers.image.version` and `org.opencontainers.image.title=godfather-base`, and the file `/etc/godfather/version`. An image built `FROM` godfather-base inherits the labels.

The workflow pushes `:<version>`, `:latest` and `:<short sha>`. It fails if `:<version>` exists already. Bump `VERSION` with each image change.

## Tests

`tests/run.sh <image tag>` runs the image with a throwaway CA and keys, signs member and admin certificates as Platform does, and checks the items in Security over SSH. Each check prints PASS or FAIL. `make check-image`, the `Check` workflow and the publish workflow run it.

## Changing it

Edit the files above and merge to `main`. The `build-pod-base-image` workflow pushes `ghcr.io/theaisocietyasu/godfather-base:latest` and `:<short sha>`. Existing pods keep the image they started with. Recreate them to get the change.

Build and push by hand:

```
docker build --build-arg GODFATHER_BASE_VERSION="$(cat VERSION)" -t ghcr.io/theaisocietyasu/godfather-base:latest .
docker push ghcr.io/theaisocietyasu/godfather-base:latest
```
