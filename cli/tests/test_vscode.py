from pathlib import Path

from godfather_cli import cli as cli_module
from godfather_cli.ssh_connector import INCLUDE_MARK, SSHConnector, host_alias, host_block, replace_block, with_include

INFO = {
    'host': '203.0.113.7',
    'port': 22041,
    'username': 'root',
    'user_folder': 'alice',
    'is_admin': False,
    'certificate': 'ssh-ed25519-cert-v01@openssh.com AAAA cert',
}


def test_host_block_points_at_the_pod_certificate(tmp_path):
    block = host_block('godfather-pod1', INFO, tmp_path / 'id_ed25519', tmp_path / 'pod1-cert.pub')
    lines = block.splitlines()
    assert lines[0] == 'Host godfather-pod1'
    assert '    HostName 203.0.113.7' in lines
    assert '    Port 22041' in lines
    assert '    User root' in lines
    assert f'    CertificateFile "{(tmp_path / "pod1-cert.pub").as_posix()}"' in lines
    assert '    IdentitiesOnly yes' in lines


def test_replace_block_keeps_other_pods_and_replaces_the_same_pod():
    first = replace_block('', 'godfather-a', 'Host godfather-a\n    Port 1\n')
    both = replace_block(first, 'godfather-b', 'Host godfather-b\n    Port 2\n')
    renewed = replace_block(both, 'godfather-a', 'Host godfather-a\n    Port 3\n')
    assert renewed.count('Host godfather-a') == 1
    assert 'Port 1' not in renewed
    assert 'Port 2' in renewed and 'Port 3' in renewed


def test_with_include_goes_first_and_only_once(tmp_path):
    own = tmp_path / 'config'
    text = with_include('Host work\n    User me\n', own)
    assert text.splitlines()[0] == INCLUDE_MARK
    assert text.splitlines()[1] == f'Include "{own.as_posix()}"'
    assert text.endswith('Host work\n    User me\n')
    assert with_include(text, own) == text


def test_write_host_writes_both_files(tmp_path):
    connector = SSHConnector(tmp_path / '.godfather')
    connector.ssh_key_dir.mkdir(parents=True)
    ssh_config = tmp_path / '.ssh' / 'config'
    assert connector.write_host('pod1', INFO, ssh_config) == host_alias('pod1')
    assert 'Host godfather-pod1' in (connector.ssh_key_dir / 'config').read_text()
    assert ssh_config.read_text().count('Include') == 1
    connector.write_host('pod1', INFO, ssh_config)
    assert ssh_config.read_text().count('Include') == 1


def test_write_host_refuses_a_strange_pod_id(tmp_path):
    connector = SSHConnector(tmp_path / '.godfather')
    connector.ssh_key_dir.mkdir(parents=True)
    assert connector.write_host('pod1\nHost *', INFO, tmp_path / '.ssh' / 'config') is None


def test_setup_vscode_saves_a_certificate_for_each_pod(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_module.Path, 'home', lambda: tmp_path)
    monkeypatch.delenv('GODFATHER_API_URL', raising=False)
    monkeypatch.setattr(cli_module.shutil, 'which', lambda name: None)
    godfather = cli_module.GodfatherCLI()
    monkeypatch.setattr(godfather, 'ensure_authenticated', lambda: True)
    monkeypatch.setattr(godfather.ssh_connector, 'ensure_keypair', lambda: 'ssh-ed25519 AAAA')
    asked = []

    def fetch(pod_id, public_key, admin=False):
        asked.append((pod_id, admin))
        return INFO

    monkeypatch.setattr(godfather.pod_manager, 'fetch_connection_info', fetch)
    godfather.ssh_connector.ssh_key_dir.mkdir(parents=True)
    godfather.setup_vscode('pod1')
    godfather.setup_vscode('pod2', admin=True)

    assert asked == [('pod1', False), ('pod2', True)]
    key_dir = Path(godfather.ssh_connector.ssh_key_dir)
    assert (key_dir / 'pod1-cert.pub').read_text().startswith('ssh-ed25519-cert')
    assert (key_dir / 'pod2-cert.pub').exists()
    own = (key_dir / 'config').read_text()
    assert 'Host godfather-pod1' in own and 'Host godfather-pod2' in own
    assert (tmp_path / '.ssh' / 'config').exists()


def test_admin_flag_works_with_vscode(monkeypatch):
    calls = []
    monkeypatch.setattr(
        cli_module,
        'GodfatherCLI',
        lambda: type('C', (), {'setup_vscode': lambda s, p, admin: calls.append((p, admin))})(),
    )
    monkeypatch.setattr('sys.argv', ['godfather', 'vscode', 'pod1', '--admin'])
    cli_module.main()
    assert calls == [('pod1', True)]
