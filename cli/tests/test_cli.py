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


def test_only_platform_tokens_for_this_server_count(tmp_path):
    auth = CLIAuthenticator('https://platform.example', 'ais', tmp_path)
    auth.config = {'token': 'gf1.a.b', 'api_url': 'https://platform.example', 'org': 'ais'}
    assert not auth.is_authenticated()
    auth.config = {'token': 'plat_abc', 'api_url': 'https://platform.example', 'org': 'ais'}
    assert auth.is_authenticated()
    assert auth.auth_headers() == {'Authorization': 'Bearer plat_abc'}
    auth.config['org'] = 'soda'
    assert not auth.is_authenticated()


class Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def json(self):
        return self.body


def test_pods_and_connect_use_the_member_compute_routes(tmp_path, monkeypatch):
    from godfather_cli import pod_manager

    calls = []

    def get(url, **kwargs):
        calls.append(('GET', url, kwargs['headers']))
        return Response(200, {'pods': [{'id': 'pod1', 'name': 'workshop', 'status': 'RUNNING'}]})

    def post(url, **kwargs):
        calls.append(('POST', url, kwargs['json']))
        return Response(200, {'ssh_info': INFO})

    monkeypatch.setattr(pod_manager.requests, 'get', get)
    monkeypatch.setattr(pod_manager.requests, 'post', post)
    auth = CLIAuthenticator('https://platform.example', 'ais', tmp_path)
    auth.config = {'token': 'plat_abc'}
    pods = pod_manager.PodManager(auth.api_base, auth)
    assert pods.get_public_pods()[0]['id'] == 'pod1'
    assert pods.get_connection_info('pod1', 'ssh-ed25519 AAAA') == INFO
    assert calls == [
        ('GET', 'https://platform.example/api/compute/ais/me/pods', {'Authorization': 'Bearer plat_abc'}),
        ('POST', 'https://platform.example/api/compute/ais/me/pods/pod1/connect', {'public_key': 'ssh-ed25519 AAAA'}),
    ]


def test_login_saves_server_and_org(tmp_path, monkeypatch):
    from godfather_cli import auth as auth_module

    opened = []
    monkeypatch.setattr(auth_module.webbrowser, 'open', opened.append)
    monkeypatch.setattr(auth_module.Prompt, 'ask', lambda *args, **kwargs: 'plat_abc')
    monkeypatch.setattr(auth_module.requests, 'get', lambda url, **kwargs: Response(200, {'pods': []}))
    auth = CLIAuthenticator('https://platform.example', 'ais', tmp_path)
    assert auth.authenticate()
    assert opened == ['https://platform.example/api/compute/ais/cli/login']
    assert CLIAuthenticator.read_config(tmp_path) == {
        'token': 'plat_abc',
        'api_url': 'https://platform.example',
        'org': 'ais',
    }

    monkeypatch.setattr(auth_module.Prompt, 'ask', lambda *args, **kwargs: 'gf1.a.b')
    assert not CLIAuthenticator('https://platform.example', 'ais', tmp_path / 'other').authenticate()


def test_retired_server_in_env_falls_back_to_default(tmp_path, monkeypatch):
    from godfather_cli import cli as cli_module

    monkeypatch.setattr(cli_module.Path, 'home', lambda: tmp_path)
    monkeypatch.setenv('GODFATHER_API_URL', 'https://8bzhwve1ri5cw2-80.proxy.runpod.net')
    assert cli_module.GodfatherCLI().api_base == cli_module.DEFAULT_API_URL
    monkeypatch.setenv('GODFATHER_API_URL', 'https://platform.example/')
    assert cli_module.GodfatherCLI().api_base == 'https://platform.example'
