"""make-awesome 4.18.0: a generated installer keeps an existing config: it downloaded every config with curl -o,
so reinstalling (tw -I, or running the .install) reset the user's settings. 12 of the 16 fleet
installers with an .rc did this; the hand-written four (tw2nb, daily-email, hledger-add,
sanity-check) already kept theirs (2026-11-04). The new default goes beside it as <name>.new."""
import importlib.machinery
import importlib.util
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_keepcfg', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_keepcfg', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)


def installer(tmp_path, monkeypatch, files):
    monkeypatch.chdir(tmp_path)
    info = ma.ProjectInfo()
    info.name, info.version, info.repo = 'demo', '1.0', 'someone/demo'
    info.files = files
    info.checksums = ['abc'] * len(files)
    assert ma.generate_installer(info)
    assert subprocess.run(['bash', '-n', 'demo.install']).returncode == 0
    return tmp_path / 'demo.install'


def run_install(script, home, sources):
    src, bin_ = home.parent / 'src', home.parent / 'bin'
    src.mkdir(exist_ok=True)
    bin_.mkdir(exist_ok=True)
    for name, text in sources.items():
        (src / name).write_text(text)
    (bin_ / 'curl').write_text('#!/bin/sh\n'
                               'while [ $# -gt 0 ]; do case "$1" in -o) out=$2; shift;; http*) url=$1;; esac; shift; done\n'
                               f'cp "{src}/$(basename "$url")" "$out"\n')
    (bin_ / 'curl').chmod(0o755)
    (home / '.task' / 'config').mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, HOME=str(home), PATH=f"{bin_}:{os.environ['PATH']}")
    env.pop('TASKRC', None)
    env.pop('TW_TASK_DIR', None)
    r = subprocess.run(['bash', str(script), 'install'], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def test_fresh_install_writes_the_config(tmp_path, monkeypatch):
    script = installer(tmp_path, monkeypatch, [('demo.rc', 'config')])
    home = tmp_path / 'home'
    home.mkdir()
    run_install(script, home, {'demo.rc': 'demo.x = stock\n'})
    cfg = home / '.task' / 'config'
    assert (cfg / 'demo.rc').read_text() == 'demo.x = stock\n'
    assert not (cfg / 'demo.rc.new').exists()


def test_reinstall_keeps_the_users_config(tmp_path, monkeypatch):
    script = installer(tmp_path, monkeypatch, [('demo.rc', 'config')])
    home = tmp_path / 'home'
    (home / '.task' / 'config').mkdir(parents=True)
    (home / '.task' / 'config' / 'demo.rc').write_text('demo.x = mine\n')
    out = run_install(script, home, {'demo.rc': 'demo.x = stock\n'})
    cfg = home / '.task' / 'config'
    assert (cfg / 'demo.rc').read_text() == 'demo.x = mine\n'
    assert (cfg / 'demo.rc.new').read_text() == 'demo.x = stock\n'
    assert 'demo.rc.new' in out


def test_reinstall_with_an_unchanged_config_leaves_no_new_file(tmp_path, monkeypatch):
    script = installer(tmp_path, monkeypatch, [('demo.rc', 'config')])
    home = tmp_path / 'home'
    (home / '.task' / 'config').mkdir(parents=True)
    (home / '.task' / 'config' / 'demo.rc').write_text('demo.x = stock\n')
    run_install(script, home, {'demo.rc': 'demo.x = stock\n'})
    assert not (home / '.task' / 'config' / 'demo.rc.new').exists()
