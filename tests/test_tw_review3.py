"""tw 2.13.0: the four minor findings of the 2026-10-17 review.

- `tw --timing 5 delete`: task's stdout was captured, so its confirmation prompt sat in the
  buffer while task waited for an answer.
- The filter PTY drain read once after task exited: output a child of task wrote just after
  (a hook's background job) was lost.
- `tw --timing` (or `tw --debug`) alone did nothing: the pass-through only ran with no tw flag set.
- `tw -l` / `tw -i` fetched each app's .meta over HTTP one after another.

Throwaway HOME, fake `task` scripts, no network.
"""
import importlib.machinery
import importlib.util
import subprocess
import threading
import time
from pathlib import Path

import pytest

TW = Path(__file__).resolve().parent.parent / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli_review3', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_review3', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)


def script(path, body):
    path.write_text(body)
    path.chmod(0o755)
    return path


@pytest.fixture
def fake_bin(tmp_path, monkeypatch):
    d = tmp_path / 'bin'
    d.mkdir()
    monkeypatch.setenv('PATH', f"{d}:/usr/bin:/bin")
    return d


# ── --timing: prompts reach the terminal ─────────────────────────────────────

def test_timing_leaves_stdout_and_stdin_to_the_terminal(fake_bin, monkeypatch):
    script(fake_bin / 'task', '#!/bin/sh\nexit 0\n')
    seen = {}
    def run(cmd, **k):
        seen.update(k)
        return subprocess.CompletedProcess(cmd, 0, stdout=None, stderr='')
    monkeypatch.setattr(tw.subprocess, 'run', run)
    tw.run_with_timing(['5', 'delete'])
    assert seen.get('stdout') is None and seen.get('stdin') is None
    assert seen.get('stderr') == subprocess.PIPE


def test_timing_prompt_is_visible(fake_bin):
    # task writes its prompt, then waits for the answer: the prompt must arrive before we answer
    import select
    script(fake_bin / 'task', '#!/bin/sh\nprintf "Delete task 5? (yes/no) "\nread answer\necho "got $answer"\n')
    p = subprocess.Popen(
        ['python3', '-c', f"""
import importlib.machinery, importlib.util
l = importlib.machinery.SourceFileLoader('t', '{TW}'); s = importlib.util.spec_from_loader('t', l)
t = importlib.util.module_from_spec(s); l.exec_module(t)
t.run_with_timing(['5', 'delete'])
"""], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    seen, deadline = b'', time.time() + 5
    while b'(yes/no)' not in seen and time.time() < deadline:
        if select.select([p.stdout], [], [], 0.2)[0]:
            seen += p.stdout.read1(1024)
    p.stdin.write(b'yes\n')
    p.stdin.close()
    rest = p.stdout.read()
    p.wait(timeout=10)
    assert b'Delete task 5? (yes/no)' in seen, 'the prompt was held back until task finished'
    assert b'got yes' in seen + rest


# ── the filter PTY keeps a late tail ──────────────────────────────────────────

def _filters(tmp_path, fake_bin, monkeypatch):
    script(fake_bin / 'catfilter', '#!/bin/sh\ncat\n')
    wrappers = tmp_path / '.tw_wrappers'
    wrappers.write_text('nice|catfilter|x|filter\n')
    monkeypatch.setattr(tw.WrapperManager, 'WRAPPERS_FILE', wrappers)
    return tw.WrapperManager()


def test_pty_keeps_output_written_just_after_task_exits(fake_bin, tmp_path, monkeypatch, capfd):
    # task exits at once; a child it left behind writes twice more on the same terminal
    script(fake_bin / 'task', '#!/bin/sh\necho head\n(sleep 0.15; echo TAIL1; sleep 0.1; echo TAIL2) &\nexit 0\n')
    _filters(tmp_path, fake_bin, monkeypatch).run_through_filters(['list'])
    out = capfd.readouterr().out
    assert 'head' in out and 'TAIL1' in out and 'TAIL2' in out


def test_pty_does_not_wait_forever_on_a_silent_child(fake_bin, tmp_path, monkeypatch, capfd):
    # a child keeps the terminal open for 30 s and says nothing: tw must not wait for it
    script(fake_bin / 'task', '#!/bin/sh\necho done\n(sleep 30) &\nexit 0\n')
    start = time.perf_counter()
    _filters(tmp_path, fake_bin, monkeypatch).run_through_filters(['list'])
    assert time.perf_counter() - start < 3
    assert 'done' in capfd.readouterr().out


# ── tw --timing / --debug alone run the default report ────────────────────────

@pytest.mark.parametrize('argv', [['--timing'], ['--debug'], ['--debug=2']])
def test_prefix_flag_alone_runs_task(argv, monkeypatch, tmp_path):
    monkeypatch.setenv('HOME', str(tmp_path))
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    ran = []
    monkeypatch.setattr(tw, 'run_with_timing', lambda args: ran.append(('timing', args)) or 0)
    monkeypatch.setattr(tw, 'pass_through_to_task', lambda args, **k: ran.append(('task', args)) or 0)
    monkeypatch.setattr(tw.sys, 'argv', ['tw'] + argv)
    assert tw.main() == 0
    assert ran == [('timing' if argv == ['--timing'] else 'task', [])]


# ── tw -l: the registry's .meta files in parallel ─────────────────────────────

def test_get_metas_runs_in_parallel(monkeypatch, tmp_path):
    monkeypatch.setenv('HOME', str(tmp_path))
    reg = tw.RegistryManager(tw.PathManager())
    active, peak, lock = [0], [0], threading.Lock()
    def get_meta(name):
        with lock:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        time.sleep(0.05)
        with lock:
            active[0] -= 1
        return None if name == 'gone' else f'meta:{name}'
    monkeypatch.setattr(reg, 'get_meta', get_meta)
    names = [f'app{i}' for i in range(12)] + ['gone']
    start = time.perf_counter()
    metas = reg.get_metas(names)
    took = time.perf_counter() - start
    assert metas == {n: f'meta:{n}' for n in names if n != 'gone'}
    assert list(metas) == [n for n in names if n != 'gone']      # registry order kept
    assert peak[0] > 1 and took < 0.05 * len(names) / 2
