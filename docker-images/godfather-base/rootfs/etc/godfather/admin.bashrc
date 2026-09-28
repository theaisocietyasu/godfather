[ -f /etc/bash.bashrc ] && . /etc/bash.bashrc
[ -f /root/.bashrc ] && . /root/.bashrc
export PS1='\[\033[01;31m\]\u\[\033[00m\]@\[\033[01;35m\]godfather\[\033[00m\]:\[\033[01;33m\]\w\[\033[00m\]\$ '
alias ll='ls -lah --color=auto'
alias workspace="cd /workspace/users/$GODFATHER_USER"
alias shared='cd /workspace/shared'
