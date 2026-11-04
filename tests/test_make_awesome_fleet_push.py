"""make-awesome 4.18.1: --fleet --push "msg" also ships what a clean repo hasn't got into the registry.

2026-11-04: the 4.18.0 template change regenerated 12 installers, each committed and pushed in its
own repo. --fleet --push skipped every one as "clean", so registry installers/ kept the old copies,
and agenda-edate's .meta (whose files= lists its own .install) kept a stale checksum, which tw
-u's verify rejects. Now the checksums are recomputed before the clean check, and a clean repo
whose .meta/.install differs from the registry copy is synced without a commit of its own.

Throwaway repos and a throwaway registry (SCRIPT_DIR is monkeypatched); nothing touches the real one.
"""
import hashlib
import importlib.machinery
import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_fleet_push', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_fleet_push', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)

HOOK = '#!/usr/bin/env python3\nprint("hi")\n'
INSTALL = '#!/usr/bin/env bash\nVERSION="1.0.0"\necho install\n'


def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def tracked_repo(d, remote):
    """d becomes a git repo with everything committed and pushed to remote, upstream set."""
    git('init', '-q', '--bare', str(remote))
    for cmd in (['init', '-q', '-b', 'main'], ['config', 'user.email', 't@t'], ['config', 'user.name', 't'],
                ['add', '-A'], ['commit', '-qm', 'one'], ['remote', 'add', 'origin', str(remote)],
                ['push', '-q', '-u', 'origin', 'main']):
        git(*cmd, cwd=d)


def meta(install_listed, install_sum):
    files, sums = 'on-add_demo.py:hook', sha(HOOK)
    if install_listed:
        files, sums = files + ',demo.install:script', sums + ',' + install_sum
    return f'name=demo\nversion=1.0.0\nfiles={files}\nchecksums={sums}\n'


@pytest.fixture
def fleet(tmp_path, monkeypatch):
    """One app repo (committed, pushed, clean) and a registry holding copies of its .meta/.install."""
    app = tmp_path / 'tw-demo-hook'
    app.mkdir()
    (app / 'on-add_demo.py').write_text(HOOK)

    reg = tmp_path / 'registry'
    (reg / 'registry.d').mkdir(parents=True)
    (reg / 'installers').mkdir()
    monkeypatch.setattr(ma, 'SCRIPT_DIR', reg)

    def build(install_listed=False, registry_install=INSTALL, stale_sum=False):
        (app / 'demo.install').write_text(INSTALL)
        listed_sum = sha('old installer\n') if stale_sum else sha(INSTALL)
        (app / 'demo.meta').write_text(meta(install_listed, listed_sum))
        (reg / 'registry.d' / 'demo.meta').write_text((app / 'demo.meta').read_text())
        (reg / 'installers' / 'demo.install').write_text(registry_install)
        tracked_repo(app, tmp_path / 'app.git')
        tracked_repo(reg, tmp_path / 'reg.git')
        return [{'name': 'demo', 'path': app, 'skip': False}]

    return app, reg, build


def heads(*repos):
    return [git('rev-parse', 'HEAD', cwd=r).strip() for r in repos]


def test_clean_repo_with_a_newer_installer_syncs_the_registry(fleet):
    app, reg, build = fleet
    apps = build(registry_install='#!/usr/bin/env bash\nVERSION="0.9.0"\n')
    app_head, reg_head = heads(app, reg)
    assert ma.cmd_fleet_push(apps, 'sync installers') == 0
    assert heads(app)[0] == app_head                                  # nothing to commit in the app
    assert (reg / 'installers' / 'demo.install').read_text() == INSTALL
    assert heads(reg)[0] != reg_head
    assert git('status', '--porcelain', cwd=reg).strip() == ''         # committed (and pushed)
    assert git('rev-parse', 'origin/main', cwd=reg) == git('rev-parse', 'HEAD', cwd=reg)


def test_a_stale_checksum_makes_a_clean_repo_commit_its_meta(fleet):
    app, reg, build = fleet
    apps = build(install_listed=True, stale_sum=True)
    app_head = heads(app)[0]
    assert ma.cmd_fleet_push(apps, 'checksums') == 0
    assert sha(INSTALL) in (app / 'demo.meta').read_text()
    assert heads(app)[0] != app_head
    assert git('status', '--porcelain', cwd=app).strip() == ''
    assert (reg / 'registry.d' / 'demo.meta').read_text() == (app / 'demo.meta').read_text()


def test_clean_and_in_sync_is_skipped(fleet):
    app, reg, build = fleet
    apps = build()
    before = heads(app, reg)
    assert ma.cmd_fleet_push(apps, 'nothing') == 0
    assert heads(app, reg) == before


def test_dry_run_writes_no_checksum_and_syncs_nothing(fleet):
    app, reg, build = fleet
    apps = build(install_listed=True, stale_sum=True, registry_install='old\n')
    before, meta_before = heads(app, reg), (app / 'demo.meta').read_text()
    assert ma.cmd_fleet_push(apps, 'dry', dry_run=True) == 0
    assert (app / 'demo.meta').read_text() == meta_before
    assert (reg / 'installers' / 'demo.install').read_text() == 'old\n'
    assert heads(app, reg) == before


def test_ipush_skip_leaves_a_stale_meta_untouched(fleet, monkeypatch):
    app, reg, build = fleet
    apps = build(install_listed=True, stale_sum=True)
    before, meta_before = heads(app, reg), (app / 'demo.meta').read_text()
    monkeypatch.setattr(ma, '_ipush_prompt', lambda name, path: False)
    assert ma.cmd_fleet_push(apps, 'skip me', interactive=True) == 0
    assert (app / 'demo.meta').read_text() == meta_before
    assert heads(app, reg) == before
