"""tw 2.21.0: tw -u kept nobody's config: update is remove + install, remove deletes every file the
manifest lists, and installers list their .rc. The new installer then found no rc and copied
its stock one in. tw2nb lost project_notebooks/annotations_in/tasknote_in this way on
2026-11-03. An update now keeps the app's config files; if the new installer writes its own
anyway, the user's stays and the stock one is saved beside it as <name>.new.

Throwaway HOME only; nothing here runs a real installer.
"""
import importlib.machinery
import importlib.util
from pathlib import Path

import pytest

TW = Path(__file__).resolve().parent.parent / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli_cfg', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_cfg', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)


class Meta(dict):
    pass


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    (tmp_path / '.task' / 'hooks').mkdir()
    am = tw.AppManager(tw.PathManager())
    am.hook = tmp_path / '.task' / 'hooks' / 'on-add_x.py'
    am.hook.write_text('old hook\n')
    am.rc = tmp_path / '.task' / 'config' / 'x.rc'
    am.rc.write_text('x.mode = mine\n')
    am.manifest.add('x', '1.0', str(am.hook))
    am.manifest.add('x', '1.0', str(am.rc))
    stage = tmp_path / 'stage'
    stage.mkdir()
    monkeypatch.setattr(am.registry, 'get_meta', lambda name: Meta(version='2.0'))
    monkeypatch.setattr(am, '_stage_downloads', lambda name, meta: stage)
    monkeypatch.setattr(am, '_station_notes', lambda name, meta: None)

    def remove(name):                      # what an installer's remove does: every listed file
        for f in am.manifest.get_files(name):
            Path(f).unlink(missing_ok=True)
        am.manifest.remove_app(name)
        return True
    monkeypatch.setattr(am, 'remove', remove)
    return am


def _installer(app, guarded):
    def install(name, stage_dir=None):
        app.hook.write_text('new hook\n')
        if not (guarded and app.rc.exists()):
            app.rc.write_text('x.mode = stock\n')
        app.manifest.add('x', '2.0', str(app.hook))
        app.manifest.add('x', '2.0', str(app.rc))
        return True
    return install


def test_update_keeps_config_with_a_guarded_installer(app, monkeypatch):
    monkeypatch.setattr(app, 'install', _installer(app, guarded=True))
    assert app.update('x') is True
    assert app.hook.read_text() == 'new hook\n'
    assert app.rc.read_text() == 'x.mode = mine\n'
    assert not app.rc.with_name('x.rc.new').exists(), 'nothing to compare: installer kept it'


def test_update_keeps_config_when_installer_overwrites(app, monkeypatch):
    monkeypatch.setattr(app, 'install', _installer(app, guarded=False))
    assert app.update('x') is True
    assert app.rc.read_text() == 'x.mode = mine\n'
    assert app.rc.with_name('x.rc.new').read_text() == 'x.mode = stock\n'


def test_plain_remove_still_removes_config(app):
    """tw -r is an uninstall: its config goes too (unchanged behaviour)."""
    assert app.remove('x') is True
    assert not app.rc.exists()
