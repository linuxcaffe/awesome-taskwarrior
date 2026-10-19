"""make-awesome 4.13.0: links= in a .meta makes the generated installer create a symlink
(recurrence-overhaul's on-modify -> on-add), record it, and remove it."""
import importlib.machinery
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('make_awesome_links', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_links', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)


def test_parse_links():
    assert ma.parse_links('a.py:b.py:hook, c:d:script,bad,x::hook') == [
        ('a.py', 'b.py', 'hook'), ('c', 'd', 'script')]


def test_meta_and_installer_carry_links(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    info = ma.ProjectInfo()
    info.name, info.version, info.repo = 'demo', '1.0', 'someone/demo'
    info.files = [('on-add_demo.py', 'hook')]
    info.checksums = ['abc']
    info.links = [('on-modify_demo.py', 'on-add_demo.py', 'hook')]
    assert ma.generate_meta_file(info)
    assert 'links=on-modify_demo.py:on-add_demo.py:hook' in Path('demo.meta').read_text()
    assert ma.generate_installer(info)
    text = Path('demo.install').read_text()
    assert 'ln -sfn "on-add_demo.py" "$HOOKS_DIR/on-modify_demo.py"' in text
    assert '$HOOKS_DIR/on-modify_demo.py||$TIMESTAMP' in text
    assert '[ -L "$file" ]' in text                     # a dangling link is still removed
    assert subprocess.run(['bash', '-n', 'demo.install']).returncode == 0
