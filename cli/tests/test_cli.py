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


PODS = [
    {'id': 'stopped0000001', 'name': 'old', 'status': 'EXITED', 'is_public': True},
    {'id': 'running000001', 'name': 'workshop', 'status': 'RUNNING', 'is_public': True},
    {'id': 'running000002', 'name': 'research-a100', 'status': 'RUNNING', 'is_public': False},
]


def test_disabled_reason_allows_only_running_pods():
    from godfather_cli.picker import disabled_reason

    assert disabled_reason({'status': 'RUNNING'}) is None
    assert disabled_reason({}) is None
    assert 'start it' in disabled_reason({'status': 'EXITED'})
    assert disabled_reason({'status': 'GONE'}) == 'deleted'
    assert disabled_reason({'status': 'CREATED'}) == 'created, not running yet'


def test_pod_options_put_connectable_pods_first():
    from godfather_cli.picker import pod_options

    options = pod_options(PODS)
    assert [o.pod_id for o in options] == ['running000001', 'running000002', 'stopped0000001']
    assert [o.disabled is None for o in options] == [True, True, False]
    text = ''.join(part for _, part in options[1].parts)
    assert 'research-a100' in text and 'RUNNING' in text and 'shared with you' in text
    assert 'running00000' in text
    # Names are padded to one width so the columns line up.
    assert len(options[0].parts[0][1]) == len(options[1].parts[0][1])


def test_single_connectable_pod_skips_the_picker():
    from godfather_cli.picker import single_connectable

    assert single_connectable(PODS) is None
    assert single_connectable(PODS[:2])['id'] == 'running000001'
    assert single_connectable(PODS[:1]) is None
    assert single_connectable([]) is None


def test_menu_offers_login_or_logout():
    from godfather_cli.picker import menu_options, LOGIN, LOGOUT

    actions = [action for action, _, _ in menu_options(True)]
    assert actions == ['connect', 'list', 'status', LOGOUT, 'exit']
    assert LOGIN in [action for action, _, _ in menu_options(False)]


def test_picker_choices_build_without_a_terminal():
    from questionary import Choice
    from godfather_cli.picker import pod_options

    choices = [Choice(o.parts, value=o.pod_id, disabled=o.disabled) for o in pod_options(PODS)]
    assert [c.disabled for c in choices][-1] == 'stopped, ask an officer to start it'


def test_api_errors_say_what_happened(tmp_path, monkeypatch):
    import pytest
    from godfather_cli import pod_manager

    auth = CLIAuthenticator('https://platform.example', 'ais', tmp_path)
    auth.config = {'token': 'plat_abc'}
    pods = pod_manager.PodManager(auth.api_base, auth)

    monkeypatch.setattr(pod_manager.requests, 'get', lambda url, **kw: Response(401, {'error': 'expired'}))
    with pytest.raises(pod_manager.ApiError) as e:
        pods.fetch_pods()
    assert e.value.kind == pod_manager.EXPIRED and 'godfather auth' in e.value.hint

    monkeypatch.setattr(pod_manager.requests, 'post', lambda url, **kw: Response(409, {'error': 'Pod is not running'}))
    with pytest.raises(pod_manager.ApiError) as e:
        pods.fetch_connection_info('pod1', 'ssh-ed25519 AAAA')
    assert e.value.kind == pod_manager.STOPPED and e.value.message == 'Pod is not running'

    def unreachable(url, **kw):
        raise pod_manager.requests.ConnectionError()

    monkeypatch.setattr(pod_manager.requests, 'get', unreachable)
    with pytest.raises(pod_manager.ApiError) as e:
        pods.fetch_pods()
    assert e.value.kind == pod_manager.UNREACHABLE and 'platform.example' in e.value.message
    assert pods.get_public_pods() == []


def test_check_token_tells_expired_from_unreachable(tmp_path, monkeypatch):
    from godfather_cli import auth as auth_module

    auth = CLIAuthenticator('https://platform.example', 'ais', tmp_path)
    assert auth.check_token() == auth_module.TOKEN_MISSING
    auth.config = {'token': 'plat_abc', 'api_url': 'https://platform.example', 'org': 'ais'}
    monkeypatch.setattr(auth_module.requests, 'get', lambda url, **kw: Response(401, {}))
    assert auth.check_token() == auth_module.TOKEN_EXPIRED

    def unreachable(url, **kw):
        raise auth_module.requests.ConnectionError()

    monkeypatch.setattr(auth_module.requests, 'get', unreachable)
    assert auth.check_token() == auth_module.TOKEN_UNREACHABLE
    assert not auth.verify_token()


def test_token_expiry_is_ninety_days_after_login(tmp_path):
    auth = CLIAuthenticator('https://platform.example', 'ais', tmp_path)
    assert auth.token_expires_at() is None
    auth.config = {'token': 'plat_abc', 'api_url': 'https://platform.example', 'org': 'ais'}
    auth.save_config()
    assert (auth.token_expires_at() - auth.token_saved_at()).days == 90


def test_choose_pod_without_a_terminal_uses_numbers(tmp_path, monkeypatch):
    from godfather_cli import cli as cli_module

    monkeypatch.setattr(cli_module.Path, 'home', lambda: tmp_path)
    monkeypatch.delenv('GODFATHER_API_URL', raising=False)
    monkeypatch.setattr(cli_module, 'is_interactive', lambda: False)
    godfather = cli_module.GodfatherCLI()
    monkeypatch.setattr(godfather.pod_manager, 'fetch_pods', lambda: PODS)
    monkeypatch.setattr(godfather.pod_manager, 'prompt_pod_number', lambda pods: pods[1]['id'])
    assert godfather.choose_pod() == 'running000001'
