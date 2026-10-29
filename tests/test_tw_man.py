"""tw 2.20.0 / make-awesome 4.17.0: man pages (CONVENTIONS §8, Man pages).

- A doc named <name>.<1-9> installs to ~/.task/docs/man/man<N>/ under its own name.
- A page another app owns (manifest) stops the generated install before anything is placed.
- tw -R lists man pages and opens one with man -l; a README wins over a page of the same name.

Throwaway HOME; generated installers fetch from a file:// BASE_URL.
"""
import importlib.machinery
import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_ld = importlib.machinery.SourceFileLoader('tw_cli_man', str(ROOT / 'tw'))
_sp = importlib.util.spec_from_loader('tw_cli_man', _ld)
tw = importlib.util.module_from_spec(_sp)
_ld.exec_module(tw)
_ld = importlib.machinery.SourceFileLoader('make_awesome_man', str(ROOT / 'make-awesome.py'))
_sp = importlib.util.spec_from_loader('make_awesome_man', _ld)
ma = importlib.util.module_from_spec(_sp)
_ld.exec_module(ma)


def test_man_section():
    for mod in (tw, ma):
        assert mod.man_section('vit.1') == '1'
        assert mod.man_section('vitrc.5') == '5'
        assert mod.man_section('README.md') is None
        assert mod.man_section('notes.10') is None
        assert mod.man_section('vit') is None


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project with a script, a README and two man pages, and its generated installer."""
    src = tmp_path / 'src'
    src.mkdir()
    monkeypatch.chdir(src)
    Path('demo').write_text('#!/bin/bash\necho demo\n')
    Path('demo').chmod(0o755)
    Path('README.md').write_text('# demo\n')
    Path('demo.1').write_text('.TH DEMO 1\n.SH NAME\ndemo\n')
    Path('demorc.5').write_text('.\\" settings\n.TH DEMORC 5\n')
    Path('notes.1').write_text('not roff\n')               # a .1 that isn't a man page
    info = ma.ProjectInfo()
    info.name, info.version, info.repo = 'demo', '1.0', 'someone/demo'
    info.files = ma.detect_files()
    assert ma.generate_installer(info)
    text = Path('demo.install').read_text().replace(
        'BASE_URL="https://raw.githubusercontent.com/someone/demo/main"', f'BASE_URL="file://{src}"')
    Path('demo.install').write_text(text)
    home = tmp_path / 'home'
    (home / '.task' / 'config').mkdir(parents=True)
    return src, home, info


def run_install(src, home):
    env = dict(os.environ, HOME=str(home))
    env.pop('TW_TASK_DIR', None)
    return subprocess.run(['bash', str(src / 'demo.install'), 'install'], env=env,
                          capture_output=True, text=True)


def test_detect_files_finds_roff_pages_only(project):
    _, _, info = project
    names = [n for n, t in info.files if t == 'doc']
    assert 'demo.1' in names and 'demorc.5' in names
    assert 'notes.1' not in names


def test_install_places_pages_under_their_own_names(project):
    src, home, _ = project
    r = run_install(src, home)
    assert r.returncode == 0, r.stderr
    man = home / '.task' / 'docs' / 'man'
    assert (man / 'man1' / 'demo.1').is_file()
    assert (man / 'man5' / 'demorc.5').is_file()
    assert (home / '.task' / 'docs' / 'demo_README.md').is_file()
    manifest = (home / '.task' / 'config' / '.tw_manifest').read_text()
    assert f'demo|1.0|{man}/man1/demo.1|' in manifest
    assert 'Manual: man demo' in r.stdout


@pytest.mark.parametrize('recorded', ['~/.task/docs/man/man5/demorc.5', '{home}/.task/docs/man/man5/demorc.5'])
def test_page_owned_by_another_app_stops_the_install(project, recorded):
    src, home, _ = project
    manifest = home / '.task' / 'config' / '.tw_manifest'
    manifest.write_text(f'other|2.0|{recorded.format(home=home)}||x\n')
    r = run_install(src, home)
    assert r.returncode != 0
    assert 'belongs to other' in r.stderr
    assert not (home / '.task' / 'scripts' / 'demo').exists()     # stopped before anything was placed


def test_own_page_is_replaced(project):
    src, home, _ = project
    (home / '.task' / 'config' / '.tw_manifest').write_text('demo|0.9|~/.task/docs/man/man1/demo.1||x\n')
    assert run_install(src, home).returncode == 0


@pytest.fixture
def docs(tmp_path):
    d = tmp_path / 'docs'
    (d / 'man' / 'man1').mkdir(parents=True)
    (d / 'man' / 'man5').mkdir()
    (d / 'vit_README.md').write_text('# vit\n')
    (d / 'man' / 'man1' / 'vit.1').write_text('.TH VIT 1\n')
    (d / 'man' / 'man5' / 'vitrc.5').write_text('.TH VITRC 5\n')
    return d


def opened(monkeypatch, docs, query):
    calls = []
    monkeypatch.setattr(tw.os, 'execvp', lambda f, argv: calls.append(argv))
    monkeypatch.setattr(tw, '_md_viewer', lambda: ['cat'])
    monkeypatch.setattr(tw.shutil, 'which', lambda name: '/usr/bin/' + name)
    tw.readme_cmd(docs, query, docs / 'man')
    return calls[0]


def test_readme_lists_man_pages(docs, capsys):
    assert tw.readme_cmd(docs, '', docs / 'man') == 0
    out = capsys.readouterr().out
    assert 'vit(1)' in out and 'vitrc(5)' in out
    assert 'man1/vit.1' in out


def test_readme_wins_over_page_of_same_name(monkeypatch, docs):
    assert opened(monkeypatch, docs, 'vit') == ['cat', str(docs / 'vit_README.md')]


def test_page_opens_with_man_l(monkeypatch, docs):
    assert opened(monkeypatch, docs, 'vit.1') == ['man', '-l', str(docs / 'man' / 'man1' / 'vit.1')]
    assert opened(monkeypatch, docs, 'vitrc') == ['man', '-l', str(docs / 'man' / 'man5' / 'vitrc.5')]
