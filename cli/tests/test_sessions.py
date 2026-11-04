import datetime

import pytest

from godfather_cli import pod_manager
from godfather_cli.auth import CLIAuthenticator
from godfather_cli.pod_manager import PodManager, starts_in

NOW = datetime.datetime(2026, 10, 21, 15, 0, tzinfo=datetime.timezone.utc)
SESSION = {
    'pod_id': 'pod1',
    'pod_name': 'workshop',
    'title': 'Intro to CUDA',
    'start_at': '2026-10-21T17:05:00+00:00',
    'stop_at': '2026-10-21T19:00:00+00:00',
    'pod_starts_at': '2026-10-21T16:55:00+00:00',
}


class Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def json(self):
        return self.body


def manager(tmp_path):
    auth = CLIAuthenticator('https://platform.example', 'ais', tmp_path)
    auth.config = {'token': 'plat_abc', 'api_url': 'https://platform.example', 'org': 'ais'}
    return PodManager(auth.api_base, auth)


def test_fetch_sessions_calls_the_member_route(tmp_path, monkeypatch):
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs['headers']))
        return Response(200, {'sessions': [SESSION, {'title': 'no start'}]})

    monkeypatch.setattr(pod_manager.requests, 'get', get)
    assert manager(tmp_path).fetch_sessions() == [SESSION]
    assert calls == [('https://platform.example/api/compute/ais/me/sessions', {'Authorization': 'Bearer plat_abc'})]


def test_old_server_returns_none_and_expired_token_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(pod_manager.requests, 'get', lambda url, **kw: Response(404, {}))
    assert manager(tmp_path).fetch_sessions() is None
    monkeypatch.setattr(pod_manager.requests, 'get', lambda url, **kw: Response(401, {'error': 'expired'}))
    with pytest.raises(pod_manager.ApiError) as e:
        manager(tmp_path).fetch_sessions()
    assert e.value.kind == pod_manager.EXPIRED


def test_starts_in_text():
    assert starts_in(SESSION, NOW) == 'starts in 2 h 5 min'
    assert starts_in(SESSION, NOW + datetime.timedelta(hours=3)) == 'now'
    assert starts_in({**SESSION, 'start_at': '2026-10-23T15:00:00Z'}, NOW) == 'starts in 2 d'
    assert starts_in({**SESSION, 'start_at': '2026-10-21T15:00:30+00:00'}, NOW) == 'starts in 0 min'


def test_next_session_line_names_the_pod_and_time():
    line = PodManager.next_session_line([SESSION], NOW)
    assert line.startswith('Next session: Intro to CUDA on workshop, ')
    assert line.endswith('(starts in 2 h 5 min)')
    assert PodManager.next_session_line([], NOW) == ''


def test_connect_with_no_running_pod_prints_the_next_session(tmp_path, monkeypatch, capsys):
    from godfather_cli import cli as cli_module

    monkeypatch.setattr(cli_module.Path, 'home', lambda: tmp_path)
    monkeypatch.delenv('GODFATHER_API_URL', raising=False)
    monkeypatch.setattr(cli_module, 'is_interactive', lambda: True)
    godfather = cli_module.GodfatherCLI()
    monkeypatch.setattr(godfather.pod_manager, 'fetch_pods', lambda: [{'id': 'pod1', 'status': 'EXITED'}])
    monkeypatch.setattr(godfather.pod_manager, 'fetch_sessions', lambda: [SESSION])
    assert godfather.choose_pod() is None
    out = capsys.readouterr().out
    assert 'None of your pods are running.' in out
    assert 'Next session: Intro to CUDA on workshop' in out


def test_menus_offer_sessions(tmp_path, monkeypatch):
    from godfather_cli import cli as cli_module
    from godfather_cli.picker import SESSIONS, menu_options

    actions = [action for action, _, _ in menu_options(True)]
    assert actions.index(SESSIONS) == actions.index('list') + 1

    monkeypatch.setattr(cli_module.Path, 'home', lambda: tmp_path)
    monkeypatch.delenv('GODFATHER_API_URL', raising=False)
    godfather = cli_module.GodfatherCLI()
    answers = iter(['5', '6'])
    ran = []
    monkeypatch.setattr(cli_module.Prompt, 'ask', lambda *a, **kw: next(answers))
    monkeypatch.setattr(godfather, 'run_action', ran.append)
    godfather.plain_menu()
    assert ran == [SESSIONS]


def test_end_time_on_the_same_day_shows_only_the_time():
    from godfather_cli.pod_manager import local_time

    start, stop = '2026-10-21T12:00:00+00:00', '2026-10-21T13:00:00+00:00'
    assert len(local_time(stop, same_day_as=start)) == len('13:00')
    assert local_time(stop).count(' ') == 3
    assert local_time('not a time') == ''
