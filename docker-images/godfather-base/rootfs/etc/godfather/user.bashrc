[ -f /etc/bash.bashrc ] && . /etc/bash.bashrc
[ -d /usr/local/cuda/bin ] && export PATH="/usr/local/cuda/bin:$PATH"
GODFATHER_USER="${USER#godfather_}"
export PS1='\[\033[01;36m\]\u\[\033[00m\]@\[\033[01;35m\]pod\[\033[00m\]:\[\033[01;33m\]\w\[\033[00m\]\$ '
alias ll='ls -lah --color=auto'
alias workspace="cd /workspace/users/$GODFATHER_USER"
alias shared='cd /workspace/shared'
