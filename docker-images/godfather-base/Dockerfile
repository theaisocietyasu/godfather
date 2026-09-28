# Godfather Base Image - RunPod compatible with auto SSH setup and user isolation
FROM runpod/base:0.4.0-cuda11.8.0

# Install additional tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    curl \
    wget \
    htop \
    tmux \
    openssh-server \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Configure SSH server. The drop-in in rootfs/etc/ssh/sshd_config.d sets key-only root
# login and trusts the Godfather user CA; make sure sshd_config includes it first.
RUN mkdir -p /var/run/sshd /etc/ssh/sshd_config.d && \
    sed -i 's/^PermitRootLogin .*/#&/' /etc/ssh/sshd_config && \
    (grep -q '^Include /etc/ssh/sshd_config.d/\*.conf' /etc/ssh/sshd_config || \
        sed -i '1i Include /etc/ssh/sshd_config.d/*.conf' /etc/ssh/sshd_config) && \
    sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

# Security: Remove sudo access for non-privileged users by default
# Restricted users created by setup-ssh.sh will NOT have sudo access
RUN echo "" > /etc/sudoers.d/README && \
    chmod 440 /etc/sudoers.d/README && \
    echo "# Only root and explicitly authorized users can use sudo" > /etc/sudoers.d/README

COPY rootfs/ /

# Create startup script for SSH key setup and user management
COPY setup-ssh.sh /start.sh
RUN chmod +x /start.sh /usr/local/bin/godfather-login

# Expose SSH port
EXPOSE 22

# Set the entrypoint to run our setup script
ENTRYPOINT ["/start.sh"]
