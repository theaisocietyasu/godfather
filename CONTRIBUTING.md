# Contributing

[AGENTS.md](AGENTS.md) has the commands, the layout and the pod image contract. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before you change how the CLI talks to Platform or how a pod starts. These rules apply to people and coding agents.

## Principles

<!-- shared: start -->
This section is the same in asusoda/platform, theaisocietyasu/sparky and theaisocietyasu/godfather. The Platform copy is the source. Change it there first, then in the other two.

- One name for each thing, in code, UI and docs. Use the terms of the Platform glossary.
- No ambiguity. A name, a route or a message has one meaning.
- Clean code: small functions, no dead code, no commented-out code, no TODO without an issue link.
- Small pull requests with one logical change.
- Tests and docs change in the same pull request as the code.
- A change is done when the gate passes.
- Comments are plain ASCII and say what the code does. The why goes in the commit body.
- Commit subjects are imperative and 72 characters or fewer.
<!-- shared: end -->

## Setup

You need [uv](https://docs.astral.sh/uv), OpenSSH on `PATH`, and Docker for the image checks. The image lint also needs `shellcheck`.

```bash
cd cli && uv sync --group dev
```

## The gate

```bash
make check         # check-cli and check-image, the same steps as CI
make check-cli     # ruff, compile, pytest, build
make check-image   # shellcheck, hadolint, docker build
```

## Branches and pull requests

Branch from `main`. Put one change in each pull request. New behavior needs a test that fails without the change. The commit body says why. Fill in the pull request template.

## Python (`cli/`)

- ruff checks and formats the code (line length 120, target `py38`).
- The code runs on Python 3.8. Do not use `match` or the `X | Y` type syntax. Use `typing.Dict` and `Optional`.
- Write output only through `godfather_cli/ui.py` (`console`, `error`, `warning`, `success`). Do not use `print()`.
- Never print a full token. `godfather status` shows the first 9 characters.
- Config files are mode 600.

## Shell (`docker-images/godfather-base/`)

- New scripts start with `set -euo pipefail`.
- `shellcheck` passes. Add `# shellcheck disable` only for a false positive, with the reason on the same line.
- Comments are plain ASCII.

## Reporting

Open an issue with one of the forms. Report a vulnerability privately through a [security advisory](https://github.com/theaisocietyasu/godfather/security/advisories/new).
