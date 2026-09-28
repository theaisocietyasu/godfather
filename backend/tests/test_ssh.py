import subprocess

import pytest

from domains.ssh.service import SSHService, is_valid_public_key, pod_principal, safe_username


@pytest.fixture
def user_key(tmp_path):
    path = tmp_path / 'id'
    subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(path)], check=True)
    return (tmp_path / 'id.pub').read_text().strip()


def cert_text(cert, tmp_path):
    path = tmp_path / 'cert.pub'
    path.write_text(cert + '\n')
    return subprocess.run(['ssh-keygen', '-L', '-f', str(path)], check=True, capture_output=True, text=True).stdout


def test_safe_username():
    assert safe_username('Some.User_1') == 'some.user_1'
    assert safe_username('a; rm -rf /') == 'arm-rf'
    assert safe_username('') == 'user'
    assert safe_username('-x') == 'x'
    assert len(safe_username('a' * 40)) == 22


def test_public_key_validation(user_key):
    assert is_valid_public_key(user_key)
    assert not is_valid_public_key('')
    assert not is_valid_public_key(user_key + '\nssh-ed25519 AAAA')
    assert not is_valid_public_key('ssh-dss AAAAB3Nza')
    assert not is_valid_public_key('-----BEGIN OPENSSH PRIVATE KEY-----')


def test_keys_are_stable(ssh_keys):
    assert SSHService.get_user_ca() == SSHService.get_user_ca()
    assert SSHService.get_backend_key() != SSHService.get_user_ca()


def test_member_certificate_is_forced_into_login(ssh_keys, user_key, tmp_path):
    cert = SSHService.sign_user_key(user_key, 'pod123', '42', 'alice', is_admin=False)
    text = cert_text(cert, tmp_path)
    assert pod_principal('pod123') in text
    assert 'force-command /usr/local/bin/godfather-login alice' in text
    assert 'permit-pty' in text
    assert 'permit-agent-forwarding' not in text


def test_admin_certificate_has_no_forced_command(ssh_keys, user_key, tmp_path):
    cert = SSHService.sign_user_key(user_key, 'pod123', '42', 'bob', is_admin=True)
    text = cert_text(cert, tmp_path)
    assert 'force-command' not in text
    assert pod_principal('pod123') in text


def test_rejects_bad_public_key(ssh_keys):
    with pytest.raises(ValueError):
        SSHService.sign_user_key('not a key', 'pod123', '42', 'alice', is_admin=False)


def test_legacy_key_is_only_a_fallback(ssh_keys):
    ssh_keys.insert_one({'key_type': 'organization', 'private_key': 'legacy', 'public_key': 'x'})
    keys = SSHService.get_file_manager_keys()
    assert keys[-1] == 'legacy' and len(keys) == 2
