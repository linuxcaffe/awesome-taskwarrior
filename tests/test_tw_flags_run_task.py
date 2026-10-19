"""tw 2.14.0: step 2 of the 2026-10-18 consolidation plan (nb tw:tw_consolidation_plan_—_2026-10-18.md).

- One flag table (TW_FLAGS) drives the argument split, argparse, `tw -h` and the bash/zsh/fish
  completions, which had drifted apart (`tw --gtk`/`--tui` were refused as unknown flags;
  completions lacked -R, -g, -t, --timing, --install-completion).
- One run_task() starts task: argv[0] 'task', the binary from PATH, exit 127 when there's none.
- The dot shortcuts are one export query each; the pager is a pipe, not a shell string.

Throwaway HOME, fake `task` scripts, no network.
"""
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

TW = Path(__file__).resolve().parent.parent / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli_flags', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_flags', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)

VISIBLE = [f for f in tw.TW_FLAGS if not f.hidden]


def script(path, body):
    path.write_text('#!/bin/sh\n' + body)
    path.chmod(0o755)
    return path


@pytest.fixture
def fake_bin(tmp_path, monkeypatch):
    d = tmp_path / 'bin'
    d.mkdir()
    monkeypatch.setenv('PATH', f"{d}:/usr/bin:/bin")
    return d


# ── the flag table reaches everything ────────────────────────────────────────

def test_table_is_well_formed():
    names = [n for f in tw.TW_FLAGS for n in tw._flag_names(f)]
    assert len(names) == len(set(names))
    assert {f.kind for f in tw.TW_FLAGS} <= set(tw._ARGPARSE_KIND)
    for f in tw.TW_FLAGS:
        assert f.long.startswith('--') and (not f.short or len(f.short) == 2)


@pytest.mark.parametrize('flag', ['--gtk', '--tui', '-g', '-t', '--readme', '--install-completion'])
def test_every_flag_is_a_tw_flag(flag):
    assert tw._is_tw_flag(flag)
    assert tw.validate_first_arg_flag([flag]) == (True, None)


def test_hidden_flag_only_after_its_owner():
    assert not tw._is_tw_flag('--gen')
    assert tw._split_tw_args(['-g', '--gen', 'next']) == (['-g', '--gen'], ['next'])


@pytest.mark.parametrize('argv,attr,value', [
    (['-i'], 'info', ''),
    (['-i', 'events'], 'info', 'events'),
    (['--debug'], 'debug', '1'),
    (['--debug=2'], 'debug', '2'),
    (['-I', 'events'], 'install', 'events'),
    (['--tui'], 'tui', True),
    (['-R'], 'readme', ''),
    (['-g', '--gen'], 'gen', []),
])
def test_argparse_from_table(argv, attr, value):
    args, extra = tw.build_parser().parse_known_args(argv)
    assert getattr(args, attr) == value and extra == []


def test_help_lists_every_flag(capsys):
    tw.show_help()
    out = capsys.readouterr().out
    for f in VISIBLE:
        assert f.long in out and f.help in out
    for topic in tw.HELP_TOPICS:
        assert f"-h {topic}" in out


@pytest.mark.parametrize('shell', ['bash', 'zsh', 'fish'])
def test_completions_list_every_flag_and_topic(shell):
    text = tw.COMPLETIONS[shell]()
    for f in VISIBLE:
        for n in tw._flag_names(f):
            if shell == 'fish':
                assert (f'-l {n[2:]}' if n.startswith('--') else f'-s {n[1:]}') in text, n
            else:
                assert n in text, n
    for topic in tw.HELP_TOPICS:
        assert topic in text


def test_bash_completion_parses(tmp_path):
    p = tmp_path / 'tw.sh'
    p.write_text(tw.generate_bash_completion())
    r = subprocess.run(['bash', '-n', str(p)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_bash_completion_arg_cases():
    text = tw.generate_bash_completion()
    assert '-r|--remove|-u|--update|--verify)' in text
    assert '--generate-completion|--install-completion)' in text
    # passthrough flags let task's words follow; package flags don't
    cmd_flags = tw._tw_command_flags()
    assert '--install' in cmd_flags and '-p' not in cmd_flags and '--timing' not in cmd_flags


def test_zsh_specs_continue_lines():
    text = tw.generate_zsh_completion()
    block = text.split('_arguments -C \\\n', 1)[1].split("'*::task commands", 1)[0]
    lines = [l for l in block.split('\n') if l.strip()]
    assert len(lines) == len(VISIBLE)
    assert all(l.endswith("' \\") for l in lines), lines
    assert "'--debug=-[Enable debug output (1-3)]::level:(1 2 3)'" in text


def test_help_topic_summaries():
    assert tw.help_topic_summary('shell') == 'Interactive Shell'
    assert tw.help_topic_summary('install') == 'Package Installation'


# ── run_task ─────────────────────────────────────────────────────────────────

def test_run_task_keeps_argv0(fake_bin, monkeypatch):
    script(fake_bin / 'task', 'exit 0\n')
    seen = {}
    def run(cmd, **k):
        seen['cmd'], seen['k'] = cmd, k
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(tw.subprocess, 'run', run)
    tw.run_task(['cal'], capture_output=True)
    assert seen['cmd'] == ['task', 'cal']
    assert seen['k']['executable'] == str(fake_bin / 'task')
    assert seen['k']['check'] is False and seen['k']['capture_output'] is True


def test_run_task_without_task(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('PATH', str(tmp_path))
    r = tw.run_task(['next'], capture_output=True, text=True)
    assert r.returncode == 127 and r.stdout == ''
    assert 'task executable not found' in capsys.readouterr().err
    assert tw.get_taskwarrior_version() == 'unknown'


def test_run_task_runs(fake_bin):
    script(fake_bin / 'task', 'echo "$*"\n')      # ($0 is the script's path, whatever argv[0] was)
    r = tw.run_task(['next', '+home'], capture_output=True, text=True)
    assert r.stdout.split() == ['next', '+home']


# ── dot shortcuts ────────────────────────────────────────────────────────────

EXPORTS = {
    'pending': '[{"id":3,"uuid":"aaaaaaaa-1","entry":"20261001T000000Z","modified":"20261018T000000Z"},'
               '{"id":9,"uuid":"bbbbbbbb-2","entry":"20261017T000000Z","modified":"20261002T000000Z"}]',
    'completed': '[{"id":0,"uuid":"cccccccc-3","end":"20261010T000000Z"},'
                 '{"id":0,"uuid":"dddddddd-4","end":"20261011T000000Z"}]',
    'deleted': '[]',
}


@pytest.fixture
def exports(fake_bin, tmp_path):
    for status, body in EXPORTS.items():
        (tmp_path / status).write_text(body)
    script(fake_bin / 'task', 'for a in "$@"; do case "$a" in status:*) cat "%s/${a#status:}";; '
                              'esac; done\n' % tmp_path)


@pytest.mark.parametrize('dot,want', [('.', '9'), ('..', '3'), ('...', 'dddddddd')])
def test_dot_shortcuts(exports, dot, want, capsys):
    assert tw.resolve_dot_shortcut(dot) == want
    err = capsys.readouterr()
    assert f'{dot} -> task {want}' in err.err and err.out == ''


def test_dot_shortcut_none_found(exports, capsys):
    assert tw.resolve_dot_shortcut('....') is None
    assert 'No most recently deleted task found' in capsys.readouterr().err


# ── pager ────────────────────────────────────────────────────────────────────

def test_pager_is_a_pipe(fake_bin, tmp_path, monkeypatch):
    log = tmp_path / 'args'
    script(fake_bin / 'task', f'echo "$*" > {log}; echo report-line; echo noise >&2\n')
    script(fake_bin / 'less', 'cat > %s/paged\n' % tmp_path)
    monkeypatch.setattr(tw.subprocess, 'run', subprocess.run)
    assert tw.run_with_pager(["proj:it's", 'next']) == 0
    args = log.read_text().split()
    assert args[:2] == ["proj:it's", 'next'] and 'rc.limit=0' in args
    assert (tmp_path / 'paged').read_text() == 'report-line\n'


# ── --timing: task's debug noise stays out, real messages and hook data don't ─

def test_timing_drops_coloured_debug_noise(fake_bin, capsys):
    script(fake_bin / 'task', r'''printf 'Filtered 1082 tasks --> 42 tasks [all tasks]\n' >&2
printf '  pending.data \033[38;5;46mrw\033[0m - T0124\n' >&2
printf 'Hook: Calling /h/on-launch_x.py\n' >&2
printf '[timing] on-launch_x.py: 12.5ms\n' >&2
printf 'Perf task 2.6.2 - 20261019T000000Z init:100 load:0 gc:0 filter:0 commit:0 sort:0 render:0 hooks:12500 other:0 total:20000\n' >&2
printf 'a real notice\n' >&2
''')
    assert tw.run_with_timing(['count']) == 0
    err = capsys.readouterr().err
    assert 'Filtered' not in err and 'pending.data' not in err
    assert 'a real notice' in err
    assert 'on-launch_x.py' in err and '12.5ms' in err
