"""make-awesome 4.15.0: a generated installer writes its config include as ~/.task/config/<app>.rc
when the task dir is the usual ~/.task, so the shared included.rc works on every station (a phone's
home isn't /home/<user>); a custom TW_TASK_DIR still gets its absolute path. Found when tw -u
recurrence-overhaul rewrote the include as /home/djp/..., which another station can't read."""
import importlib.machinery
import importlib.util
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_portable', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_portable', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)


def installer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    info = ma.ProjectInfo()
    info.name, info.version, info.repo = 'demo', '1.0', 'someone/demo'
    info.files = [('demo.rc', 'config')]
    info.checksums = ['abc']
    assert ma.generate_installer(info)
    assert subprocess.run(['bash', '-n', 'demo.install']).returncode == 0
    return tmp_path / 'demo.install'


def run_install(script, home, task_dir=None):
    """Run the installer for real; a stub curl copies demo.rc from a local folder."""
    src, bin_ = home.parent / 'src', home.parent / 'bin'
    src.mkdir(exist_ok=True)
    bin_.mkdir(exist_ok=True)
    (src / 'demo.rc').write_text('demo.x = 1\n')
    (bin_ / 'curl').write_text('#!/bin/sh\nfor a; do last=$a; done\n'
                               'while [ $# -gt 0 ]; do case "$1" in -o) out=$2; shift;; http*) url=$1;; esac; shift; done\n'
                               f'cp "{src}/$(basename "$url")" "$out"\n')
    (bin_ / 'curl').chmod(0o755)
    td = Path(task_dir) if task_dir else home / '.task'
    (td / 'config').mkdir(parents=True, exist_ok=True)
    (td / 'config' / 'included.rc').write_text('# included\n')
    env = dict(os.environ, HOME=str(home), PATH=f"{bin_}:{os.environ['PATH']}")
    env.pop('TASKRC', None)
    env.pop('TW_TASK_DIR', None)
    if task_dir:
        env['TW_TASK_DIR'] = str(task_dir)
    r = subprocess.run(['bash', str(script), 'install'], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return (td / 'config' / 'included.rc').read_text()


def test_the_usual_task_dir_gets_a_portable_include(tmp_path, monkeypatch):
    script = installer(tmp_path, monkeypatch)
    home = tmp_path / 'home'
    home.mkdir()
    text = run_install(script, home)
    assert 'include ~/.task/config/demo.rc\n' in text
    assert str(home) not in text


def test_a_custom_task_dir_keeps_its_absolute_include(tmp_path, monkeypatch):
    script = installer(tmp_path, monkeypatch)
    home = tmp_path / 'home'
    home.mkdir()
    custom = tmp_path / 'elsewhere' / 'task'
    text = run_install(script, home, task_dir=custom)
    assert f'include {custom}/config/demo.rc\n' in text
