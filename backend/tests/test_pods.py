import os
import time

from domains.auth import tokens
from domains.auth.service import AuthService
from domains.pods import service as pod_service
from domains.pods.service import PodService


def admin_headers(monkeypatch):
    monkeypatch.setattr(AuthService, 'get_guild_member', staticmethod(lambda uid: {'roles': ['2000']}))
    token = tokens.sign({'sub': '123', 'exp': time.time() + 60}, os.environ['GODFATHER_TOKEN_SECRET'])
    return {'Authorization': f'Bearer {token}'}


class Recorder:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        self.docs.append(doc)


def test_cpu_pod_uses_instance_id(client, ssh_keys, monkeypatch):
    calls = []
    monkeypatch.setattr(pod_service.runpod, 'create_pod', lambda **kw: calls.append(kw) or {'id': 'p1'})
    monkeypatch.setattr(pod_service, 'pods_collection', Recorder())

    response = client.post('/api/pods', headers=admin_headers(monkeypatch), json={
        'name': 'cpu', 'use_cpu_only': True, 'instance_ids': ['cpu3c-4-8']
    })

    assert response.status_code == 200
    kwargs = calls[0]
    assert kwargs['gpu_type_id'] is None
    assert kwargs['instance_id'] == 'cpu3c-4-8'
    assert 'instanceIds' not in kwargs and 'computeType' not in kwargs
    assert kwargs['env']['GODFATHER_SSH_CA_PUBLIC_KEY'].startswith('ssh-ed25519 ')


def test_gpu_pod_keeps_gpu_type(client, ssh_keys, monkeypatch):
    calls = []
    monkeypatch.setattr(pod_service.runpod, 'create_pod', lambda **kw: calls.append(kw) or {'id': 'p2'})
    monkeypatch.setattr(pod_service, 'pods_collection', Recorder())

    response = client.post('/api/pods', headers=admin_headers(monkeypatch), json={'name': 'gpu'})

    assert response.status_code == 200
    assert calls[0]['gpu_type_id'] == 'NVIDIA RTX A4000'
    assert 'instance_id' not in calls[0]


def test_connect_requires_public_key(client, monkeypatch):
    headers = admin_headers(monkeypatch)
    response = client.post('/api/pods/p1/connect', headers=headers, json={})
    assert response.status_code == 400


def test_connect_denies_member_without_access(client, ssh_keys, monkeypatch, tmp_path):
    import subprocess
    subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(tmp_path / 'k')], check=True)
    public_key = (tmp_path / 'k.pub').read_text().strip()

    from domains.discord.service import DiscordService
    monkeypatch.setattr(AuthService, 'get_guild_member', staticmethod(lambda uid: {'roles': []}))
    monkeypatch.setattr(DiscordService, 'get_member', staticmethod(lambda uid: {'roles': [], 'user': {'username': 'm'}}))
    monkeypatch.setattr(PodService, 'check_pod_access', staticmethod(lambda pod_id, uid: False))
    token = tokens.sign({'sub': '5', 'exp': time.time() + 60}, os.environ['GODFATHER_TOKEN_SECRET'])

    response = client.post('/api/pods/p1/connect', headers={'Authorization': f'Bearer {token}'},
                           json={'public_key': public_key})
    assert response.status_code == 403


def test_connect_issues_certificate(client, ssh_keys, monkeypatch, tmp_path):
    import subprocess
    subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(tmp_path / 'k')], check=True)
    public_key = (tmp_path / 'k.pub').read_text().strip()

    from domains.discord.service import DiscordService
    monkeypatch.setattr(AuthService, 'get_guild_member', staticmethod(lambda uid: {'roles': []}))
    monkeypatch.setattr(DiscordService, 'get_member',
                        staticmethod(lambda uid: {'roles': [], 'user': {'username': 'Alice'}}))
    monkeypatch.setattr(PodService, 'check_pod_access', staticmethod(lambda pod_id, uid: True))
    monkeypatch.setattr(PodService, 'get_pod_ssh_info',
                        staticmethod(lambda pod_id: {'host': '1.2.3.4', 'port': 2222, 'username': 'root'}))
    token = tokens.sign({'sub': '5', 'exp': time.time() + 60}, os.environ['GODFATHER_TOKEN_SECRET'])

    response = client.post('/api/pods/p1/connect', headers={'Authorization': f'Bearer {token}'},
                           json={'public_key': public_key})
    assert response.status_code == 200
    info = response.get_json()['ssh_info']
    assert info['user_folder'] == 'alice'
    assert info['is_admin'] is False
    assert info['certificate'].startswith('ssh-ed25519-cert-v01@openssh.com ')
