HADOLINT := ghcr.io/hadolint/hadolint:v2.14.0
IMAGE_DIR := docker-images/godfather-base
IMAGE_TAG := godfather-base:check
IMAGE_VERSION := $(shell cat $(IMAGE_DIR)/VERSION)
SHELL_SCRIPTS := $(IMAGE_DIR)/setup-ssh.sh $(IMAGE_DIR)/rootfs/usr/local/bin/godfather-login $(IMAGE_DIR)/tests/run.sh
BASH_RC_FILES := $(IMAGE_DIR)/rootfs/etc/godfather/user.bashrc $(IMAGE_DIR)/rootfs/etc/godfather/admin.bashrc

.PHONY: check check-cli lint-image check-image

check: check-cli check-image

check-cli:
	cd cli && uv sync --frozen --group dev
	cd cli && uv run ruff check .
	cd cli && uv run ruff format --check .
	cd cli && uv run python -m compileall -q godfather_cli
	cd cli && uv run pytest -q tests
	cd cli && uv build

lint-image:
	shellcheck $(SHELL_SCRIPTS)
	shellcheck -s bash $(BASH_RC_FILES)
	docker run --rm -i -v "$(CURDIR)/$(IMAGE_DIR)/.hadolint.yaml:/hadolint.yaml:ro" $(HADOLINT) \
		hadolint --config /hadolint.yaml - < $(IMAGE_DIR)/Dockerfile

check-image: lint-image
	docker build --build-arg GODFATHER_BASE_VERSION=$(IMAGE_VERSION) -t $(IMAGE_TAG) $(IMAGE_DIR)
	$(IMAGE_DIR)/tests/run.sh $(IMAGE_TAG)
