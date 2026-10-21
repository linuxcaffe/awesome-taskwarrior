"""make-awesome 4.14.2: the timing block goes below a module docstring, never above it.

2026-10-20: the pipeline put the block straight after nag's shebang, above its docstring, so the
docstring stopped being the module's first statement, __doc__ became None and `nag -h` crashed
(smart-nag 1.3.1)."""
import ast
import importlib.machinery
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_timing_doc', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_timing_doc', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)

SCRIPT = '''#!/usr/bin/env python3
"""
demo - a command

  demo -h   help
"""

import sys
print(__doc__)
'''


def write(tmp_path, text, name='demo'):
    f = tmp_path / name
    f.write_text(text)
    return f


def docstring(f):
    return ast.get_docstring(ast.parse(f.read_text()))


def block_line(f):
    return next(i for i, l in enumerate(f.read_text().splitlines()) if 'import os as _os_timing' in l)


def test_block_goes_below_the_docstring(tmp_path):
    f = write(tmp_path, SCRIPT)
    assert ma.inject_timing_block(str(f))
    assert docstring(f).startswith('demo - a command')
    lines = f.read_text().splitlines()
    assert block_line(f) < lines.index('import sys')        # still ahead of every import


def test_no_docstring_still_right_after_the_shebang(tmp_path):
    f = write(tmp_path, '#!/usr/bin/env python3\nimport sys\n')
    assert ma.inject_timing_block(str(f))
    assert block_line(f) == 1


def test_a_block_above_the_docstring_is_moved_below_it(tmp_path):
    lines = SCRIPT.splitlines(keepends=True)
    f = write(tmp_path, lines[0] + ma._TIMING_BLOCK + ''.join(lines[1:]))
    assert docstring(f) is None                               # the 1.3.1 nag
    assert ma.inject_timing_block(str(f))                     # no --force needed
    assert docstring(f).startswith('demo - a command')
    assert f.read_text().count('import os as _os_timing') == 1
    assert not ma.inject_timing_block(str(f))                 # now in place: skipped


def test_dry_run_reports_the_move_and_writes_nothing(tmp_path):
    lines = SCRIPT.splitlines(keepends=True)
    text = lines[0] + ma._TIMING_BLOCK + ''.join(lines[1:])
    f = write(tmp_path, text)
    assert ma.inject_timing_block(str(f), dry_run=True)
    assert f.read_text() == text
