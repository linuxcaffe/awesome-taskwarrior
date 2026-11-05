"""tw 2.22.0: a ~/.task shared between stations (gittw), found 2026-11-04 on s5.

gittw merges config/.tw_manifest with git's union rule, so both stations' install lines are
kept. When s5 and yoga each updated tw2nb, the union kept both versions' lines. Three fixes:

- tw reads the manifest settled: an app listed at two versions keeps the newer version's lines
  (by the date on them), and a line listed twice is listed once; the file is rewritten.
- tw -I/-u/-r pull ~/.task first (gittw pull), so a station changes the latest manifest.
- tw.update_station (a shared rc key) names the one station that installs and updates; on any
  other (gittw.device), tw -I/-u/-r say so and ask, and refuse without a terminal.

Throwaway HOME only.
"""
import importlib.machinery
import importlib.util
from pathlib import Path

import pytest

TW = Path(__file__).resolve().parent.parent / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli_station', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_station', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)

MERGED = """\
tw2nb|1.4.2|~/.task/hooks/on-add_tw2nb.py||2026-11-05T02:47:08Z
tw2nb|1.4.2|~/.task/config/tw2nb.rc||2026-11-05T02:47:08Z
other|0.3|~/.task/scripts/other||2026-10-01T00:00:00Z
tw2nb|1.4.3|~/.task/hooks/on-add_tw2nb.py||2026-11-05T03:10:00Z
tw2nb|1.4.3|~/.task/config/tw2nb.rc||2026-11-05T03:10:00Z
tw2nb|1.4.3|~/.task/scripts/tw2nb_lib.py||2026-11-05T03:10:00Z
other|0.3|~/.task/scripts/other||2026-10-01T00:00:00Z
"""


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    for d in ('config', 'hooks', 'scripts'):
        (tmp_path / '.task' / d).mkdir(parents=True)
    return tmp_path


def _manifest(home):
    return home / '.task' / 'config' / '.tw_manifest'


# ── the manifest, settled ─────────────────────────────────────────────────────

def test_two_versions_of_an_app_keep_the_newer(home):
    _manifest(home).write_text(MERGED)
    m = tw.Manifest(_manifest(home))
    assert m.get_version('tw2nb') == '1.4.3'
    assert {e['version'] for e in m.entries if e['app'] == 'tw2nb'} == {'1.4.3'}
    assert len(m.get_files('tw2nb')) == 3


def test_a_line_listed_twice_is_listed_once(home):
    _manifest(home).write_text(MERGED)
    assert len(tw.Manifest(_manifest(home)).get_files('other')) == 1


def test_tw_rewrites_a_settled_manifest_and_says_so(home, capsys):
    _manifest(home).write_text(MERGED)
    tw.AppManager(tw.PathManager())
    text = _manifest(home).read_text()
    assert '1.4.2' not in text and text.count('scripts/other') == 1
    assert 'tw2nb' in capsys.readouterr().out          # one line naming what it settled


def test_a_clean_manifest_is_left_alone(home):
    clean = 'x|1.0|~/.task/hooks/on-add_x.py||2026-10-01T00:00:00Z\n'
    _manifest(home).write_text(clean)
    tw.AppManager(tw.PathManager())
    assert _manifest(home).read_text() == clean


# ── pull first ────────────────────────────────────────────────────────────────

def _gittw(home, rc=0):
    log = home / 'gittw.log'
    g = home / '.task' / 'scripts' / 'gittw'
    g.write_text(f'#!/bin/sh\necho "$@" >> {log}\nexit {rc}\n')
    g.chmod(0o755)
    return log


def test_a_shared_task_folder_is_pulled_first(home):
    (home / '.task' / '.git').mkdir()
    log = _gittw(home)
    am = tw.AppManager(tw.PathManager())
    assert am.pull_shared() is True
    assert log.read_text().split() == ['pull']


def test_no_git_no_pull(home):
    log = _gittw(home)
    assert tw.AppManager(tw.PathManager()).pull_shared() is False
    assert not log.exists()


def test_a_failed_pull_goes_on_with_this_stations_copy(home, capsys):
    (home / '.task' / '.git').mkdir()
    _gittw(home, rc=1)
    assert tw.AppManager(tw.PathManager()).pull_shared() is False
    assert "this station's copy" in capsys.readouterr().out


def test_the_manifest_is_read_again_after_the_pull(home):
    (home / '.task' / '.git').mkdir()
    g = home / '.task' / 'scripts' / 'gittw'
    g.write_text(f"#!/bin/sh\necho 'y|2.0|~/.task/scripts/y||2026-11-05T00:00:00Z' >> {_manifest(home)}\n")
    g.chmod(0o755)
    am = tw.AppManager(tw.PathManager())
    am.pull_shared()
    assert am.manifest.get_version('y') == '2.0'


# ── one station updates ───────────────────────────────────────────────────────

def _station(am, monkeypatch, update_station, device):
    values = {'tw.update_station': update_station, 'gittw.device': device}
    monkeypatch.setattr(am, '_rc_value', lambda key, default='': values.get(key, default))


@pytest.mark.parametrize('update_station, device', [('', 's5'), ('yoga', 'yoga'), ('yoga', '')])
def test_the_update_station_or_none_named_goes_ahead(home, monkeypatch, update_station, device):
    am = tw.AppManager(tw.PathManager())
    _station(am, monkeypatch, update_station, device)
    assert am.may_change_here('update', 'tw2nb') is True


def test_another_station_without_a_terminal_refuses(home, monkeypatch, capsys):
    am = tw.AppManager(tw.PathManager())
    _station(am, monkeypatch, 'yoga', 's5')
    monkeypatch.setattr('sys.stdin.isatty', lambda: False)
    assert am.may_change_here('update', 'tw2nb') is False
    out = capsys.readouterr().out
    assert 'yoga' in out and 's5' in out and 'gittw sync' in out


@pytest.mark.parametrize('answer, ok', [('y', True), ('', False), ('n', False)])
def test_another_station_at_a_terminal_asks(home, monkeypatch, answer, ok):
    am = tw.AppManager(tw.PathManager())
    _station(am, monkeypatch, 'yoga', 's5')
    monkeypatch.setattr('sys.stdin.isatty', lambda: True)
    monkeypatch.setattr('builtins.input', lambda prompt='': answer)
    assert am.may_change_here('install', 'tw2nb') is ok
