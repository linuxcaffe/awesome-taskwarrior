"""make-awesome 4.16.1: the debug stage keeps a file's own imports whole.

2026-10-22: adding the debug block to recurrence_rules.py dropped its
`from datetime import datetime, timedelta, timezone` as a duplicate of the block's
`from datetime import datetime`, so timedelta and timezone were gone and recurrence-overhaul
3.1.0 spawned nothing. Only a line the block itself writes is a duplicate."""
import importlib.machinery
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_debug_imports', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_debug_imports', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)

IMPORTS = '''from datetime import datetime, timedelta, timezone
from datetime import date
from pathlib import Path, PurePosixPath
import os
import sys
'''

USE = '''
print(timedelta(days=1), timezone.utc, date(2030, 1, 1), PurePosixPath('a'), os.sep, sys.version_info[0])
'''


def enhance(tmp_path, text):
    f = tmp_path / 'lib.py'
    f.write_text(text)
    assert ma.process_python_file(str(f))
    return f


def runs(f):
    r = subprocess.run([sys.executable, str(f)], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stderr


def test_new_debug_keeps_the_names_a_file_imports(tmp_path):
    f = enhance(tmp_path, '"""a library"""\n' + IMPORTS + USE)
    code, err = runs(f)
    assert code == 0, err
    text = f.read_text()
    assert 'from datetime import datetime, timedelta, timezone\n' in text
    assert 'from pathlib import Path, PurePosixPath\n' in text


def test_existing_debug_keeps_the_names_a_file_imports(tmp_path):
    f = enhance(tmp_path, '"""a hook"""\n' + IMPORTS + '\nDEBUG = 0\n' + USE)
    code, err = runs(f)
    assert code == 0, err
    assert 'from datetime import datetime, timedelta, timezone\n' in f.read_text()


def test_the_blocks_own_imports_are_not_doubled(tmp_path):
    f = enhance(tmp_path, '"""a library"""\nimport os\nimport sys\nfrom datetime import datetime\n'
                          'print(os.sep, sys.argv[0], datetime(2030, 1, 1))\n')
    text = f.read_text()
    assert text.count('\nimport os\n') == 1 and text.count('\nimport sys\n') == 1
    assert text.count('from datetime import datetime\n') == 1
    assert runs(f)[0] == 0
