# Godfather Base Image - RunPod compatible with auto SSH setup and user isolation
FROM runpod/base:0.6.3-cuda11.8.0

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

# Configure SSH server
RUN mkdir /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

# Security: Remove sudo access for non-privileged users by default
# Restricted users created by setup-ssh.sh will NOT have sudo access
RUN echo "" > /etc/sudoers.d/README && \
    chmod 440 /etc/sudoers.d/README && \
    echo "# Only root and explicitly authorized users can use sudo" > /etc/sudoers.d/README

# Create startup script for SSH key setup and user management
COPY setup-ssh.sh /start.sh
RUN chmod +x /start.sh

# Expose SSH port
EXPOSE 22

# Set the entrypoint to run our setup script
ENTRYPOINT ["/start.sh"]
