"""tw 2.19.0: reports open in vit (vit 1.4.1, nb tw:docs/vit-plan.md "Harnessing tw").

- tw.ui=vit (a station's local.rc): a command task would run as a report (default.command
  included, so a bare `tw`) opens in vit on an interactive terminal, with the same arguments.
- Never into a pipe or a script, never from inside vit (TW_CLIENT=vit: a shell or `tw` started
  in vit), never without vit on PATH, never for a write; plain `task` is never affected.
- tw -V opens vit once, without the setting.

Throwaway HOME and TASKRC, the real task (to tell a report), a fake vit; os.execvp and run_task
are recorded, not run.
"""
import importlib.machinery
import importlib.util
import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader('tw_cli_vit', str(ROOT / 'tw'))
spec = importlib.util.spec_from_loader('tw_cli_vit', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)

TASK = shutil.which('task')
pytestmark = pytest.mark.skipif(not TASK, reason='needs task 2.6.2 on PATH')


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A station: ~/.taskrc includes local.rc (where tw.ui lives); vit and task on PATH."""
    task_dir = tmp_path / '.task'
    (task_dir / 'config').mkdir(parents=True)
    (task_dir / 'local.rc').write_text('tw.ui=vit\n')
    (tmp_path / '.taskrc').write_text(
        f'data.location={task_dir}\nhooks=off\nconfirmation=no\nnews.version=2.6.2\n'
        f'include {task_dir}/local.rc\n')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    vit = bin_dir / 'vit'
    vit.write_text('#!/bin/sh\nexit 0\n')
    vit.chmod(0o755)
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.delenv('TASKRC', raising=False)
    monkeypatch.delenv('TW_CLIENT', raising=False)
    monkeypatch.setenv('PATH', f'{bin_dir}:{os.path.dirname(TASK)}:/usr/bin:/bin')
    return tmp_path


@pytest.fixture
def calls(monkeypatch):
    """What ran: ('vit', argv) from os.execvp, ('task', args) from run_task."""
    seen = []

    def execvp(file, argv):
        seen.append(('vit', list(argv)))
        raise SystemExit(0)

    class Done:
        returncode = 0

    real_run_task = tw.run_task

    def run_task(args, **kw):
        if kw.get('capture_output'):      # tw's own reads (task _show): real
            return real_run_task(args, **kw)
        seen.append(('task', list(args)))
        return Done()

    monkeypatch.setattr(tw.os, 'execvp', execvp)
    monkeypatch.setattr(tw, 'run_task', run_task)
    monkeypatch.setattr(tw, '_interactive', lambda: True)
    return seen


def through(args):
    try:
        tw.pass_through_to_task(args)
    except SystemExit:
        pass


@pytest.mark.parametrize('args', [['next'], [], ['+home', 'next'], ['ls', 'project:x']])
def test_a_report_on_a_terminal_opens_in_vit(home, calls, args):
    through(args)
    assert calls == [('vit', ['vit'] + args)]


@pytest.mark.parametrize('args', [['add', 'x'], ['1', 'done'], ['1'], ['stats']])
def test_anything_else_runs_task(home, calls, args):
    through(args)
    assert calls == [('task', args)]


def test_not_on_a_terminal(home, calls, monkeypatch):
    monkeypatch.setattr(tw, '_interactive', lambda: False)
    through(['next'])
    assert calls == [('task', ['next'])]


def test_not_from_inside_vit(home, calls, monkeypatch):
    monkeypatch.setenv('TW_CLIENT', 'vit')
    through(['next'])
    assert calls == [('task', ['next'])]


def test_not_without_the_setting(home, calls):
    (home / '.task' / 'local.rc').write_text('tw.platforms=desktop\n')
    through(['next'])
    assert calls == [('task', ['next'])]


def test_not_without_vit(home, calls):
    (home / 'bin' / 'vit').unlink()
    through(['next'])
    assert calls == [('task', ['next'])]


def test_interactive_needs_both_ends_a_terminal(monkeypatch):
    monkeypatch.setattr(tw.sys.stdin, 'isatty', lambda: True)
    monkeypatch.setattr(tw.sys.stdout, 'isatty', lambda: False)
    assert tw._interactive() is False


# ── tw -V ────────────────────────────────────────────────────────────────────

def test_dash_V_is_a_tw_flag():
    assert tw._is_tw_flag('-V') and tw._is_tw_flag('--vit')


def test_dash_V_opens_vit_without_the_setting(home, calls, monkeypatch):
    (home / '.task' / 'local.rc').write_text('')
    monkeypatch.setattr(tw.sys, 'argv', ['tw', '-V', '+home', 'next'])
    try:
        tw.main()
    except SystemExit:
        pass
    assert calls == [('vit', ['vit', '+home', 'next'])]


def test_dash_V_without_vit_says_how_to_get_it(home, calls, monkeypatch, capsys):
    (home / 'bin' / 'vit').unlink()
    monkeypatch.setattr(tw.sys, 'argv', ['tw', '-V'])
    assert tw.main() == 1
    assert 'tw -I vit' in capsys.readouterr().out
    assert calls == []
