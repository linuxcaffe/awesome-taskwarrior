"""tw 2.13.1: step 1 of the 2026-10-18 consolidation plan (nb tw:tw_consolidation_plan_—_2026-10-18.md).

- `tw . export`: the `[tw] . -> task N` notice went to stdout, after the JSON.
- `tw --install --dry-run APP` (the form `tw -h install` shows): --install took --dry-run as its app.
- `tw -i +python`: -i took the tag as its app.
- `tw -home next`: refused as an unknown flag; task reads it as a tag exclusion.
- `tw --verify`: guessed each file's place from its type, and read name:type:dest as type `type:dest`.
- Completions read ~/.task/.tw_manifest (it's ~/.task/config/.tw_manifest).
- init_directories() made an `installed/` folder beside the tw script.
- `tw @- last`: the "nothing left" clear kept earlier sets' context.cmx:<set>.* keys.

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
loader = importlib.machinery.SourceFileLoader('tw_cli_review4', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_review4', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)


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


# ── dot shortcuts: notices on stderr ─────────────────────────────────────────

def test_dot_notice_stays_off_stdout(fake_bin, tmp_path):
    # the shortcut's query finds task 7; the real command (`7 export`) prints its JSON
    script(fake_bin / 'task', 'case "$*" in *status:pending*) '
                              'echo "[{\\"id\\":7,\\"entry\\":\\"20261018T000000Z\\"}]";; '
                              '*) echo "[{\\"id\\":7}]";; esac\n')
    env = dict(os.environ, HOME=str(tmp_path), PATH=os.environ['PATH'])
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    r = subprocess.run([sys.executable, str(TW), '.', 'export'], capture_output=True, text=True,
                       env=env, timeout=30)
    assert r.stdout.strip() == '[{"id":7}]'
    assert '. -> task 7' in r.stderr


# ── argument splitting ───────────────────────────────────────────────────────

@pytest.mark.parametrize('argv,parser,rest', [
    (['--install', '--dry-run', 'events'], ['--dry-run', '--install', 'events'], []),
    (['-I', '--dry-run', 'events'],        ['--dry-run', '-I', 'events'], []),
    (['--dry-run', '--install', 'events'], ['--dry-run', '--install', 'events'], []),
    (['-i', '+python'],                    ['-i'], ['+python']),
    (['-i', '-hook'],                      ['-i'], ['-hook']),
    (['-i', 'events', '+calendar'],        ['-i', 'events'], ['+calendar']),
    (['-R', 'events'],                     ['-R', 'events'], []),
])
def test_split_tw_args(argv, parser, rest):
    assert tw._split_tw_args(argv) == (parser, rest)


def test_install_dry_run_in_documented_order(tmp_path):
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    env = dict(os.environ, HOME=str(tmp_path))
    r = subprocess.run([sys.executable, str(TW), '--install', '--dry-run', 'events'],
                       capture_output=True, text=True, env=env, timeout=30)
    assert 'usage:' not in r.stderr
    assert 'DRY RUN' in r.stdout


@pytest.mark.parametrize('first,result', [
    ('-l',        (True, None)),
    ('--debug=2', (True, None)),
    ('-home',     (False, None)),          # task's: exclude tag home
    ('-lena',     (False, None)),          # a tag, not -l
    ('--',        (False, None)),
    ('next',      (False, None)),
    ('-x',        (False, 'Unknown flag: -x')),
    ('--isntall', (False, 'Unknown flag: --isntall')),
])
def test_validate_first_arg_flag(first, result):
    assert tw.validate_first_arg_flag([first, 'next']) == result


def test_leading_tag_exclusion_reaches_task(fake_bin, tmp_path):
    log = tmp_path / 'args'
    script(fake_bin / 'task', f'echo "$@" >> {log}\n')
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    env = dict(os.environ, HOME=str(tmp_path), PATH=os.environ['PATH'])
    r = subprocess.run([sys.executable, str(TW), '-home', 'next'], capture_output=True, text=True,
                       env=env, timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr
    assert log.read_text().split('\n')[-2] == '-home next'


# ── meta files: name:type:dest ───────────────────────────────────────────────

def make_meta(tmp_path, files):
    p = tmp_path / 'app.meta'
    p.write_text(f'name=app\nversion=1.0\nfiles={files}\n')
    return tw.MetaFile(p)


def test_meta_files_three_part_entries(tmp_path):
    m = make_meta(tmp_path, 'a.py:script:~/.task/scripts/a,README.md:doc:docs/app_README.md,'
                            'b.sh:script:scripts,c.rc:config,plain')
    assert m.get_files() == [('a.py', 'script'), ('README.md', 'doc'), ('b.sh', 'script'),
                             ('c.rc', 'config'), ('plain', 'file')]
    task = tmp_path / '.task'
    assert m.get_dest('a.py', task) == Path.home() / '.task/scripts/a'
    assert m.get_dest('README.md', task) == task / 'docs/app_README.md'
    assert m.get_dest('b.sh', task) is None            # just the type's folder
    assert m.get_dest('c.rc', task) is None


# ── verify: the manifest's paths ─────────────────────────────────────────────

@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.delenv('TASKRC', raising=False)
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    return tmp_path


def test_verify_uses_recorded_paths(home, capsys):
    import hashlib
    unit = home / '.config' / 'systemd' / 'user' / 'app.timer'
    script_ = home / '.task' / 'scripts' / 'app'                 # installed without its .py
    for p, body in ((unit, 'timer'), (script_, 'print()')):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    sums = [hashlib.sha256(b'print()').hexdigest(), hashlib.sha256(b'timer').hexdigest()]
    meta = make_meta(home, 'app.py:script:~/.task/scripts/app,app.timer:systemd')
    meta.data['checksums'] = ','.join(sums)
    (home / '.task' / 'config' / '.tw_manifest').write_text(
        f'app|1.0|{script_}||2026-10-18T00:00:00Z\napp|1.0|{unit}||2026-10-18T00:00:00Z\n')

    mgr = tw.AppManager(tw.PathManager())
    mgr.registry.get_meta = lambda name: meta
    assert mgr.verify('app') is True, capsys.readouterr().out


# ── completions and directories ──────────────────────────────────────────────

@pytest.mark.parametrize('gen', ['generate_bash_completion', 'generate_zsh_completion',
                                 'generate_fish_completion'])
def test_completions_read_the_real_manifest(gen):
    text = getattr(tw, gen)()
    assert '$HOME/.task/config/.tw_manifest' in text
    assert '$HOME/.task/.tw_manifest' not in text
    assert '.task/registry' not in text


def test_init_directories_leaves_the_script_folder_alone(home):
    paths = tw.PathManager()
    paths.init_directories()
    assert not (paths.tw_root / 'installed').exists()
    assert (home / '.task' / 'hooks').is_dir()


# ── cmx: removing the last context drops old set keys ────────────────────────

def test_cmx_remove_last_drops_set_keys(tmp_path, monkeypatch):
    rc = tmp_path / 'my.taskrc'
    rc.write_text('context.work.read=+work\ncontext=cmx:work\ncmx.contexts=work\n'
                  'context.cmx:work.read=( +work )\ncontext.cmx.read=( +work )\n')
    monkeypatch.setenv('TASKRC', str(rc))
    assert tw.Cmx().remove('work') == 0
    keys = [l.split('=')[0] for l in rc.read_text().splitlines()]
    assert 'context.cmx:work.read' not in keys
    assert 'context.work.read' in keys
