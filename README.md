# Godfather

Godfather gives ASU students free compute. The AI Society at ASU pays for GPU and CPU machines on RunPod. Any student in the club's Discord server can get a private workspace on one, with no card, no cloud account, and no setup beyond installing the CLI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![GitHub stars](https://img.shields.io/github/stars/theaisocietyasu/godfather?style=social)](https://github.com/theaisocietyasu/godfather/stargazers) [![GitHub forks](https://img.shields.io/github/forks/theaisocietyasu/godfather?style=social)](https://github.com/theaisocietyasu/godfather/forks)

Since 2.0.0, the `godfather` module of [Platform](https://github.com/asusoda/platform) manages the pods. Officers create pods, share them, and schedule workshop sessions there. This repo keeps the two pieces that run outside Platform:

| Folder | What it is | Runs where |
| --- | --- | --- |
| `cli/` | `godfather-cli` on PyPI. Members sign in and connect with it. | members' laptops |
| `docker-images/godfather-base/` | The image every pod runs: sshd, member accounts, workspaces. | each RunPod pod |

The old Flask backend and Next.js portal were removed in 2.0.0. They are in the git history up to v1.1.0.

## How a member connects

```
godfather auth     browser -> platform /api/compute/<org>/cli/login -> Discord
                   -> http://127.0.0.1:<port>/callback?code=... -> CLI
                   CLI -> platform /api/compute/<org>/cli/token (code + PKCE verifier) -> token
godfather connect  CLI -> platform /api/compute/<org>/me/pods/<id>/connect -> 12-hour SSH certificate
                   CLI -> ssh with the certificate -> pod (godfather-base)
```

1. `godfather auth` opens Platform's sign-in page with a localhost callback and a PKCE challenge. The member signs in with Discord, and Platform sends a one-time code back to the CLI, which exchanges it for the token. If that is not possible, the member pastes the token that the page shows. The token lasts 90 days and stops working if they leave the Discord server.
2. The CLI makes its own SSH key once (`~/.godfather/ssh/id_ed25519`) and sends the public half when connecting. The platform returns a certificate signed by the org's user CA, valid for 12 hours and for that one pod.
3. The pod trusts the CA (`TrustedUserCAKeys`) and only accepts certificates naming its own pod ID. A member's certificate forces `godfather-login <username>`, which puts them in their own account. Members cannot list other workspaces and have no sudo. Officers get root.

Platform setup, routes, sessions and the file manager are in the Platform repo under `docs/modules/godfather.md`.

## Where to make common changes

| I want to... | Edit |
| --- | --- |
| Add a CLI command | `main()` and `GodfatherCLI` in `cli/godfather_cli/cli.py`. API calls go in `pod_manager.py`, SSH logic in `ssh_connector.py`. |
| Change the default server or org | `DEFAULT_API_URL` and `DEFAULT_ORG` in `cli/godfather_cli/cli.py`. |
| Change the pod shell, banner, or tools | `docker-images/godfather-base/`. Pods pick it up when created, so recreate pods after publishing. |
| Change what members can do on a pod | `docker-images/godfather-base/rootfs/usr/local/bin/godfather-login`, and the certificate options in Platform's `modules/godfather/ssh.py`. |

## Checks

```bash
make check
```

`make check` lints, tests and builds the CLI, lints the image scripts and the Dockerfile, and builds the image. The `Check` workflow runs the same steps on every push and pull request. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Releasing

Bump `version` in `cli/pyproject.toml` and `cli/godfather_cli/__init__.py`, add `docs/releases/v<version>.md`, and merge to main. `release.yml` creates the GitHub release and `publish-cli.yml` publishes to PyPI. When `docker-images/` changes, `build-pod-base-image.yml` builds the pod image and pushes it to `ghcr.io/theaisocietyasu/godfather-base` with `GITHUB_TOKEN`.

## License

MIT. See [LICENSE](LICENSE).
