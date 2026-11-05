# AGENTS.md

Instructions for AI agents in this repo. `CLAUDE.md` imports this file, and `.claude/` is a link to `.agents/`.

Godfather is the CLI (`godfather-cli` on PyPI) and the pod image (`godfather-base`). Platform's `godfather` module manages the pods: [asusoda/platform](https://github.com/asusoda/platform), `modules/godfather/`, `docs/modules/godfather.md`. Read [CONTRIBUTING.md](CONTRIBUTING.md) before the first change. Its rules apply to agents. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) has the design, [docs/ROADMAP.md](docs/ROADMAP.md) the direction.

## Commands

```bash
make check                                   # the gate: check-cli and check-image; CI runs the same
make check-cli                               # ruff, compile, pytest, uv build
make check-image                             # shellcheck, hadolint, docker build, tests/run.sh
cd cli && uv run pytest -q tests
cd cli && uv run ruff check . && uv run ruff format --check .
docker build -t godfather-base:dev docker-images/godfather-base
```

## Layout

| Path | Holds |
| --- | --- |
| `cli/godfather_cli/cli.py` | Argument parsing, the interactive menu, the server and org defaults |
| `cli/godfather_cli/auth.py` | Sign-in, token storage in `~/.godfather/config.json`, token checks |
| `cli/godfather_cli/login_server.py` | The loopback server that receives the sign-in code |
| `cli/godfather_cli/pod_manager.py` | Calls to the member routes, the pod table |
| `cli/godfather_cli/ssh_connector.py` | The SSH key, the certificate, the `ssh` command |
| `cli/godfather_cli/picker.py` | Arrow-key menus and the pod picker |
| `cli/godfather_cli/update_checker.py` | The PyPI version check |
| `cli/godfather_cli/ui.py` | Console output and styles |
| `cli/tests/` | pytest tests |
| `docker-images/godfather-base/` | `Dockerfile`, `setup-ssh.sh` (the entrypoint), `rootfs/` (files copied into the image), `VERSION`, `tests/run.sh` |
| `docs/releases/` | Release notes, one file for each version |
| `.github/workflows/` | `check.yml` (the gate), image publish, release, PyPI publish |
| `.agents/skills/` | Skills for agents |

## Rules

- The CLI calls only the member routes under `/api/compute/<org>/` (`me/pods`, `me/pods/<id>/connect`, `me/sessions`) and the sign-in routes `cli/login` and `cli/token`. It imports no Platform code.
- The pod image contract is shared with Platform. A change to any item names the matching Platform PR:
  - env names `GODFATHER_SSH_PUBLIC_KEY` and `GODFATHER_SSH_CA_PUBLIC_KEY`;
  - the certificate principal `gf-<pod id>`;
  - `/usr/local/bin/godfather-login <username>` and `godfather-login --admin <username>`;
  - the account name `godfather_<username>` and the `su - godfather_<username>` process that `modules/godfather/presence.py` matches;
  - `/etc/godfather/admin.bashrc`, which `presence.py` also matches;
  - the member setup files `/workspace/.godfather/member-setup/repo` and `script`, which Platform writes;
  - the label `com.ais-asu.godfather.base-version` and the file `/etc/godfather/version`, from `docker-images/godfather-base/VERSION`.
- Comments are plain ASCII and say what the code does.
- Never write a token, key or secret in code, tests, docs or commits.

## Skills

The skills are in `.agents/skills/`. Use them:

- `karpathy-guidelines` while you write code; `code-quality` and `codebase-design` for naming, layout and cleanup.
- `systematic-debugging` for a bug or a failing test; `verification-before-completion` before you say a change works.
- `technical-writing` for docs, comments and messages; `unslop` on long prose; `mermaid-diagrams` for diagrams; `writing-for-agents` for skills and this file.
- `pr` for a pull request body; `receiving-code-review` before you act on review comments; `write-report` for results.
- `grilling`, `discernment-nudge` and `show-me` when the person asks for them.

## Releasing

1. Bump `version` in `cli/pyproject.toml` and `__version__` in `cli/godfather_cli/__init__.py`.
2. Add `docs/releases/v<version>.md`.
3. Merge to `main`. `release.yml` creates the GitHub release. `publish-cli.yml` publishes to TestPyPI and PyPI.

A change under `docker-images/` that merges to `main` starts `build-pod-base-image.yml`. It pushes `ghcr.io/theaisocietyasu/godfather-base` with `GITHUB_TOKEN`.

## Docs

Change `README.md`, `cli/README.md`, `docs/ARCHITECTURE.md` and `docker-images/godfather-base/README.md` in the same commit as the behavior they describe.
