# Godfather Base Image - RunPod compatible with auto SSH setup
FROM runpod/base:0.4.0-cuda11.8.0

# Install additional tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    curl \
    wget \
    htop \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Create startup script for SSH key setup
COPY setup-ssh.sh /start.sh
RUN chmod +x /start.sh

# Set the entrypoint to run our setup script
ENTRYPOINT ["/start.sh"]
