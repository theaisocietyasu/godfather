import os
import stat
import threading
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse

import pytest

from godfather_cli import auth as auth_module
from godfather_cli.auth import CLIAuthenticator, challenge_for, make_verifier
from godfather_cli.login_server import LoopbackReceiver

SERVER = 'https://platform.example'


class Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def json(self):
        return self.body


def get_status(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code


def test_challenge_matches_rfc_7636_appendix_b():
    assert challenge_for('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk') == 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
    verifier = make_verifier()
    assert 43 <= len(verifier) <= 128


def test_receiver_keeps_the_code_for_the_right_state_only():
    receiver = LoopbackReceiver('state123')
    assert receiver._server.server_address[0] == '127.0.0.1'
    base = f'http://127.0.0.1:{receiver.port}'
    results = {}
    worker = threading.Thread(target=lambda: results.setdefault('code', receiver.wait(10)))
    worker.start()
    try:
        assert get_status(f'{base}/other') == 404
        assert get_status(f'{base}/callback?code=abc&state=wrong') == 400
        assert get_status(f'{base}/callback?code=abc&state=state123') == 200
        worker.join(5)
    finally:
        receiver.close()
    assert results['code'] == 'abc'


def test_receiver_times_out():
    receiver = LoopbackReceiver('s')
    try:
        assert receiver.wait(0.2) is None
    finally:
        receiver.close()


def browser_that_signs_in(code='code1'):
    """A fake webbrowser.open that follows the login URL to the loopback callback."""
    opened = []

    def open_url(url):
        opened.append(url)
        query = parse_qs(urlparse(url).query)
        port, state = query['port'][0], query['state'][0]
        callback = f'http://127.0.0.1:{port}/callback?code={code}&state={state}'
        threading.Thread(target=get_status, args=(callback,)).start()
        return True

    return open_url, opened


def test_browser_login_saves_the_token(tmp_path, monkeypatch):
    open_url, opened = browser_that_signs_in()
    posts = []

    def post(url, json, **kwargs):
        posts.append((url, json))
        if not json:
            return Response(400, {'error': 'code and code_verifier are required'})
        return Response(200, {'token': 'plat_new', 'expires_days': 90})

    monkeypatch.setattr(auth_module.webbrowser, 'open', open_url)
    monkeypatch.setattr(auth_module.requests, 'post', post)
    monkeypatch.setattr(auth_module.requests, 'get', lambda url, **kwargs: Response(200, {'pods': []}))
    monkeypatch.setattr(auth_module.Prompt, 'ask', lambda *a, **kw: pytest.fail('asked to paste'))

    auth = CLIAuthenticator(SERVER, 'ais', tmp_path)
    assert auth.authenticate()

    login = urlparse(opened[0])
    query = parse_qs(login.query)
    assert f'{login.scheme}://{login.netloc}{login.path}' == f'{SERVER}/api/compute/ais/cli/login'
    assert query['code_challenge_method'] == ['S256']
    token_url, body = posts[1]
    assert token_url == f'{SERVER}/api/compute/ais/cli/token'
    assert body['code'] == 'code1'
    assert challenge_for(body['code_verifier']) == query['code_challenge'][0]
    assert CLIAuthenticator.read_config(tmp_path) == {'token': 'plat_new', 'api_url': SERVER, 'org': 'ais'}
    assert stat.S_IMODE(os.stat(tmp_path / 'config.json').st_mode) == 0o600


def paste_flow(monkeypatch):
    """Patches the paste prompt and the token check. Returns the list of pastes asked for."""
    asked = []
    monkeypatch.setattr(auth_module.Prompt, 'ask', lambda *a, **kw: asked.append(1) or 'plat_pasted')
    monkeypatch.setattr(auth_module.requests, 'get', lambda url, **kwargs: Response(200, {'pods': []}))
    return asked


def test_old_server_falls_back_to_paste(tmp_path, monkeypatch):
    asked = paste_flow(monkeypatch)
    opened = []
    monkeypatch.setattr(auth_module.webbrowser, 'open', opened.append)
    monkeypatch.setattr(auth_module.requests, 'post', lambda url, **kwargs: Response(404, {}))
    assert CLIAuthenticator(SERVER, 'ais', tmp_path).authenticate()
    assert asked == [1]
    assert opened == [f'{SERVER}/api/compute/ais/cli/login']
    assert CLIAuthenticator.read_config(tmp_path)['token'] == 'plat_pasted'


def test_timeout_falls_back_to_paste(tmp_path, monkeypatch):
    asked = paste_flow(monkeypatch)
    monkeypatch.setattr(auth_module, 'LOGIN_WAIT_SECONDS', 0.2)
    monkeypatch.setattr(auth_module.webbrowser, 'open', lambda url: True)
    monkeypatch.setattr(auth_module.requests, 'post', lambda url, **kwargs: Response(400, {}))
    assert CLIAuthenticator(SERVER, 'ais', tmp_path).authenticate()
    assert asked == [1]


def test_no_browser_falls_back_to_paste(tmp_path, monkeypatch):
    asked = paste_flow(monkeypatch)
    monkeypatch.setattr(auth_module.webbrowser, 'open', lambda url: False)
    monkeypatch.setattr(auth_module.requests, 'post', lambda url, **kwargs: Response(400, {}))
    assert CLIAuthenticator(SERVER, 'ais', tmp_path).authenticate()
    assert asked == [1]


def test_paste_flag_skips_the_probe(tmp_path, monkeypatch):
    asked = paste_flow(monkeypatch)
    monkeypatch.setattr(auth_module.webbrowser, 'open', lambda url: True)
    monkeypatch.setattr(auth_module.requests, 'post', lambda *a, **kw: pytest.fail('probed the server'))
    assert CLIAuthenticator(SERVER, 'ais', tmp_path).authenticate(paste=True)
    assert asked == [1]
