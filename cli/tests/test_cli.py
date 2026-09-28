from godfather_cli.auth import CLIAuthenticator
from godfather_cli.ssh_connector import SSHConnector

INFO = {'host': '1.2.3.4', 'port': 2200, 'username': 'root', 'user_folder': 'alice'}


def test_member_command_has_no_remote_command(tmp_path):
    command = SSHConnector(tmp_path).build_command({**INFO, 'is_admin': False})
    assert command[-1] == 'root@1.2.3.4'
    assert f'CertificateFile={tmp_path}/ssh/id_ed25519-cert.pub' in command


def test_admin_command_runs_login_script(tmp_path):
    command = SSHConnector(tmp_path).build_command({**INFO, 'is_admin': True})
    assert command[-1] == '/usr/local/bin/godfather-login --admin alice'


def test_rejects_unsafe_username(tmp_path):
    assert SSHConnector(tmp_path).build_command({**INFO, 'user_folder': 'a; rm -rf /'}) is None


def test_keypair_is_created_once(tmp_path):
    connector = SSHConnector(tmp_path)
    first = connector.ensure_keypair()
    assert first.startswith('ssh-ed25519 ')
    assert connector.ensure_keypair() == first


def test_legacy_token_is_not_authenticated(tmp_path):
    auth = CLIAuthenticator('https://example.invalid', tmp_path)
    auth.config = {'token': 'discord_123_1700000000'}
    assert not auth.is_authenticated()
    auth.config = {'token': 'gf1.a.b'}
    assert auth.is_authenticated()
    assert auth.auth_headers() == {'Authorization': 'Bearer gf1.a.b'}
