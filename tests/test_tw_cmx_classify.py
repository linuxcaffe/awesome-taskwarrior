"""tw 2.15.0: step 3 of the 2026-10-18 consolidation plan (nb tw:tw_consolidation_plan_—_2026-10-18.md).

- Cmx: context multiplexing as one class around one TaskRC; every @ form in
  handle_context_command (it was split between that function and ~90 lines of main()).
- TaskRC follows includes as task does (_include_target, /usr/share/taskwarrior too) and reads
  each file once: a circular include recursed until Python gave up.
- The shell's :context reads the taskrc instead of starting task.
- One classifier (command_of) gives the report name too; _find_report_name and its own command
  list are gone. Pre-exec and filter wrappers get the resolved name (alias, abbreviation, default).

Throwaway rc files, fake `task` scripts.
"""
import importlib.machinery
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

TW = Path(__file__).resolve().parent.parent / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli_cmx', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_cmx', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)


def script(path, body):
    path.write_text('#!/bin/sh\n' + body)
    path.chmod(0o755)
    return path


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A taskrc with three contexts, and a fake task that logs its arguments."""
    rc = tmp_path / 'my.taskrc'
    rc.write_text('data.location=/tmp/x\ncontext.work.read=+work\ncontext.work.write=+work\n'
                  'context.home.read=project:home\ncontext.old=+legacy\n')
    monkeypatch.setenv('TASKRC', str(rc))
    bin_ = tmp_path / 'bin'
    bin_.mkdir()
    log = tmp_path / 'task.log'
    script(bin_ / 'task', f'echo "$*" >> {log}\n')
    monkeypatch.setenv('PATH', f"{bin_}:/usr/bin:/bin")
    monkeypatch.setattr(tw, 'CMX_STALE_MARKER', tmp_path / '.cmx_stale')

    class Env:
        pass
    e = Env()
    e.rc, e.log, e.tmp = rc, log, tmp_path
    e.keys = lambda: dict(l.split('=', 1) for l in rc.read_text().splitlines() if '=' in l)
    e.ran = lambda: log.read_text().splitlines() if log.exists() else []
    return e


def at(*argv):
    return tw.handle_context_command(argv[0], list(argv[1:]))


# ── @ forms ──────────────────────────────────────────────────────────────────

def test_add_builds_a_set_from_a_regular_context(env, capsys):
    assert at('@+work') == 0
    assert env.keys()['context'] == 'work' and 'cmx.contexts' not in env.keys()
    assert at('@+', 'home') == 0
    k = env.keys()
    assert k['context'] == 'cmx:work,home' and k['cmx.contexts'] == 'work,home'
    assert k['context.cmx:work,home.read'] == k['context.cmx.read'] == '( +work ) and ( project:home )'
    assert k['context.cmx.write'] == '( +work )'
    assert 'Activated contexts: work,home' in capsys.readouterr().out


def test_space_forms_and_already_active(env, capsys):
    at('@', '+work')
    at('@+', 'old')
    assert env.keys()['context.cmx.read'] == '( +work ) and ( +legacy )'   # pre-2.6 key works
    assert at('@+old') == 0
    assert "Context 'old' is already active" in capsys.readouterr().out


def test_undefined_and_missing_names(env, capsys):
    assert at('@+nosuch') == 1
    assert "Context 'nosuch' is not defined" in capsys.readouterr().out
    assert at('@+') == 1 and at('@-') == 1 and at('@:') == 1
    assert env.ran() == []


def test_remove_demotes_then_clears(env, capsys):
    tw.Cmx().activate(['work', 'home', 'old'], silent=True)
    assert at('@-home') == 0
    assert env.keys()['context'] == 'cmx:work,old'
    assert at('@-', 'old') == 0
    k = env.keys()
    assert k['context'] == 'work' and k['cmx.contexts'] == '' and k['context.cmx.read'] == ''
    assert not [key for key in k if key.startswith('context.cmx:')]
    assert at('@-work') == 0
    assert 'No cmx contexts are currently active' in capsys.readouterr().out


def test_pause_and_restore(env, capsys):
    tw.Cmx().activate(['work', 'home'], silent=True)
    assert at('@0') == 0
    k = env.keys()
    assert k['context'] == '' and k['cmx.contexts'] == 'work,home' and k['context.cmx.read'] == ''
    assert "CMX set preserved: work,home" in capsys.readouterr().out
    assert at('@') == 0                       # paused: task's own `context`, not "active"
    assert env.ran() == ['context']
    env.rc.write_text(env.rc.read_text().replace('context.home.read=project:home',
                                                 'context.home.read=project:house'))
    assert at('@@') == 0                      # filters rebuilt from today's definitions
    assert env.keys()['context.cmx.read'] == '( +work ) and ( project:house )'


def test_show_active_set(env, capsys):
    tw.Cmx().activate(['work', 'home'], silent=True)
    capsys.readouterr()
    assert at('@') == 0
    out = capsys.readouterr().out
    assert 'Context multiplexing active: work,home' in out and 'Combined filter:' in out
    assert env.ran() == []


def test_restore_with_nothing_saved(env, capsys):
    assert at('@@') == 1
    assert 'No saved CMX set' in capsys.readouterr().out


@pytest.mark.parametrize('argv,ran', [
    (['@?'],                        'context show'),
    (['@:', 'home', 'list'],        'rc.context:home list'),
    (['@_', 'next', '+x'],          'rc.context:none next +x'),
    (['@list'],                     'context list'),
    (['@', 'list'],                 'context list'),
    (['@', 'work'],                 'context work'),
    (['@', '0'],                    'context 0'),       # only +/- words become set operations
    (['@none'],                     'context none'),
])
def test_task_forms(env, argv, ran):
    assert at(*argv) == 0
    assert env.ran() == [ran]


def test_stale_marker_rebuilds_an_active_set(env):
    tw.Cmx().activate(['work', 'home'], silent=True)
    env.rc.write_text(env.rc.read_text().replace('context.work.read=+work', 'context.work.read=+job'))
    tw.CMX_STALE_MARKER.touch()
    tw.Cmx().rebuild_if_stale()
    assert env.keys()['context.cmx.read'] == '( +job ) and ( project:home )'
    assert not tw.CMX_STALE_MARKER.exists()


def test_stale_marker_while_paused_only_clears_the_marker(env):
    tw.Cmx().activate(['work', 'home'], silent=True)
    at('@0')
    before = env.rc.read_text()
    tw.CMX_STALE_MARKER.touch()
    tw.Cmx().rebuild_if_stale()
    assert env.rc.read_text() == before and not tw.CMX_STALE_MARKER.exists()


def test_main_routes_at_forms(env, monkeypatch):
    monkeypatch.setattr(tw.sys, 'argv', ['tw', '@+', 'work'])
    assert tw.main() == 0
    assert env.keys()['context'] == 'work'


# ── TaskRC includes ──────────────────────────────────────────────────────────

def test_circular_include_is_read_once(tmp_path, monkeypatch):
    a, b = tmp_path / 'a.rc', tmp_path / 'b.rc'
    a.write_text('include b.rc\ncontext.x.read=+a\n')
    b.write_text('include a.rc\ncontext.y.read=+b\n')
    monkeypatch.setenv('TASKRC', str(a))
    rc = tw.TaskRC()
    assert rc.get('context.x.read') == '+a' and rc.get('context.y.read') == '+b'


def test_include_lookup_matches_task(tmp_path, monkeypatch):
    sysdir = tmp_path / 'share'
    sysdir.mkdir()
    (sysdir / 'dark-256.theme').write_text('color.due=red\ncolor.tagged=green\n')
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'sub' / 'local.rc').write_text('context.z.read=+z\n')
    main = tmp_path / 'main.rc'
    main.write_text('include sub/local.rc\ninclude dark-256.theme\ninclude missing.rc\n'
                    'color.due=blue\n')
    monkeypatch.setattr(tw, '_SYSTEM_RC_DIR', sysdir)
    monkeypatch.setenv('TASKRC', str(main))
    rc = tw.TaskRC()
    assert rc.get('context.z.read') == '+z'
    assert rc.get('color.tagged') == 'green'      # found in /usr/share/taskwarrior
    assert rc.get('color.due') == 'blue'          # the later definition wins


# ── one classifier ───────────────────────────────────────────────────────────

VOCAB = {
    'reports': {'next', 'list', 'ls', 'agenda', 'newest', 'minimal'},
    'aliases': {'agd': 'edate:today agenda', 'rm': 'delete', 'l8': '+LATEST'},
    'abbreviation': 2,
    'default': 'next',
}


@pytest.mark.parametrize('args,result', [
    ([],                  ('report', 'next')),
    (['+work'],           ('report', 'next')),
    (['proj:x', 'li'],    ('report', 'list')),
    (['agd'],             ('report', 'agenda')),
    (['l8'],              ('report', 'next')),
    (['5', 'del'],        ('other', 'delete')),
    (['rm', '5'],         ('other', 'delete')),
    (['5'],               ('other', 'information')),
    (['ne'],              ('other', None)),
    (['add', 'list', 'x'], ('other', 'add')),
])
def test_command_of(args, result):
    assert tw.command_of(args, VOCAB) == result


def test_command_of_without_vocab():
    assert tw.command_of(['list'], None) == (None, None)


def test_pre_exec_gets_the_resolved_report(env, monkeypatch, tmp_path):
    seen = tmp_path / 'seen'
    hook = script(tmp_path / 'theme-wrap', f'echo "$TW_PRE_EXEC_PHASE $TW_REPORT" >> {seen}\n')
    wrappers = tmp_path / 'wrappers'
    wrappers.write_text(f'theme-switch|{hook}|themes|pre-exec\n')
    monkeypatch.setattr(tw.WrapperManager, 'WRAPPERS_FILE', wrappers)
    monkeypatch.setattr(tw, '_task_vocab', lambda: VOCAB)
    for args in (['agd'], ['5', 'del'], []):
        assert tw.pass_through_to_task(args) == 0
    assert seen.read_text().splitlines() == ['pre agenda', 'post agenda', 'pre ', 'post ',
                                             'pre next', 'post next']
    assert env.ran() == ['agd', '5 del', '']
