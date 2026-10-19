"""tw 2.16.0: step 4 of the 2026-10-18 consolidation plan (nb tw:tw_consolidation_plan_—_2026-10-18.md).

- One _fetch() for every download (urllib; was urllib→tempfile twice and curl subprocesses).
- registry.d/index.json (make-awesome.py writes it) gives tw every .meta in one request; without
  it tw falls back to the GitHub API listing and one fetch per .meta.
- MetaFile.from_text: one parser for files and index entries.
- The manifest is the one record of what's installed (Manifest.apps); update backups keep each
  file's whole path, so two files with one name never share a backup.
- One installer environment for install and remove; staged and downloaded installers cleaned up.

Throwaway HOME, fake downloads, no network.
"""
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TW = ROOT / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli_registry', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_registry', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)


def load_make_awesome():
    ld = importlib.machinery.SourceFileLoader('make_awesome_for_tests', str(ROOT / 'make-awesome.py'))
    sp = importlib.util.spec_from_loader('make_awesome_for_tests', ld)
    mod = importlib.util.module_from_spec(sp)
    ld.exec_module(mod)
    return mod


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.delenv('TASKRC', raising=False)
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    return tmp_path


@pytest.fixture
def remote(home, monkeypatch):
    """Production mode (no local registry) with downloads served from a dict: url -> bytes."""
    served, fetched = {}, []
    def fetch(url, timeout=30, headers=None):
        fetched.append(url)
        return served.get(url)
    monkeypatch.setattr(tw, '_fetch', fetch)
    paths = tw.PathManager()
    paths.is_dev_mode, paths.registry_dir = False, None
    class R:
        pass
    r = R()
    r.served, r.fetched, r.paths = served, fetched, paths
    return r


META_A = 'name=a\nversion=1.0\ntags=hook,python\nfiles=on-add_a.py:hook\n'
META_B = 'name=b\nversion=2.0\ntags=script\nfiles=b.sh:script\n'


# ── _fetch ───────────────────────────────────────────────────────────────────

def test_fetch_reads_and_fails_quietly(tmp_path):
    f = tmp_path / 'x.txt'
    f.write_bytes(b'hello')
    assert tw._fetch(f.as_uri()) == b'hello'
    assert tw._fetch((tmp_path / 'nope').as_uri()) is None
    assert tw._fetch('not a url') is None


# ── the registry index ───────────────────────────────────────────────────────

def test_index_is_one_request(remote):
    remote.served[tw.RegistryManager.INDEX_URL] = json.dumps(
        {'format': 1, 'metas': {'b': META_B, 'a': META_A}}).encode()
    reg = tw.RegistryManager(remote.paths)
    assert reg.list_apps() == ['a', 'b']
    metas = reg.get_metas(reg.list_apps())
    assert metas['a'].get('version') == '1.0' and metas['b'].get_tags() == ['script']
    assert remote.fetched == [tw.RegistryManager.INDEX_URL]


def test_without_index_falls_back_to_api_and_raw(remote):
    remote.served[f"{tw.GITHUB_API_BASE}/contents/registry.d"] = json.dumps(
        [{'name': 'a.meta'}, {'name': 'index.json'}, {'name': 'b.meta'}]).encode()
    remote.served[f"{tw.GITHUB_RAW_BASE}/registry.d/a.meta"] = META_A.encode()
    reg = tw.RegistryManager(remote.paths)
    assert reg.list_apps() == ['a', 'b']
    assert reg.get_meta('a').get('name') == 'a'
    assert reg.get_meta('b') is None                    # not served
    assert remote.fetched.count(tw.RegistryManager.INDEX_URL) == 1     # tried once per run


def test_unreadable_index_falls_back(remote):
    remote.served[tw.RegistryManager.INDEX_URL] = b'<html>rate limited</html>'
    remote.served[f"{tw.GITHUB_RAW_BASE}/registry.d/a.meta"] = META_A.encode()
    assert tw.RegistryManager(remote.paths).get_meta('a').get('version') == '1.0'


def test_meta_from_text_matches_file(tmp_path):
    p = tmp_path / 'a.meta'
    p.write_text('# comment\n' + META_A + 'checksums=x, y\n')
    assert tw.MetaFile(p).data == tw.MetaFile.from_text(p.read_text()).data
    assert tw.MetaFile.from_text(META_A).get_files() == [('on-add_a.py', 'hook')]


def test_index_matches_registry():
    """registry.d/index.json is what make-awesome.py --index would write: run it after editing a .meta."""
    ma = load_make_awesome()
    index = ROOT / 'registry.d' / 'index.json'
    assert index.read_text() == ma.registry_index_text(ROOT), \
        'registry.d/index.json is stale: run python3 make-awesome.py --index'


def test_index_round_trips_through_tw(tmp_path):
    ma = load_make_awesome()
    (tmp_path / 'registry.d').mkdir()
    (tmp_path / 'registry.d' / 'a.meta').write_text(META_A)
    assert ma.write_registry_index(tmp_path) is True
    assert ma.write_registry_index(tmp_path) is False          # unchanged: no rewrite
    metas = json.loads((tmp_path / 'registry.d' / 'index.json').read_text())['metas']
    assert tw.MetaFile.from_text(metas['a']).get_tags() == ['hook', 'python']


# ── the manifest ─────────────────────────────────────────────────────────────

def test_manifest_apps(home):
    m = tw.Manifest(home / '.task' / 'config' / '.tw_manifest')
    m.add('x', '1.0', '/a/x1')
    m.add('y', '2.0', '/a/y')
    m.add('x', '1.0', '/a/x2')
    assert m.apps() == {'x': '1.0', 'y': '2.0'}
    assert tw.get_installed_extensions(tw.PathManager()) == {'x': '1.0', 'y': '2.0'}


# ── staging ──────────────────────────────────────────────────────────────────

def staged_meta(files, checksums):
    return tw.MetaFile.from_text(f'name=s\nversion=1\nbase_url=https://x.test/s/\n'
                                 f'files={files}\nchecksums={checksums}\n')


def test_stage_downloads_verifies_and_stages_the_installer(remote):
    remote.served.update({'https://x.test/s/s.py': b'code', 'https://x.test/s/README.md': b'doc',
                          f"{tw.GITHUB_RAW_BASE}/installers/s.install": b'#!/bin/bash\n'})
    good = hashlib.sha256(b'code').hexdigest()
    am = tw.AppManager(remote.paths)
    stage = am._stage_downloads('s', staged_meta('s.py:script,README.md:doc', f'{good},wrong'))
    try:
        assert (stage / 's.py').read_bytes() == b'code'
        assert (stage / 'README.md').read_bytes() == b'doc'           # docs aren't checked
        assert (stage / 's.install').stat().st_mode & 0o111
    finally:
        import shutil
        shutil.rmtree(stage)


def test_stage_downloads_refuses_a_bad_checksum(remote, tmp_path, monkeypatch):
    remote.served['https://x.test/s/s.py'] = b'tampered'
    made = []
    real = tw.tempfile.mkdtemp
    monkeypatch.setattr(tw.tempfile, 'mkdtemp', lambda **k: made.append(real(**k)) or made[-1])
    am = tw.AppManager(remote.paths)
    assert am._stage_downloads('s', staged_meta('s.py:script', hashlib.sha256(b'code').hexdigest())) is None
    assert made and not Path(made[0]).exists()


def test_stage_downloads_missing_file(remote):
    am = tw.AppManager(remote.paths)
    assert am._stage_downloads('s', staged_meta('s.py:script', '')) is None


# ── install / remove ─────────────────────────────────────────────────────────

INSTALLER = '#!/bin/bash\necho "$1 $HOOKS_DIR $TASKRC $TW_DRY_RUN" >> "{log}"\nexit {rc}\n'


def test_install_runs_the_staged_installer_and_cleans_up(remote, home, monkeypatch):
    log = home / 'installer.log'
    stage = home / 'stage'
    stage.mkdir()
    (stage / 's.install').write_text(INSTALLER.format(log=log, rc=0))
    am = tw.AppManager(remote.paths)
    monkeypatch.setattr(am.registry, 'get_meta', lambda n: staged_meta('s.py:script', ''))
    monkeypatch.setattr(am, '_stage_downloads', lambda n, m: stage)
    assert am.install('s') is True
    assert log.read_text().split()[:3] == ['install', str(home / '.task' / 'hooks'),
                                           str(home / '.taskrc')]
    assert not stage.exists()                          # its own stage: removed


def test_install_keeps_a_callers_stage(remote, home):
    stage = home / 'stage'
    stage.mkdir()
    (stage / 's.install').write_text(INSTALLER.format(log=home / 'log', rc=1))
    assert tw.AppManager(remote.paths).install('s', stage_dir=stage) is False
    assert stage.exists()                              # tw -u owns it


def test_remove_cleans_up_the_downloaded_installer(remote, home):
    log = home / 'installer.log'
    remote.served[f"{tw.GITHUB_RAW_BASE}/installers/s.install"] = INSTALLER.format(log=log, rc=0).encode()
    made = []
    am = tw.AppManager(remote.paths)
    real = am.registry.get_installer
    am.registry.get_installer = lambda n, dest_dir=None: made.append(real(n, dest_dir)) or made[-1]
    am.manifest.add('s', '1', str(home / 'gone.py'))
    assert am.remove('s') is True
    assert log.read_text().startswith('remove ')
    assert made and not made[0].parent.exists()
    assert not am.manifest.is_installed('s')


# ── update backups: whole paths ──────────────────────────────────────────────

def test_backup_keeps_same_named_files_apart(home):
    am = tw.AppManager(tw.PathManager())
    one = home / '.task' / 'docs' / 'README.md'
    two = home / '.task' / 'config' / 'README.md'
    for p, body in ((one, 'docs readme'), (two, 'config readme')):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
        am.manifest.add('z', '1', str(p))
    hook = home / '.task' / 'hooks' / 'on-add_z.py'
    hook.parent.mkdir(parents=True)
    hook.write_text('hook')
    hook.chmod(0o755)
    am.manifest.add('z', '1', str(hook))
    backup = am._backup_files('z')
    entries = [e.copy() for e in am.manifest.entries if e['app'] == 'z']
    for p in (one, two, hook):
        p.unlink()
    am._restore_files(backup, entries)
    assert one.read_text() == 'docs readme' and two.read_text() == 'config readme'
    assert hook.stat().st_mode & 0o111                 # mode kept by copy2


# ── verify: configs are reported modified; a version gap is said ─────────────

def test_verify_reports_modified_configs(home, capsys):
    hook = home / '.task' / 'hooks' / 'on-add_v.py'
    rc = home / '.task' / 'config' / 'v.rc'
    for p, body in ((hook, b'hook'), (rc, b'edited by the app')):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
    meta = tw.MetaFile.from_text('version=1.0\nfiles=on-add_v.py:hook,v.rc:config\nchecksums='
                                 f"{hashlib.sha256(b'hook').hexdigest()},{hashlib.sha256(b'shipped').hexdigest()}\n")
    am = tw.AppManager(tw.PathManager())
    am.registry.get_meta = lambda name: meta
    for p in (hook, rc):
        am.manifest.add('v', '1.0', str(p))
    assert am.verify('v') is True
    out = capsys.readouterr().out
    assert '[~] v.rc (modified)' in out and '(1 config file modified)' in out
    hook.write_bytes(b'tampered')
    assert am.verify('v') is False                      # a hook must still match
    assert 'on-add_v.py (checksum mismatch)' in capsys.readouterr().out


def test_verify_says_when_versions_differ(home, capsys):
    am = tw.AppManager(tw.PathManager())
    am.manifest.add('v', '1.0', str(home / 'x'))
    am.registry.get_meta = lambda name: tw.MetaFile.from_text('version=1.1\nfiles=x:script\nchecksums=abc\n')
    am.verify('v')
    assert "v1.0 is installed; these checksums are v1.1's" in capsys.readouterr().out


def test_help_topics_keep_their_indentation():
    assert '\n    tw> exec ls -la\n' in tw.HELP_TOPICS['shell']
    assert '\n     manifest says the installer put them' in tw.HELP_TOPICS['verify']
