"""make-awesome 4.14.0: a HANDCRAFTED installer is never regenerated, and --dry-run changes nothing.

2026-10-20: `--install` run in tw-smart-nag-hook checked for `tw-smart-nag-hook.install` (the folder's
name), found none, asked the meta questions and generated `smart-nag.install` over the handcrafted one.
And `--push --dry-run` committed and pushed, and the full pipeline with --dry-run wrote awesome.rc."""
import builtins
import hashlib
import importlib.machinery
import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_handcrafted', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_handcrafted', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)

HANDCRAFTED = '''#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# demo - Installer Script
#
# HANDCRAFTED — do not overwrite with make-awesome.py --install
# ============================================================================

VERSION="1.0.0"
APPNAME="demo"
echo "my own logic"
'''

META = '''# demo.meta
name=demo
version=2.0.0
type=hook
description=Demo
repo=https://github.com/someone/tw-demo-hook
base_url=https://raw.githubusercontent.com/someone/tw-demo-hook/main
files=on-add_demo.py:hook
checksums={sum}
'''

HOOK = '#!/usr/bin/env python3\nimport sys\nfor line in sys.stdin:\n    sys.stdout.write(line)\n'


def no_prompts(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError('make-awesome asked a question')
    monkeypatch.setattr(builtins, 'input', refuse)


def project(tmp_path, monkeypatch, folder='tw-demo-hook'):
    """A hook repo whose folder name differs from its app name, with a handcrafted installer."""
    d = tmp_path / folder
    d.mkdir()
    (d / 'on-add_demo.py').write_text(HOOK)
    (d / 'demo.meta').write_text(META.format(sum=hashlib.sha256(HOOK.encode()).hexdigest()))
    (d / 'demo.install').write_text(HANDCRAFTED)
    monkeypatch.chdir(d)
    return d


# ── The convention ────────────────────────────────────────────────────────────

@pytest.mark.parametrize('header', ['# HANDCRAFTED', '# HANDCRAFTED — do not overwrite', '#HANDCRAFTED'])
def test_marker_in_the_header_counts(tmp_path, header):
    f = tmp_path / 'x.install'
    f.write_text(f'#!/usr/bin/env bash\n{header}\nVERSION="1"\n')
    assert ma.is_handcrafted(f)


def test_marker_must_be_a_header_comment(tmp_path):
    f = tmp_path / 'x.install'
    f.write_text('#!/usr/bin/env bash\n' + 'echo hi\n' * 20 + '# HANDCRAFTED\n')
    assert not ma.is_handcrafted(f)                       # too far down: not the header
    f.write_text('#!/usr/bin/env bash\necho "HANDCRAFTED"\n')
    assert not ma.is_handcrafted(f)                       # not a comment
    assert not ma.is_handcrafted(tmp_path / 'missing.install')


def test_every_registry_installer_marked_handcrafted_uses_the_convention():
    for f in sorted((ROOT / 'installers').glob('*.install')):
        if 'HANDCRAFTED' in f.read_text():
            assert ma.is_handcrafted(f), f.name


# ── Bug 2: never regenerated ──────────────────────────────────────────────────

def test_generate_installer_refuses_to_overwrite_a_handcrafted_one(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    info = ma.ProjectInfo()
    info.name, info.version, info.repo = 'demo', '2.0.0', 'someone/tw-demo-hook'
    info.files = [('on-add_demo.py', 'hook')]
    info.checksums = ['abc']
    assert ma.generate_installer(info)
    assert Path('demo.install').read_text() == HANDCRAFTED


def test_install_in_a_folder_named_differently_keeps_the_handcrafted_installer(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    no_prompts(monkeypatch)
    assert ma.cmd_install(None) == 0
    text = Path('demo.install').read_text()
    assert 'echo "my own logic"' in text
    assert 'VERSION="2.0.0"' in text                      # synced from the meta, not the default 1.0.0
    assert not Path('tw-demo-hook.install').exists()


# ── Bug 1: --dry-run changes nothing ──────────────────────────────────────────

def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def repo_with_remote(tmp_path, monkeypatch):
    remote = tmp_path / 'remote.git'
    git('init', '-q', '--bare', str(remote))
    d = project(tmp_path, monkeypatch)
    for cmd in (['init', '-q'], ['config', 'user.email', 't@t'], ['config', 'user.name', 't'],
                ['add', '-A'], ['commit', '-qm', 'one'], ['remote', 'add', 'origin', str(remote)],
                ['push', '-q', 'origin', 'HEAD:main']):
        git(*cmd, cwd=d)
    (d / 'on-add_demo.py').write_text(HOOK + '# changed\n')
    return d, remote


def snapshot(*dirs):
    return {p: p.read_bytes() for d in dirs for p in sorted(Path(d).rglob('*'))
            if p.is_file() and '.git' not in p.parts}


def test_push_dry_run_commits_and_pushes_nothing(tmp_path, monkeypatch):
    d, remote = repo_with_remote(tmp_path, monkeypatch)
    no_prompts(monkeypatch)
    head, remote_head = git('rev-parse', 'HEAD', cwd=d), git('rev-parse', 'main', cwd=remote)
    before = snapshot(d, ROOT / 'registry.d', ROOT / 'installers')
    assert ma.cmd_push(SimpleNamespace(dry_run=True), 'msg') == 0
    assert git('rev-parse', 'HEAD', cwd=d) == head
    assert git('rev-parse', 'main', cwd=remote) == remote_head
    assert git('status', '--short', cwd=d).strip() == 'M on-add_demo.py'
    assert snapshot(d, ROOT / 'registry.d', ROOT / 'installers') == before


def test_pipeline_dry_run_changes_no_file(tmp_path, monkeypatch):
    d, remote = repo_with_remote(tmp_path, monkeypatch)
    no_prompts(monkeypatch)
    head = git('rev-parse', 'HEAD', cwd=d)
    before = snapshot(d, ROOT / 'registry.d', ROOT / 'installers')
    rc_before = (ROOT / 'awesome.rc').read_bytes()
    assert ma.cmd_pipeline('msg', SimpleNamespace(dry_run=True, force=False)) == 0
    assert git('rev-parse', 'HEAD', cwd=d) == head
    assert snapshot(d, ROOT / 'registry.d', ROOT / 'installers') == before
    assert (ROOT / 'awesome.rc').read_bytes() == rc_before


# ── The banner names the app the .meta describes ──────────────────────────────

def test_project_info_comes_from_the_meta(tmp_path, monkeypatch, capsys):
    project(tmp_path, monkeypatch)
    info = ma.detect_project_info()
    assert (info.name, info.version) == ('demo', '2.0.0')  # not the folder's name, not 1.0.0
    out = capsys.readouterr().out
    assert 'Project: demo' in out and 'Version: 2.0.0' in out


def test_docstring_version_matches_VERSION():
    assert f'Version: {ma.VERSION}' in ma.__doc__
