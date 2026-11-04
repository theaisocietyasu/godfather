# Godfather Base Image - RunPod compatible with auto SSH setup and user isolation
FROM runpod/base:0.4.0-cuda11.8.0

ARG GODFATHER_BASE_VERSION=dev

# Platform reads com.ais-asu.godfather.base-version. Images built FROM this one inherit it.
LABEL com.ais-asu.godfather.base-version=$GODFATHER_BASE_VERSION \
      org.opencontainers.image.title=godfather-base \
      org.opencontainers.image.version=$GODFATHER_BASE_VERSION

# Install tools. sudo comes with runpod/base; members must not have it and root does not need it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    git \
    curl \
    wget \
    htop \
    tmux \
    openssh-server \
    && SUDO_FORCE_REMOVE=yes apt-get purge -y sudo \
    && rm -rf /var/lib/apt/lists/* /etc/sudoers /etc/sudoers.d

# Configure SSH server. The drop-in in rootfs/etc/ssh/sshd_config.d sets key-only root
# login and trusts the Godfather user CA; make sure sshd_config includes it first.
RUN mkdir -p /var/run/sshd /etc/ssh/sshd_config.d && \
    sed -i 's/^PermitRootLogin .*/#&/' /etc/ssh/sshd_config && \
    (grep -q '^Include /etc/ssh/sshd_config.d/\*.conf' /etc/ssh/sshd_config || \
        sed -i '1i Include /etc/ssh/sshd_config.d/*.conf' /etc/ssh/sshd_config) && \
    sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

COPY rootfs/ /
RUN printf '%s\n' "$GODFATHER_BASE_VERSION" > /etc/godfather/version

# Create startup script for SSH key setup and user management
COPY setup-ssh.sh /start.sh
RUN chmod +x /start.sh /usr/local/bin/godfather-login

# Expose SSH port
EXPOSE 22

# Set the entrypoint to run our setup script
ENTRYPOINT ["/start.sh"]
