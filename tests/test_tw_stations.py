"""tw 2.18.0: one ~/.task shared by stations (gittw), and what each station does with it.

- The manifest records paths the portable way (~/.task/...), so every station writes the same lines
  and the file can be shared; installers still see this station's absolute paths while they run.
- tw -l marks an installed app that isn't at work here [~]: its hooks aren't in this station's own
  hooks.location (tw-mobilize's hooks.d/<station>), hooks = off, or files outside ~/.task missing.
- platforms= in a .meta: an app marked for another kind of station is noted in tw -l and on install.

Throwaway HOME and TASKRC, real bash installers, no network.
"""
import importlib.machinery
import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader('tw_cli_stations', str(ROOT / 'tw'))
spec = importlib.util.spec_from_loader('tw_cli_stations', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)

# A make-awesome style installer: records absolute paths, and its remove reads them back with
# `[ -f "$file" ]` (25 registry installers do), so it must never see a ~ path.
INSTALLER = '''#!/bin/bash
M="$CONFIG_DIR/.tw_manifest"
case "$1" in
install)
    cp "$M" "$HOME/seen-by-installer" 2>/dev/null || true
    mkdir -p "$HOOKS_DIR"
    for h in on-add_two.py on-exit_two.py; do echo x > "$HOOKS_DIR/$h"; echo "two|1|$HOOKS_DIR/$h||now" >> "$M"; done
    ;;
remove)
    grep "^two|" "$M" | cut -d"|" -f3 | while read -r file; do
        if [ -f "$file" ]; then rm "$file"; fi
    done
    sed -i "/^two|/d" "$M"
    ;;
esac
'''


def write_station(home, local_rc):
    task = home / '.task'
    (task / 'config').mkdir(parents=True, exist_ok=True)
    (task / 'local.rc').write_text(local_rc)
    (home / '.taskrc').write_text(f'data.location={task}\ninclude {task}/local.rc\n')


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.delenv('TASKRC', raising=False)
    write_station(tmp_path, '')
    return tmp_path


def manager(home, installer=None):
    paths = tw.PathManager()
    paths.is_dev_mode, paths.registry_dir = False, None
    am = tw.AppManager(paths)
    am.registry.get_meta = lambda name: None
    if installer:       # dev mode: install and remove run the installer where it is
        paths.is_dev_mode = True
        (home / 'installers').mkdir(exist_ok=True)
        path = home / 'installers' / 'two.install'
        path.write_text(installer)
        am.registry.get_installer = lambda n, dest_dir=None: path
    else:
        am.registry.get_installer = lambda n, dest_dir=None: None
    return am


def manifest_path(home):
    return home / '.task' / 'config' / '.tw_manifest'


# ── portable manifest ─────────────────────────────────────────────────────────

def test_portable_paths():
    h = str(Path.home())
    assert tw._portable(f'{h}/.task/hooks/on-add_x.py') == '~/.task/hooks/on-add_x.py'
    assert tw._portable('/data/data/com.termux/files/home/.task/scripts/x') == '~/.task/scripts/x'
    assert tw._portable(f'{h}/.config/systemd/user/x.timer') == '~/.config/systemd/user/x.timer'
    assert tw._portable('https://github.com/x/y.git') == 'https://github.com/x/y.git'
    assert tw._portable('/etc/x') == '/etc/x'


def test_older_manifest_is_rewritten_portable_once(home):
    """yoga's lines (absolute, its own home) read on s5 (another home) mean s5's ~/.task."""
    manifest_path(home).write_text(
        'a|1|/home/djp/.task/hooks/on-add_a.py||t\n'
        f'a|1|{home}/.task/docs/a_README.md||t\n'
        'v|1|https://github.com/x/v.git||t\n')
    am = manager(home)
    assert am.manifest.get_files('a') == [f'{home}/.task/hooks/on-add_a.py', f'{home}/.task/docs/a_README.md']
    assert manifest_path(home).read_text() == (
        'a|1|~/.task/hooks/on-add_a.py||t\n'
        'a|1|~/.task/docs/a_README.md||t\n'
        'v|1|https://github.com/x/v.git||t\n')
    before = manifest_path(home).stat().st_mtime_ns
    manager(home)
    assert manifest_path(home).stat().st_mtime_ns == before      # already portable: not rewritten


def test_installer_sees_absolute_paths_and_the_file_ends_portable(home):
    manifest_path(home).write_text('a|1|~/.task/scripts/a||t\n')
    am = manager(home, INSTALLER)
    assert am.install('two')
    assert (home / 'seen-by-installer').read_text() == f'a|1|{home}/.task/scripts/a||t\n'
    lines = manifest_path(home).read_text().splitlines()
    assert lines[0] == 'a|1|~/.task/scripts/a||t'
    assert [l.split('|')[2] for l in lines[1:]] == ['~/.task/hooks/on-add_two.py', '~/.task/hooks/on-exit_two.py']
    assert am.manifest.get_files('two') == [f'{home}/.task/hooks/on-add_two.py', f'{home}/.task/hooks/on-exit_two.py']

    # its remove reads the paths back with [ -f "$file" ]: the files go
    assert manager(home, INSTALLER).remove('two')
    assert not (home / '.task' / 'hooks' / 'on-add_two.py').exists()
    assert manifest_path(home).read_text() == 'a|1|~/.task/scripts/a||t\n'


# ── this station ──────────────────────────────────────────────────────────────

def s5(home, hooks_on='on', linked=('on-add_two.py',)):
    """A station with its own hook list, as tw-mobilize writes it."""
    write_station(home, f'gittw.device = s5\ntw.platforms = mobile\nhooks = {hooks_on}\n'
                        'mobilize.hooks = need-priority, gittw\nhooks.location = ~/.task/hooks.d/s5\n')
    hooks = home / '.task' / 'hooks'
    own = home / '.task' / 'hooks.d' / 's5'
    hooks.mkdir(parents=True, exist_ok=True)
    own.mkdir(parents=True, exist_ok=True)
    for h in ('on-add_two.py', 'on-exit_two.py', 'on-add_one.py'):
        (hooks / h).write_text('x')
    for h in linked:
        (own / h).symlink_to(os.path.relpath(hooks / h, own))
    manifest_path(home).write_text(
        'two|1|~/.task/hooks/on-add_two.py||t\ntwo|1|~/.task/hooks/on-exit_two.py||t\n'
        'one|1|~/.task/hooks/on-add_one.py||t\n'
        'timer|1|~/.config/systemd/user/x.timer||t\n'
        'plain|1|~/.task/hooks/on-add_two.py||t\n')


def test_not_here_reasons(home):
    s5(home)
    am = manager(home)
    assert am.station_hooks_dir() == home / '.task' / 'hooks.d' / 's5'
    assert am.not_here('two') == '1 of 2 hooks run here'
    assert am.not_here('one') == "its hooks don't run here (~/.task/hooks.d/s5)"
    assert am.not_here('timer') == '1 file(s) not on this station'


def test_hooks_off_and_default_station(home):
    s5(home, hooks_on='off')
    assert manager(home).not_here('two') == 'hooks = off here'
    write_station(home, 'gittw.device = yoga\n')          # runs ~/.task/hooks: everything is at work
    am = manager(home)
    assert am.station_hooks_dir() is None
    assert am.not_here('one') is None


def test_platforms():
    am = tw.AppManager.__new__(tw.AppManager)
    am.rc = type('RC', (), {'get': lambda self, k, d='': {'tw.platforms': 'mobile'}.get(k, d)})()
    meta = tw.MetaFile.from_text
    assert am.not_for_here(meta('platforms=desktop')) == 'desktop only'
    assert am.not_for_here(meta('platforms=desktop, mobile')) is None
    assert am.not_for_here(meta('name=x')) is None


def test_list_marks_what_isnt_at_work_here(home, capsys):
    s5(home)
    am = manager(home)
    metas = {'two': 'version=1', 'one': 'version=1\nplatforms=desktop', 'timer': 'version=1', 'plain': 'version=1',
             'new': 'version=1\nplatforms=desktop'}
    am.registry.list_apps = lambda: list(metas)
    am.registry.get_metas = lambda names: {n: tw.MetaFile.from_text(metas[n]) for n in names}
    am.list_installed()
    out = capsys.readouterr().out
    assert '[~] two (v1)  (1 of 2 hooks run here)' in out
    assert "[~] one (v1)  (its hooks don't run here (~/.task/hooks.d/s5); desktop only)" in out
    assert '[ ] new (v1)  (desktop only)' in out
    assert '[~] installed, not at work on this station' in out
    assert 'Station s5 (mobile) runs its own hook list, ~/.task/hooks.d/s5' in out


def test_install_says_how_to_run_the_hooks_here(home, capsys):
    s5(home, linked=())
    (home / '.task' / 'hooks' / 'on-add_two.py').unlink()
    (home / '.task' / 'hooks' / 'on-exit_two.py').unlink()
    manifest_path(home).write_text('')
    am = manager(home, INSTALLER)
    assert am.install('two')
    out = capsys.readouterr().out
    assert "mobilize hooks --set 'need-priority, gittw, two'" in out
