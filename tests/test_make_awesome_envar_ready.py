"""make-awesome 4.14.2: envar_ready = yes only when no hard-coded ~/.task path remains.

2026-10-20: the envar stage found nothing it knew how to patch in smart-nag, had no failures, and
wrote envar_ready = yes, though on-launch_smart-nag.py builds every path from Path.home() / '.task'.
The line had been reverted by hand once already; the next pipeline run put it back."""
import importlib.machinery
import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_envar_ready', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_envar_ready', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)

RC = '''[demo]
type        = hook
envar_ready = no
'''

HARDCODED = '''#!/usr/bin/env python3
"""Demo hook."""
from pathlib import Path
# state lives in ~/.task/config
STATE = Path.home() / '.task' / 'config' / 'demo.rc'
'''

ISOLATED = '''#!/usr/bin/env python3
"""Demo hook."""
import os
from pathlib import Path
TASK_DIR = Path(os.environ.get('TW_TASK_DIR', str(Path.home() / '.task')))
STATE = TASK_DIR / 'config' / 'demo.rc'
'''


def setup(tmp_path, monkeypatch, hook):
    fleet = tmp_path / 'fleet'
    fleet.mkdir()
    (fleet / 'awesome.rc').write_text(RC)
    monkeypatch.setattr(ma, 'SCRIPT_DIR', fleet)          # never the real awesome.rc
    d = tmp_path / 'tw-demo-hook'
    d.mkdir()
    (d / 'demo.meta').write_text('name=demo\nversion=1.0.0\n')
    (d / 'on-add_demo.py').write_text(hook)
    monkeypatch.chdir(d)
    return fleet / 'awesome.rc'


def test_hardcoded_task_dir_found(tmp_path):
    f = tmp_path / 'h.py'
    f.write_text(HARDCODED)
    assert [n for n, _ in ma.hardcoded_task_dir(f)] == [5]     # the comment doesn't count
    f.write_text(ISOLATED)
    assert ma.hardcoded_task_dir(f) == []                     # a TW_TASK_DIR default is fine


def test_not_ready_while_a_path_is_hardcoded(tmp_path, monkeypatch):
    rc = setup(tmp_path, monkeypatch, HARDCODED)
    assert ma.cmd_envar(SimpleNamespace(dry_run=False, force=False)) == 0
    assert 'envar_ready = no' in rc.read_text()


def test_ready_when_every_path_honours_TW_TASK_DIR(tmp_path, monkeypatch):
    rc = setup(tmp_path, monkeypatch, ISOLATED)
    assert ma.cmd_envar(SimpleNamespace(dry_run=False, force=False)) == 0
    assert 'envar_ready = yes' in rc.read_text()
