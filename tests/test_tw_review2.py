"""tw 2.12.0: the rest of the notable findings from the 2026-10-17 review, plus `tw -R APP`.

- `tw -R APP` ran `bat --style=plain …`, but on Ubuntu `bat` can be Bacula's console (the
  pager is `batcat`): it opened a Qt app and printed Bacula's usage.
- `tw -l -hook`, `-l -python`, `-p -tag next`: an excluded tag went to argparse as short flags.
- `tw -i APP +tag` outside dev mode: registry_dir is None → TypeError.
- cmx (`tw @…`) wrote ~/.taskrc whatever $TASKRC said, replaced a symlinked .taskrc with a
  plain file, and left every earlier set's context.cmx:<set>.* keys behind.
- `tw -s`: an apostrophe killed the shell; `!!` never repeated a shell command (and could run
  a task line through /bin/sh); `:context` read the pre-2.6 key after changing the saved context.

Throwaway HOME and rc files only.
"""
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

TW = Path(__file__).resolve().parent.parent / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli_review2', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_review2', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)


def script(path, body):
    path.write_text('#!/bin/sh\n' + body)
    path.chmod(0o755)
    return path


# ── tw -R APP: a markdown viewer that is what it says ─────────────────────────

@pytest.fixture
def bin_dir(tmp_path, monkeypatch):
    d = tmp_path / 'bin'
    d.mkdir()
    monkeypatch.setenv('PATH', str(d))
    monkeypatch.delenv('PAGER', raising=False)
    return d


def test_bacula_bat_is_not_a_pager(bin_dir):
    script(bin_dir / 'bat', 'echo "Version: 9.6.7 (10 December 2020) x86_64-pc-linux-gnu"; exit 1\n')
    script(bin_dir / 'less', 'exit 0\n')
    assert tw._md_viewer() == ['less']


def test_batcat_first(bin_dir):
    script(bin_dir / 'bat', 'echo "Version: 9.6.7"; exit 1\n')
    script(bin_dir / 'batcat', 'echo "bat 0.19.0"\n')
    assert tw._md_viewer() == ['batcat', '--style=plain', '--language=md']


def test_the_real_bat(bin_dir):
    script(bin_dir / 'bat', 'echo "bat 0.24.0 (fc954678)"\n')
    assert tw._md_viewer() == ['bat', '--style=plain', '--language=md']


def test_pager_then_cat(bin_dir, monkeypatch):
    script(bin_dir / 'most', 'exit 0\n')
    monkeypatch.setenv('PAGER', 'most')
    assert tw._md_viewer() == ['most']
    monkeypatch.setenv('PAGER', 'nosuchpager')
    assert tw._md_viewer() == ['cat']


# ── tw -l -tag, tw -p -tag next: an excluded tag isn't a flag ─────────────────

@pytest.mark.parametrize('argv,parser,rest', [
    (['-l', '-hook'],              ['-l'], ['-hook']),
    (['-l', '+python', '-python'], ['-l'], ['+python', '-python']),
    (['-p', '-tag', 'next'],       ['-p'], ['-tag', 'next']),
    (['-I', 'events'],             ['-I', 'events'], []),
    (['--debug=2', '-l', '-hook'], ['--debug=2', '-l'], ['-hook']),
    (['-i', 'events', '+calendar'], ['-i', 'events'], ['+calendar']),
])
def test_split_tw_args(argv, parser, rest):
    assert tw._split_tw_args(argv) == (parser, rest)


def test_list_with_an_excluded_tag_runs(tmp_path):
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    env = dict(os.environ, HOME=str(tmp_path))
    r = subprocess.run([sys.executable, str(TW), '-l', '-hook'], capture_output=True, text=True,
                       env=env, timeout=30)
    assert r.returncode == 0, r.stderr
    assert 'ignored explicit argument' not in r.stderr


# ── tw -i APP +tag: ask the registry, not registry_dir ────────────────────────

def test_info_tag_check_uses_the_registry():
    class Meta:
        def get_tags(self):
            return ['calendar', 'holidays']
    class Registry:
        def get_meta(self, name):
            return Meta() if name == 'events' else None
    f = tw.TagFilter(['+calendar'])
    assert tw._app_matches(Registry(), 'events', f) is True
    assert tw._app_matches(Registry(), 'events', tw.TagFilter(['-holidays'])) is False
    assert tw._app_matches(Registry(), 'nosuch', f) is None


# ── cmx: $TASKRC, symlinks, old sets ──────────────────────────────────────────

@pytest.fixture
def rc(tmp_path, monkeypatch):
    path = tmp_path / 'my.taskrc'
    path.write_text('data.location=/tmp/x\n# a comment\ncontext.work.read=+work\n'
                    'context.home.read=project:home\n')
    monkeypatch.setenv('TASKRC', str(path))
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    (tmp_path / 'home').mkdir()
    return path


def test_taskrc_env_is_honoured(rc, tmp_path):
    tw.TaskRC().set_keys({'context': 'work'})
    assert 'context=work' in rc.read_text().splitlines()
    assert not (tmp_path / 'home' / '.taskrc').exists()


def test_pathmanager_taskrc_honours_env(rc):
    assert tw.PathManager().taskrc == rc


def test_symlinked_taskrc_stays_a_symlink(rc, tmp_path, monkeypatch):
    link = tmp_path / 'link.taskrc'
    link.symlink_to(rc)
    monkeypatch.setenv('TASKRC', str(link))
    tw.TaskRC().set_keys({'context': 'home'})
    assert link.is_symlink()
    assert 'context=home' in rc.read_text().splitlines()


def test_cmx_drops_earlier_sets(rc):
    assert tw.set_cmx_context('work', silent=True) == 0
    assert tw.set_cmx_context('work,home', silent=True) == 0
    keys = [l.split('=')[0] for l in rc.read_text().splitlines() if '=' in l]
    assert 'context.cmx:work,home.read' in keys
    assert 'context.cmx:work.read' not in keys
    assert 'context.cmx.read' in keys and 'context.work.read' in keys
    assert '# a comment' in rc.read_text()
    tw.set_cmx_context('', silent=True)
    assert not [k for k in (l.split('=')[0] for l in rc.read_text().splitlines()) if k.startswith('context.cmx:')]


# ── tw -s ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def shell(monkeypatch, tmp_path):
    monkeypatch.setattr(tw, 'SHELL_HISTFILE', str(tmp_path / 'hist'))
    sh = tw.TaskShell()
    sh.ran, sh.shell_ran = [], []
    monkeypatch.setattr(sh, '_run_task', lambda args: sh.ran.append(args))
    real_run = tw.subprocess.run
    def run(cmd, *a, **k):
        if k.get('shell'):
            sh.shell_ran.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        return real_run(cmd, *a, **k)
    monkeypatch.setattr(tw.subprocess, 'run', run)
    return sh


def test_apostrophe_does_not_kill_the_shell(shell):
    shell.head = ['add']
    assert shell.handle_line("don't forget milk") is True
    assert shell.ran == [['add', "don't", 'forget', 'milk']]
    assert shell.handle_line(":push 'unclosed") is True       # says so, carries on


def test_bang_bang_repeats_the_last_shell_command(shell):
    shell.handle_line('!echo hi')
    shell.handle_line('5 done')
    shell.handle_line('!!')
    assert shell.shell_ran == ['echo hi', 'echo hi']
    assert shell.ran == [['5', 'done']]


def test_bang_bang_never_runs_a_task_line(shell):
    shell.handle_line('5 done')
    shell.handle_line('!!')
    assert shell.shell_ran == []


def test_context_reads_the_262_key_and_changes_nothing(shell, monkeypatch):
    calls = []
    def run(cmd, *a, **k):
        calls.append(cmd)
        out = 'project:home or +errand' if cmd[-1] == 'rc.context.home.read' else ''
        return subprocess.CompletedProcess(cmd, 0, stdout=out)
    monkeypatch.setattr(tw.subprocess, 'run', run)
    shell.handle_line(':context home')
    assert shell.prefix_stack == ['(', 'project:home', 'or', '+errand', ')']
    assert not any(c[:2] == ['task', 'context'] for c in calls)
