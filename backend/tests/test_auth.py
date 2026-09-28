import os
import time

import pytest

from domains.auth import tokens
from domains.auth.service import AuthService


def bearer(sub='123', ttl=60, secret=None):
    token = tokens.sign({'sub': sub, 'exp': time.time() + ttl}, secret or os.environ['GODFATHER_TOKEN_SECRET'])
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def discord(monkeypatch):
    members = {}
    monkeypatch.setattr(AuthService, 'get_guild_member', staticmethod(lambda uid: members.get(uid)))
    return members


def test_header_user_id_is_not_trusted(client, discord):
    discord['123'] = {'roles': ['2000']}
    response = client.get('/api/pods', headers={'X-Discord-User-ID': '123'})
    assert response.status_code == 401


def test_me_requires_token(client, discord):
    assert client.get('/api/me').status_code == 401


def test_me_rejects_forged_token(client, discord):
    discord['123'] = {'roles': []}
    response = client.get('/api/me', headers=bearer(secret='z' * 40))
    assert response.status_code == 401


def test_me_rejects_non_member(client, discord):
    assert client.get('/api/me', headers=bearer()).status_code == 403


def test_me_reports_member(client, discord):
    discord['123'] = {'roles': []}
    response = client.get('/api/me', headers=bearer())
    assert response.status_code == 200
    assert response.get_json() == {'success': True, 'discord_user_id': '123', 'is_admin': False}


def test_admin_route_rejects_member(client, discord):
    discord['123'] = {'roles': []}
    assert client.get('/api/pods', headers=bearer()).status_code == 403


def test_ssh_key_endpoint_is_gone(client, discord):
    discord['123'] = {'roles': ['2000']}
    assert client.get('/api/ssh-key', headers=bearer()).status_code == 404
