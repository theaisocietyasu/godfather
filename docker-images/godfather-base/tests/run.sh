#!/bin/bash
# Runs a godfather-base image and checks its security properties over SSH.
# Usage: tests/run.sh <image tag>
set -euo pipefail

IMAGE="${1:?usage: tests/run.sh <image tag>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
EXPECTED_VERSION="$(cat "$HERE/../VERSION")"
POD_ID=test1
WORK="$(mktemp -d)"
CONTAINER="godfather-base-test-$$"
FAILED=0

# shellcheck disable=SC2317 # called by the EXIT trap
cleanup() {
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
    rm -rf "$WORK"
}
trap cleanup EXIT

pass() { echo "PASS $1"; }
fail() { echo "FAIL $1"; FAILED=1; }

# Keys: a throwaway user CA, the backend key, and one key for each login.
ssh-keygen -q -t ed25519 -N '' -C ca -f "$WORK/ca"
ssh-keygen -q -t ed25519 -N '' -C backend -f "$WORK/backend"
for name in alice bob admin other; do
    ssh-keygen -q -t ed25519 -N '' -C "$name" -f "$WORK/$name"
done

# Certificates as Platform signs them in modules/godfather/ssh.py.
sign_member() {
    ssh-keygen -q -s "$WORK/ca" -I "test:$1" -n "$2" -V +1h \
        -O clear -O permit-pty -O permit-port-forwarding \
        -O force-command="/usr/local/bin/godfather-login $1" "$WORK/$3.pub"
}
sign_member alice "gf-$POD_ID" alice
sign_member bob "gf-$POD_ID" bob
sign_member alice gf-other other
ssh-keygen -q -s "$WORK/ca" -I test:admin -n "gf-$POD_ID" -V +1h "$WORK/admin.pub"

docker run -d --name "$CONTAINER" -p 127.0.0.1::22 \
    -e GODFATHER_SSH_PUBLIC_KEY="$(cat "$WORK/backend.pub")" \
    -e GODFATHER_SSH_CA_PUBLIC_KEY="$(cat "$WORK/ca.pub")" \
    -e RUNPOD_POD_ID="$POD_ID" \
    -e RUNPOD_API_KEY=dummy-test-value \
    "$IMAGE" >/dev/null
PORT="$(docker port "$CONTAINER" 22/tcp | head -n1 | sed 's/.*://')"

SSH_OPTS=(-p "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR
    -o BatchMode=yes -o ConnectTimeout=5 -o IdentitiesOnly=yes)

for _ in $(seq 1 60); do
    if ssh "${SSH_OPTS[@]}" -i "$WORK/backend" root@127.0.0.1 true 2>/dev/null; then
        break
    fi
    sleep 1
done

# A member shell: with no remote command, godfather-login opens the interactive shell, so the script goes on stdin.
as_member() {
    ssh "${SSH_OPTS[@]}" -T -i "$WORK/$1" root@127.0.0.1 2>/dev/null <<<"$2
exit"
}
as_admin() {
    ssh "${SSH_OPTS[@]}" -i "$WORK/admin" root@127.0.0.1 "$@" 2>/dev/null
}
# Opens a direct-tcpip channel to the pod's sshd. Succeeds when the pod accepts it.
local_forward_works() {
    timeout 5 ssh "${SSH_OPTS[@]}" -i "$WORK/$1" -W 127.0.0.1:22 root@127.0.0.1 </dev/null 2>/dev/null \
        | head -c 64 | grep -q '^SSH-2.0'
}
# Asks for a remote forward and holds it for 3 seconds. Succeeds when the pod accepts it.
remote_forward_works() {
    local out code=0
    out="$(timeout 3 ssh "${SSH_OPTS[@]}" -o ExitOnForwardFailure=yes -N -i "$WORK/$1" \
        -R 127.0.0.1:0:127.0.0.1:22 root@127.0.0.1 2>&1)" || code=$?
    [ "$code" -eq 124 ] && ! grep -qi 'failed\|prohibited' <<<"$out"
}

# 1. Version label and version file.
label="$(docker inspect -f '{{ index .Config.Labels "com.ais-asu.godfather.base-version" }}' "$IMAGE")"
file="$(as_admin cat /etc/godfather/version || true)"
if [ "$label" = "$EXPECTED_VERSION" ] && [ "$file" = "$EXPECTED_VERSION" ]; then
    pass "1 version label and file are $EXPECTED_VERSION"
else
    fail "1 version label '$label' and file '$file', expected '$EXPECTED_VERSION'"
fi

# Bob logs in once, so his folders exist for check 4.
as_member bob 'touch ~/bob-file' >/dev/null || true

# 2. Alice is her own account with umask 077 and cannot list the other workspaces.
out="$(as_member alice 'id -un; umask; touch new-file; stat -c %a new-file
ls /workspace/users >/dev/null 2>&1 && echo listed || echo not-listed
cd /workspace/users/alice && echo entered')"
expected="godfather_alice
0077
600
not-listed
entered"
if [ "$(grep -v '^ *$' <<<"$out" | grep -A4 '^godfather_alice$')" = "$expected" ]; then
    pass "2 member account, umask 077, private files, no listing of /workspace/users"
else
    fail "2 member shell output: $out"
fi

# 3. Folder modes.
modes="$(as_admin stat -c %a /workspace/users /workspace/users/alice /home/godfather_alice | tr '\n' ' ')"
if [ "$modes" = "711 700 700 " ]; then
    pass "3 modes 711, 700, 700"
else
    fail "3 modes are $modes"
fi

# 4. Alice cannot read Bob's folders.
out="$(as_member alice 'ls /workspace/users/bob >/dev/null 2>&1 && echo read-ws || echo no-ws
ls /home/godfather_bob >/dev/null 2>&1 && echo read-home || echo no-home')"
if grep -q '^no-ws$' <<<"$out" && grep -q '^no-home$' <<<"$out"; then
    pass "4 no access to another member's workspace and home"
else
    fail "4 output: $out"
fi

# 5. No sudo and no su to root.
out="$(as_member alice 'command -v sudo >/dev/null && sudo -n true 2>/dev/null && echo sudo-ok || echo no-sudo
su root -c true </dev/null >/dev/null 2>&1 && echo su-ok || echo no-su')"
if grep -q '^no-sudo$' <<<"$out" && grep -q '^no-su$' <<<"$out"; then
    pass "5 no sudo, no su to root"
else
    fail "5 output: $out"
fi

# 6. The pod secrets are not in the member environment.
out="$(as_member alice 'env | grep -cE "^(GODFATHER_SSH_|RUNPOD_API_KEY)" || true
cat /proc/1/environ >/dev/null 2>&1 && echo environ-read || echo environ-denied')"
if grep -q '^0$' <<<"$out" && grep -q '^environ-denied$' <<<"$out"; then
    pass "6 no pod secrets in the member environment"
else
    fail "6 output: $out"
fi

# 7. A certificate for another pod is refused.
if ssh "${SSH_OPTS[@]}" -T -i "$WORK/other" root@127.0.0.1 </dev/null >/dev/null 2>&1; then
    fail "7 certificate for gf-other was accepted"
else
    pass "7 certificate for another pod refused"
fi

# 8. Forwarding: local forwards for members and admins, no remote forwards.
if ! local_forward_works alice; then
    fail "8 member local forward refused"
elif remote_forward_works alice; then
    fail "8 member remote forward accepted"
elif remote_forward_works admin; then
    fail "8 admin remote forward accepted"
elif ! local_forward_works admin; then
    fail "8 admin local forward refused"
else
    pass "8 member and admin -L work, member and admin -R refused"
fi

# 9. The backend key: SFTP works, no pty, no forwarding.
sftp_out="$(sftp -P "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
    -o BatchMode=yes -i "$WORK/backend" root@127.0.0.1 <<<'ls /workspace' 2>/dev/null || true)"
tty_out="$(ssh "${SSH_OPTS[@]}" -tt -i "$WORK/backend" root@127.0.0.1 tty 2>/dev/null || true)"
if ! grep -q users <<<"$sftp_out"; then
    fail "9 backend sftp output: $sftp_out"
elif grep -q '^/dev/pts' <<<"$tty_out"; then
    fail "9 backend key got a pty"
elif local_forward_works backend; then
    fail "9 backend local forward accepted"
else
    pass "9 backend key: sftp works, no pty, no forwarding"
fi

# 10. Admin login is root with GODFATHER_USER set.
# shellcheck disable=SC2016 # the variable expands in the pod shell
out="$(ssh "${SSH_OPTS[@]}" -T -i "$WORK/admin" root@127.0.0.1 /usr/local/bin/godfather-login --admin carol \
    <<<'id -un; echo "user=$GODFATHER_USER"; exit' 2>/dev/null || true)"
if grep -q '^root$' <<<"$out" && grep -q '^user=carol$' <<<"$out"; then
    pass "10 admin shell is root with GODFATHER_USER=carol"
else
    fail "10 output: $out"
fi

# 11. A command from the client runs as the member, in the workspace, with no banner.
out="$(ssh "${SSH_OPTS[@]}" -T -i "$WORK/alice" root@127.0.0.1 'id -un; umask; pwd' </dev/null 2>/dev/null || true)"
expected="godfather_alice
0077
/workspace/users/alice"
if [ "$out" = "$expected" ]; then
    pass "11 member command runs as godfather_alice in the workspace, no banner"
else
    fail "11 member command output: $out"
fi

# 12. SFTP as a member runs as the member, so VS Code and scp can copy files.
sftp_out="$(sftp -P "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
    -o BatchMode=yes -o IdentitiesOnly=yes -i "$WORK/alice" root@127.0.0.1 <<<"pwd
put $WORK/alice.pub sftp-file" 2>/dev/null || true)"
owner="$(as_admin stat -c %U /workspace/users/alice/sftp-file || true)"
if grep -q '/workspace/users/alice' <<<"$sftp_out" && [ "$owner" = "godfather_alice" ]; then
    pass "12 member sftp starts in the workspace and writes as godfather_alice"
else
    fail "12 member sftp output: $sftp_out, owner: $owner"
fi

# 13. hidepid status file, and hidden processes when it is on.
state="$(as_admin cat /etc/godfather/hidepid || true)"
if [ "$state" = "on" ]; then
    others="$(as_member alice 'ps -e -o user= | sort -u | grep -vc "^godfather_alice$" || true' | grep -E '^[0-9]+$' | tail -n1)"
    if [ "$others" = "0" ]; then
        pass "13 hidepid on, member sees only own processes"
    else
        fail "13 hidepid on, member sees $others other users"
    fi
elif [ "$state" = "off" ]; then
    pass "13 hidepid off (container has no CAP_SYS_ADMIN)"
else
    fail "13 hidepid status is '$state'"
fi

exit "$FAILED"
