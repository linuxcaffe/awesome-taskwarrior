"""make-awesome 4.19.0: a config is discrete unless taskwarrior itself must read it (2026-11-04).

Most fleet apps read their own ~/.task/config/<app>.rc directly (CONVENTIONS §7), yet every
installer also put it in the include chain, where a missing file stops `task` from starting at
all: the old update bug left timelog, matrix-taskbot and tw2nb includes commented out for weeks.
Now an installer includes only a config the .meta names in `included=`, or one that defines keys
taskwarrior uses (uda., report., urgency., alias., context., …: included anyway, with a warning to
declare it). Every other config is discrete: no include, and one an older version added is removed.
"""
import importlib.machinery
import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_discrete', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_discrete', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)

DISCRETE = 'demo.mode = on\n'
NATIVE = 'uda.demo.type = string\nreport.demo.columns = id\n'


def installer(tmp_path, monkeypatch, sources, included=()):
    """Generate demo.install in a project dir holding the config sources (native detection reads them)."""
    proj = tmp_path / 'proj'
    proj.mkdir()
    for name, text in sources.items():
        (proj / name).write_text(text)
    monkeypatch.chdir(proj)
    info = ma.ProjectInfo()
    info.name, info.version, info.repo = 'demo', '1.0', 'someone/demo'
    info.files = [(n, 'config') for n in sources]
    info.checksums = ['abc'] * len(sources)
    info.included = list(included)
    assert ma.generate_installer(info)
    script = proj / 'demo.install'
    assert subprocess.run(['bash', '-n', str(script)]).returncode == 0
    return script


def run(script, home, sources, action='install'):
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
    r = subprocess.run(['bash', str(script), action], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


@pytest.fixture
def home(tmp_path):
    h = tmp_path / 'home'
    (h / '.task' / 'config').mkdir(parents=True)
    (h / '.task' / 'config' / 'included.rc').write_text('include ~/.task/config/other.rc\n')
    (h / '.taskrc').write_text('include ~/.task/config/included.rc\n')
    return h


def chain(home):
    return (home / '.task' / 'config' / 'included.rc').read_text() + (home / '.taskrc').read_text()


# ── What counts as native ─────────────────────────────────────────────────────

def test_native_keys_are_taskwarriors_own(tmp_path):
    f = tmp_path / 'x.rc'
    f.write_text('# comment\ninclude ~/.task/other.rc\ndemo.a = 1\nuda.x.type = string\n'
                 'context.work.read = +work\nreport.next.filter = +x\ncondition.y.filter = +z\n')
    assert ma.native_rc_keys(f) == ['uda.x.type', 'context.work.read', 'report.next.filter']
    f.write_text('tw2nb.mode = on\nhomeserver = https://example.org\ncondition.y.filter = +z\n')
    assert ma.native_rc_keys(f) == []
    assert ma.native_rc_keys(tmp_path / 'missing.rc') == []


# ── Discrete: the norm ────────────────────────────────────────────────────────

def test_a_discrete_config_gets_no_include(tmp_path, monkeypatch, home):
    script = installer(tmp_path, monkeypatch, {'demo.rc': DISCRETE})
    run(script, home, {'demo.rc': DISCRETE})
    assert (home / '.task' / 'config' / 'demo.rc').read_text() == DISCRETE
    assert 'demo.rc' not in chain(home)


@pytest.mark.parametrize('where', ['included.rc', '.taskrc'])
@pytest.mark.parametrize('line', ['include ~/.task/config/demo.rc',
                                  '#include ~/.task/config/demo.rc   # tw -r demo 2026-10-31: file missing'])
def test_an_older_include_of_a_discrete_config_is_removed(tmp_path, monkeypatch, home, where, line):
    target = home / '.task' / 'config' / 'included.rc' if where == 'included.rc' else home / '.taskrc'
    target.write_text(target.read_text() + line + '\n')
    script = installer(tmp_path, monkeypatch, {'demo.rc': DISCRETE})
    out = run(script, home, {'demo.rc': DISCRETE})
    assert 'demo.rc' not in chain(home)
    assert 'other.rc' in chain(home) and 'included.rc' in chain(home)   # nothing else touched
    assert 'reads its own settings' in out


def test_removing_a_discrete_include_spares_a_similar_name(tmp_path, monkeypatch, home):
    inc = home / '.task' / 'config' / 'included.rc'
    inc.write_text(inc.read_text() + 'include ~/.task/config/old-demo.rc\ninclude ~/.task/config/demo.rc\n')
    script = installer(tmp_path, monkeypatch, {'demo.rc': DISCRETE})
    run(script, home, {'demo.rc': DISCRETE})
    assert 'old-demo.rc' in inc.read_text()
    assert 'config/demo.rc' not in inc.read_text()


# ── Included: the exception ───────────────────────────────────────────────────

def test_a_declared_config_is_included(tmp_path, monkeypatch, home):
    script = installer(tmp_path, monkeypatch, {'demo.rc': DISCRETE}, included=['demo.rc'])
    run(script, home, {'demo.rc': DISCRETE})
    assert 'include ~/.task/config/demo.rc' in chain(home)


def test_native_keys_include_an_undeclared_config_with_a_warning(tmp_path, monkeypatch, home, capsys):
    script = installer(tmp_path, monkeypatch, {'demo.rc': NATIVE})
    assert 'included=demo.rc' in capsys.readouterr().out
    run(script, home, {'demo.rc': NATIVE})
    assert 'include ~/.task/config/demo.rc' in chain(home)


def test_each_config_is_decided_on_its_own(tmp_path, monkeypatch, home):
    """Only the first config was ever included before; now each is included or discrete."""
    script = installer(tmp_path, monkeypatch, {'demo.rc': DISCRETE, 'demo-udas.rc': NATIVE,
                                               'extra.rc': DISCRETE}, included=['extra.rc'])
    run(script, home, {'demo.rc': DISCRETE, 'demo-udas.rc': NATIVE, 'extra.rc': DISCRETE})
    c = chain(home)
    assert 'config/demo.rc' not in c
    assert 'include ~/.task/config/demo-udas.rc' in c and 'include ~/.task/config/extra.rc' in c


def test_remove_drops_every_configs_include(tmp_path, monkeypatch, home):
    script = installer(tmp_path, monkeypatch, {'demo.rc': NATIVE, 'extra.rc': DISCRETE},
                       included=['extra.rc'])
    run(script, home, {'demo.rc': NATIVE, 'extra.rc': DISCRETE})
    run(script, home, {}, action='remove')
    assert 'demo.rc' not in chain(home) and 'extra.rc' not in chain(home)
    assert 'other.rc' in chain(home)


# ── The .meta keeps the declaration ───────────────────────────────────────────

def test_meta_round_trips_included(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    info = ma.ProjectInfo()
    info.name, info.version, info.repo = 'demo', '1.0', 'someone/demo'
    info.files, info.checksums = [('demo.rc', 'config'), ('udas.rc', 'config')], ['a', 'b']
    info.included = ['udas.rc']
    assert ma.generate_meta_file(info)
    assert 'included=udas.rc\n' in Path('demo.meta').read_text()
    assert ma.meta_included(Path('demo.meta')) == ['udas.rc']
