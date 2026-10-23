"""make-awesome 4.16.2: --push pushes commits already made, and the .meta's checksums are the files'.

2026-10-23: gittw 0.3.5 and mobilize 0.6.2 were committed before `make-awesome --push "msg"`. The
working tree was clean, so it said "nothing to commit" and pushed nothing; the registry went out
naming versions GitHub didn't have, with the old files' checksums. tw -u reinstalled the old code."""
import hashlib
import importlib.machinery
import importlib.util
import subprocess
from types import SimpleNamespace

ROOT = __import__('pathlib').Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_push_committed', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_push_committed', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)

META = '''name=demo
version=2.0.0
files=on-add_demo.py:hook
checksums={sum}
'''


def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def tracked_repo(tmp_path, monkeypatch):
    remote, d = tmp_path / 'remote.git', tmp_path / 'tw-demo-hook'
    git('init', '-q', '--bare', '-b', 'main', str(remote))
    d.mkdir()
    (d / 'on-add_demo.py').write_text('one\n')
    (d / 'demo.meta').write_text(META.format(sum=hashlib.sha256(b'one\n').hexdigest()))
    for cmd in (['init', '-q', '-b', 'main'], ['config', 'user.email', 't@t'], ['config', 'user.name', 't'],
                ['add', '-A'], ['commit', '-qm', 'one'], ['remote', 'add', 'origin', str(remote)],
                ['push', '-q', '-u', 'origin', 'main']):
        git(*cmd, cwd=d)
    monkeypatch.chdir(d)
    return d, remote


def test_a_clean_tree_with_commits_ahead_is_pushed(tmp_path, monkeypatch):
    d, remote = tracked_repo(tmp_path, monkeypatch)
    (d / 'on-add_demo.py').write_text('two\n')
    git('commit', '-qam', '2.0.0', cwd=d)                       # committed by hand, before --push
    assert ma.push_project_repo('msg')
    assert git('rev-parse', 'main', cwd=remote) == git('rev-parse', 'HEAD', cwd=d)


def test_a_clean_tree_level_with_its_remote_pushes_nothing(tmp_path, monkeypatch):
    d, remote = tracked_repo(tmp_path, monkeypatch)
    before = git('rev-parse', 'main', cwd=remote)
    assert ma.push_project_repo('msg')
    assert git('rev-parse', 'main', cwd=remote) == before


def test_push_brings_the_meta_checksums_up_to_date_first(tmp_path, monkeypatch):
    d, _ = tracked_repo(tmp_path, monkeypatch)
    (d / 'on-add_demo.py').write_text('two\n')
    seen = {}
    monkeypatch.setattr(ma, 'push_project_repo', lambda m: seen.setdefault('meta', (d / 'demo.meta').read_text()) or True)
    monkeypatch.setattr(ma, 'push_registry', lambda name: True)    # never the real registry
    assert ma.cmd_push(SimpleNamespace(dry_run=False), 'msg') == 0
    assert hashlib.sha256(b'two\n').hexdigest() in seen['meta'], 'checksums before the project commit'
