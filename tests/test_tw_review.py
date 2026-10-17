"""tw 2.11.0: three findings from the 2026-10-17 review of tw.

1. A wrapper keyword shadowed tw's own flags and task text: `tw -I events` ran the
   `events` wrapper, and `tw add sync phone contacts` ran a git sync instead of adding
   a task. A keyword now counts only before the command word (or `--`), and never when
   tw's own flag comes first.
2. With a filter wrapper registered, anything not on a short list of write commands went
   through the filter's PTY (nobody answers prompts there) with rc.dateformat forced:
   `tw 5 del` hung, `tw 5 mod due:10/20/2026` parsed in the wrong format. Now only a
   command that is (or resolves to) a report goes through filters.
3. `tw -u` ignored a failed remove and installed on top; a failed install's restore
   appended the backup's manifest entries next to whatever was there (duplicates).

Throwaway HOME only; nothing here runs a wrapper, task with real data, or an installer.
"""
import importlib.machinery
import importlib.util
from pathlib import Path

import pytest

TW = Path(__file__).resolve().parent.parent / 'tw'
loader = importlib.machinery.SourceFileLoader('tw_cli_review', str(TW))
spec = importlib.util.spec_from_loader('tw_cli_review', loader)
tw = importlib.util.module_from_spec(spec)
loader.exec_module(tw)


# ── 1. wrapper keywords ───────────────────────────────────────────────────────

@pytest.fixture
def wrappers(tmp_path, monkeypatch):
    f = tmp_path / '.tw_wrappers'
    f.write_text('\n'.join([
        'ann|annn|annotations|command',
        'checkup|sanity-check|sanity|command',
        'deps|deps|dependency tree|command',
        'theme|theme-select.py|themes|command',
        'sync|tw-sync|git sync|command',
        'events|events|holidays, moon|command',
        'nice|nicedates|dates|filter',
    ]) + '\n')
    monkeypatch.setattr(tw.WrapperManager, 'WRAPPERS_FILE', f)
    return tw.WrapperManager()


@pytest.mark.parametrize('args', [
    ['-I', 'events'], ['-u', 'events'], ['-r', 'events'], ['-i', 'events'], ['-R', 'events'],
    ['--install', 'events'], ['--update', 'events'], ['--remove', 'events'], ['--verify', 'events'],
    ['-I', 'sync'], ['-l', 'theme'],
])
def test_tw_flags_are_never_a_wrapper(wrappers, args):
    assert wrappers.find_keyword(args) == (None, None, None)


@pytest.mark.parametrize('args', [
    ['add', 'sync', 'phone', 'contacts'],
    ['add', 'review', 'theme', 'colours'],
    ['12', 'annotate', 'see', 'ann.txt'],
    ['12', 'annot', 'see', 'ann.txt'],          # an abbreviation is the command too
    ['add', '--', 'check', 'deps'],
    ['log', 'sync', 'done'],
    ['+work', 'modify', 'events'],
    ['--', 'deps'],
])
def test_task_text_is_never_a_wrapper(wrappers, args):
    assert wrappers.find_keyword(args) == (None, None, None)


@pytest.mark.parametrize('args,want', [
    (['42', 'ann'],             ('ann', ['42'], [])),
    (['42', 'ann.1'],           ('ann', ['42'], ['.1'])),
    (['42', '-ann.1'],          ('ann', ['42'], ['-ann.1'])),
    (['sync'],                  ('sync', [], [])),
    (['sync', 'push'],          ('sync', [], ['push'])),
    (['+work', 'deps'],         ('deps', ['+work'], [])),
    (['project:home', 'deps'],  ('deps', ['project:home'], [])),
    (['--timing', '42', 'ann'], ('ann', ['--timing', '42'], [])),
    (['events', 'init', '--moon', 'yes'], ('events', [], ['init', '--moon', 'yes'])),
    (['home', 'deps'],          ('deps', ['home'], [])),   # a bare filter word isn't a command
])
def test_wrappers_still_dispatch(wrappers, args, want):
    assert wrappers.find_keyword(args) == want


def test_filter_wrappers_are_not_keywords(wrappers):
    assert wrappers.find_keyword(['nice']) == (None, None, None)


# ── 2. which commands go through filter wrappers ──────────────────────────────

VOCAB = {
    'reports': {'list', 'next', 'agenda', 'all', 'long', 'ls', 'minimal', 'newest', 'oldest',
                'overdue', 'ready', 'recurring', 'waiting', 'completed', 'active', 'blocked'},
    'aliases': {'agd': 'edate:today agenda', 'check_edate': '( +PENDING ) modify +edate_checkall',
                'l8': '+LATEST', 'rm': 'delete', 'history': 'history.monthly'},
    'abbreviation': 2,
    'default': 'next',
}


@pytest.mark.parametrize('args,report', [
    ([], True),                                  # bare `tw`: the default command
    (['+work'], True),
    (['list'], True),
    (['project:home', 'li'], True),              # an abbreviation of a report
    (['foo', 'list'], True),                     # a bare filter word, then the report
    (['agd'], True),                             # alias → report
    (['l8'], True),                              # alias → filter only → default report
    (['5', 'del'], False),                       # the review's hang: abbreviated delete
    (['+work', 'mod', 'pri:H'], False),
    (['5', 'mod', 'due:10/20/2026'], False),
    (['log', 'call', 'mum'], False),
    (['add', 'list', 'groceries'], False),       # the command is add; 'list' is text
    (['5'], False),                              # IDs alone: information
    (['rm', '5'], False),                        # alias → delete
    (['check_edate'], False),                    # alias → modify
    (['ne'], False),                             # ambiguous (news, newest, next): task refuses it
    (['history'], False),                        # alias → history.monthly: not a tabular report
    (['calendar'], False),
    (['--', 'list'], True),                      # after --, words are filter text: default report
])
def test_report_classification(args, report):
    assert tw._args_have_report(args, VOCAB) is report


def test_vocab_from_task(monkeypatch):
    shown = '\n'.join(['abbreviation.minimum=3', 'alias.agd=edate:today agenda', 'default.command=list',
                       'report.list.columns=id', 'report.next.columns=id', 'report.next.labels=ID'])
    class R:
        returncode, stdout = 0, shown
    monkeypatch.setattr(tw.subprocess, 'run', lambda *a, **k: R())
    v = tw._task_vocab()
    assert v == {'reports': {'list', 'next'}, 'aliases': {'agd': 'edate:today agenda'},
                 'abbreviation': 3, 'default': 'list'}


def test_a_write_never_goes_through_filters(wrappers, monkeypatch):
    monkeypatch.setattr(tw, '_task_vocab', lambda: VOCAB)
    monkeypatch.setattr(tw.WrapperManager, 'run_through_filters',
                        lambda *a, **k: pytest.fail('a write went through the filter PTY'))
    ran = []
    monkeypatch.setattr(tw.shutil, 'which', lambda name: '/usr/bin/true')
    monkeypatch.setattr(tw.subprocess, 'run',
                        lambda argv, **k: ran.append(argv) or type('R', (), {'returncode': 0})())
    assert tw.pass_through_to_task(['5', 'del']) == 0
    assert ran == [['task', '5', 'del']]


def test_a_report_still_goes_through_filters(wrappers, monkeypatch):
    monkeypatch.setattr(tw, '_task_vocab', lambda: VOCAB)
    monkeypatch.setattr(tw.WrapperManager, 'run_through_filters', lambda self, args, **k: 7)
    assert tw.pass_through_to_task(['+work', 'list']) == 7


# ── 3. tw -u: a failed remove stops the update; a restore leaves no duplicates ──

class Meta(dict):
    pass


@pytest.fixture
def apps(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    (tmp_path / '.task' / 'config').mkdir(parents=True)
    (tmp_path / '.task' / 'hooks').mkdir()
    am = tw.AppManager(tw.PathManager())
    hook = tmp_path / '.task' / 'hooks' / 'on-add_x.py'
    hook.write_text('old hook\n')
    am.manifest.add('x', '1.0', str(hook))
    stage = tmp_path / 'stage'
    stage.mkdir()
    monkeypatch.setattr(am.registry, 'get_meta', lambda name: Meta(version='2.0'))
    monkeypatch.setattr(am, '_stage_downloads', lambda name, meta: stage)
    am.hook = hook
    return am


def entries(am):
    return [(e['app'], e['version'], e['file']) for e in tw.Manifest(am.paths.manifest_file).entries]


def test_failed_remove_stops_the_update(apps, monkeypatch):
    def remove(name):
        apps.hook.unlink()          # got halfway, then failed
        return False
    monkeypatch.setattr(apps, 'remove', remove)
    monkeypatch.setattr(apps, 'install', lambda *a, **k: pytest.fail('installed on top of a failed remove'))
    assert apps.update('x') is False
    assert apps.hook.read_text() == 'old hook\n'
    assert entries(apps) == [('x', '1.0', str(apps.hook))]


def test_failed_install_restores_without_duplicates(apps, monkeypatch):
    def remove(name):
        apps.hook.unlink()
        apps.manifest.remove_app(name)
        return True
    def install(name, stage_dir=None):
        apps.manifest.add('x', '2.0', str(apps.hook))   # the new installer got partway
        return False
    monkeypatch.setattr(apps, 'remove', remove)
    monkeypatch.setattr(apps, 'install', install)
    assert apps.update('x') is False
    assert apps.hook.read_text() == 'old hook\n'
    assert entries(apps) == [('x', '1.0', str(apps.hook))]


def test_restore_after_a_remove_that_kept_the_manifest(apps, monkeypatch):
    # A custom installer's remove that succeeded but left the manifest lines: still one copy each
    monkeypatch.setattr(apps, 'remove', lambda name: True)
    monkeypatch.setattr(apps, 'install', lambda name, stage_dir=None: False)
    assert apps.update('x') is False
    assert entries(apps) == [('x', '1.0', str(apps.hook))]
