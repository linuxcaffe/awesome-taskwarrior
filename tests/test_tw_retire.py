"""tw 2.17.0: an app installed earlier under another name stops claiming the new one's files.

- After an install, the files it lists are its own: any other app's manifest lines for them go,
  and an app left with nothing is retired (tw-recurrence 2.0.0 listed recurrence-overhaul's hooks).
- tw -r never removes a file another app lists too: skipped without an installer, put back when
  the installer's remove takes it anyway.
- tw -l shows installed apps the registry doesn't have, with how to retire them.

Throwaway HOME, real bash installers, no network.
"""
import importlib.machinery
import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader('tw_cli_retire', str(ROOT / 'tw'))
spec = importlib.util.spec_from_loader('tw_cli_retire', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)

# What make-awesome's installers do: copy the files, append manifest lines; remove deletes what
# the manifest lists for the app, then its lines.
INSTALLER = '''#!/bin/bash
M="$CONFIG_DIR/.tw_manifest"
case "$1" in
install)
    mkdir -p "$HOOKS_DIR" "$DOCS_DIR"
    echo new > "$HOOKS_DIR/on-add_x.py"; chmod +x "$HOOKS_DIR/on-add_x.py"
    echo new > "$DOCS_DIR/new_README.md"
    echo "new|2|$HOOKS_DIR/on-add_x.py||now" >> "$M"
    echo "new|2|$DOCS_DIR/new_README.md||now" >> "$M"
    ;;
remove)
    grep "^{app}|" "$M" | cut -d"|" -f3 | while read -r f; do rm -f "$f"; done
    sed -i "/^{app}|/d" "$M"
    ;;
esac
'''


@pytest.fixture
def am(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.delenv('TASKRC', raising=False)
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    paths = tw.PathManager()
    paths.is_dev_mode, paths.registry_dir = False, None
    manager = tw.AppManager(paths)
    manager.registry.get_installer = lambda n, dest_dir=None: None
    return manager


def old_install(am):
    """tw-recurrence 2.0.0 as it was: the same hook, plus a README of its own."""
    hooks, docs = am.paths.hooks_dir, am.paths.docs_dir
    hooks.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    (hooks / 'on-add_x.py').write_text('old')
    (docs / 'old_README.md').write_text('old doc')
    am.manifest.add('old', '1', str(hooks / 'on-add_x.py'))
    am.manifest.add('old', '1', str(docs / 'old_README.md'))


def stage(am, app='new'):
    d = am.paths.task_dir / 'stage'
    d.mkdir(exist_ok=True)
    (d / f'{app}.install').write_text(INSTALLER.replace('{app}', app))
    return d


def test_install_takes_over_the_old_apps_lines(am, capsys):
    old_install(am)
    assert am.install('new', stage_dir=stage(am))
    m = tw.Manifest(am.paths.manifest_file)
    assert m.get_files('old') == [str(am.paths.docs_dir / 'old_README.md')]
    assert str(am.paths.hooks_dir / 'on-add_x.py') in m.get_files('new')
    out = capsys.readouterr().out
    assert 'took over 1 file(s) old listed' in out and 'tw -r old' in out


def test_an_app_with_nothing_left_is_retired(am, capsys):
    am.paths.hooks_dir.mkdir(parents=True)
    am.manifest.add('old', '1', str(am.paths.hooks_dir / 'on-add_x.py'))
    assert am.install('new', stage_dir=stage(am))
    assert not tw.Manifest(am.paths.manifest_file).is_installed('old')
    assert 'Retired: old' in capsys.readouterr().out


def test_then_removing_the_old_app_leaves_the_new_ones_files(am):
    old_install(am)
    am.install('new', stage_dir=stage(am))
    am.manifest = tw.Manifest(am.paths.manifest_file)
    assert am.remove('old')
    assert (am.paths.hooks_dir / 'on-add_x.py').read_text() == 'new\n'
    assert not (am.paths.docs_dir / 'old_README.md').exists()
    assert tw.Manifest(am.paths.manifest_file).get_files('new')


def test_remove_without_an_installer_skips_shared_files(am, capsys):
    old_install(am)
    am.manifest.add('new', '2', str(am.paths.hooks_dir / 'on-add_x.py'))   # before any claim
    assert am.remove('old')
    assert (am.paths.hooks_dir / 'on-add_x.py').exists()
    assert not (am.paths.docs_dir / 'old_README.md').exists()
    assert 'Kept 1 file(s)' in capsys.readouterr().out


def test_remove_puts_back_what_an_installer_takes(am):
    old_install(am)
    hook = am.paths.hooks_dir / 'on-add_x.py'
    os.chmod(hook, 0o755)
    link = am.paths.hooks_dir / 'on-modify_x.py'
    link.symlink_to('on-add_x.py')
    am.manifest.add('old', '1', str(link))
    am.manifest.add('new', '2', str(hook))
    am.manifest.add('new', '2', str(link))
    d = stage(am, 'old')
    am.registry.get_installer = lambda n, dest_dir=None: d / 'old.install'
    am.paths.is_dev_mode = True                    # keep the stage; it's ours
    assert am.remove('old')
    assert hook.read_text() == 'old' and os.access(hook, os.X_OK)
    assert link.is_symlink() and os.readlink(link) == 'on-add_x.py'
    m = tw.Manifest(am.paths.manifest_file)
    assert not m.is_installed('old') and len(m.get_files('new')) == 2


def test_list_shows_apps_the_registry_lacks(am, capsys, monkeypatch):
    am.manifest.add('ghost', '0.1', '/nowhere')
    am.manifest.add('a', '1.0', '/a')
    monkeypatch.setattr(am.registry, 'list_apps', lambda: ['a'])
    monkeypatch.setattr(am.registry, 'get_metas', lambda apps: {
        'a': tw.MetaFile.from_text('name=a\nversion=1.0\nfiles=a:hook\n')})
    am.list_installed()
    out = capsys.readouterr().out
    assert '[?] ghost (v0.1) not in the registry; tw -r ghost retires it' in out
    assert '[?] a ' not in out
