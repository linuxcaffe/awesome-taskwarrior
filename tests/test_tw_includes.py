"""tw -r safety net: after an app is removed, any `include` left pointing at a missing file is
commented out, so `task` still starts. (2026-10-13: `tw -r daily-email` deleted daily-email.rc
but left its include; task, and tw-web, refused to start.)"""
import importlib.machinery
import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

TW = Path(__file__).resolve().parent.parent / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli', str(TW))
spec = importlib.util.spec_from_loader('tw_cli', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    return tmp_path


def rc_chain(home, included_lines):
    cfg = home / '.task' / 'config'
    (cfg / 'keep.rc').write_text('keep.x=1\n')
    (cfg / 'included.rc').write_text(''.join(l + '\n' for l in included_lines))
    top = home / '.taskrc'
    top.write_text(f'data.location={home}/.task\nhooks=off\ninclude ~/.task/config/included.rc\n')
    return top, cfg / 'included.rc'


def test_dangling_include_is_commented_out(home):
    top, inc = rc_chain(home, ['include ~/.task/config/keep.rc', 'include ~/.task/config/daily-email.rc'])
    fixed = tw.repair_dangling_includes(top, note='tw -r daily-email')
    assert len(fixed) == 1 and 'daily-email.rc' in fixed[0]
    lines = inc.read_text().splitlines()
    assert lines[0] == 'include ~/.task/config/keep.rc'
    assert lines[1].startswith('#include ~/.task/config/daily-email.rc') and 'tw -r daily-email' in lines[1]


def test_nothing_to_fix_leaves_files_untouched(home):
    top, inc = rc_chain(home, ['include ~/.task/config/keep.rc', '#include ~/.task/config/old.rc'])
    before = inc.read_bytes(), top.read_bytes()
    assert tw.repair_dangling_includes(top) == []
    assert (inc.read_bytes(), top.read_bytes()) == before


def test_relative_and_system_includes_count_as_found(home):
    top, inc = rc_chain(home, ['include keep.rc'])          # relative to included.rc's folder
    if Path('/usr/share/taskwarrior/dark-256.theme').exists():
        inc.write_text(inc.read_text() + 'include dark-256.theme\n')
    assert tw.repair_dangling_includes(top) == []


def test_missing_in_top_rc_too(home):
    top, _ = rc_chain(home, [])
    top.write_text(top.read_text() + 'include ~/.task/config/gone.rc\n')
    assert len(tw.repair_dangling_includes(top)) == 1
    assert '#include ~/.task/config/gone.rc' in top.read_text()


def test_symlinked_taskrc_is_edited_in_place(home):
    """gittw keeps .taskrc inside ~/.task and symlinks it: fix the target, keep the link."""
    real = home / '.task' / '.taskrc'
    real.write_text(f'data.location={home}/.task\nhooks=off\ninclude ~/.task/config/gone.rc\n')
    (home / '.taskrc').symlink_to(real)
    tw.repair_dangling_includes(home / '.taskrc')
    assert (home / '.taskrc').is_symlink() and '#include' in real.read_text()


@pytest.mark.skipif(not shutil.which('task'), reason='task not installed')
def test_task_starts_after_repair(home):
    top, _ = rc_chain(home, ['include ~/.task/config/daily-email.rc'])
    env = {'HOME': str(home), 'TASKRC': str(top), 'PATH': '/usr/bin:/bin'}
    broken = subprocess.run(['task', '_version'], capture_output=True, text=True, env=env)
    assert broken.returncode != 0 and 'Could not read include file' in broken.stderr
    tw.repair_dangling_includes(top)
    assert subprocess.run(['task', '_version'], capture_output=True, text=True, env=env).returncode == 0


def test_remove_runs_the_repair(home, monkeypatch):
    """AppManager.remove() repairs includes after the app's own remove step, whatever it did."""
    top, inc = rc_chain(home, ['include ~/.task/config/fake.rc'])
    (home / '.task' / 'config' / 'fake.rc').write_text('fake.x=1\n')
    installer = home / 'fake.install'
    installer.write_text(f'#!/bin/bash\n[ "$1" = remove ] && rm -f {home}/.task/config/fake.rc\nexit 0\n')
    paths = tw.PathManager()
    am = tw.AppManager(paths)
    monkeypatch.setattr(am.manifest, 'is_installed', lambda app: True)
    monkeypatch.setattr(am.manifest, 'remove_app', lambda app: None)
    monkeypatch.setattr(am.registry, 'get_installer', lambda app: installer)
    monkeypatch.setattr(paths, 'is_dev_mode', True)       # don't delete our installer as a temp file
    assert am.remove('fake') is True
    assert inc.read_text().startswith('#include ~/.task/config/fake.rc')
