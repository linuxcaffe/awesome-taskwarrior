#!/usr/bin/env python3
"""
tw.py - Universal wrapper and package manager for Taskwarrior extensions

Version: 1.3.0
Author: awesome-taskwarrior project
License: MIT
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import configparser

VERSION = "1.3.0"
DEBUG = os.environ.get('TW_DEBUG', '0') == '1'


class Colors:
    """ANSI color codes"""
    RESET = '\033[0m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    
    @classmethod
    def enabled(cls):
        return sys.stdout.isatty()


def colorize(text: str, color: str) -> str:
    if Colors.enabled():
        return f"{color}{text}{Colors.RESET}"
    return text


def debug_print(msg: str) -> None:
    if DEBUG:
        print(f"DEBUG: {msg}", file=sys.stderr)


def error(msg: str) -> None:
    print(colorize(f"Error: {msg}", Colors.RED), file=sys.stderr)


def warning(msg: str) -> None:
    print(colorize(f"Warning: {msg}", Colors.YELLOW), file=sys.stderr)


def info(msg: str) -> None:
    print(colorize(msg, Colors.BLUE))


def success(msg: str) -> None:
    print(colorize(msg, Colors.GREEN))


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = self._find_config()
        self.load()
        
    def _find_config(self) -> Optional[Path]:
        search_paths = [
            Path.home() / '.task' / 'config' / 'tw.config',
            Path.home() / '.task' / 'tw.config',
            Path(__file__).resolve().parent / 'tw.config',
            Path('/etc/tw.config'),
        ]
        
        for path in search_paths:
            if path.exists():
                debug_print(f"Found config: {path}")
                return path
        
        debug_print("No config file found, using defaults")
        return None
    
    def load(self) -> None:
        if self.config_path:
            try:
                self.config.read(self.config_path)
            except Exception as e:
                warning(f"Could not read config file: {e}")
    
    def get(self, section: str, key: str, fallback=None):
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getboolean(self, section: str, key: str, fallback=False):
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback


class PathManager:
    def __init__(self, config: Config):
        self.config = config
        
        # Base installation root
        self.install_root = Path(
            config.get('paths', 'install_root', str(Path.home() / '.task'))
        ).expanduser()
        
        # Subdirectories for different types
        self.hooks_dir = Path(
            config.get('paths', 'hooks_dir', str(self.install_root / 'hooks'))
        ).expanduser()
        
        self.scripts_dir = Path(
            config.get('paths', 'scripts_dir', str(self.install_root / 'scripts'))
        ).expanduser()
        
        self.config_dir = Path(
            config.get('paths', 'config_dir', str(self.install_root / 'config'))
        ).expanduser()
        
        self.logs_dir = Path(
            config.get('paths', 'logs_dir', str(self.install_root / 'logs'))
        ).expanduser()
        
        self.taskrc = Path(
            config.get('paths', 'taskrc', str(Path.home() / '.taskrc'))
        ).expanduser()
        
        # Registry and installers are relative to tw.py location (resolve symlinks)
        tw_dir = Path(__file__).resolve().parent
        self.registry_dir = tw_dir / 'registry.d'
        self.installers_dir = tw_dir / 'installers'
        self.manifest_file = tw_dir / 'installed' / '.manifest'
        self.lib_dir = tw_dir / 'lib'
        
        # Ensure critical directories exist
        self.install_root.mkdir(parents=True, exist_ok=True)
        self.hooks_dir.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        
        debug_print(f"Paths initialized:")
        debug_print(f"  install_root={self.install_root}")
        debug_print(f"  hooks_dir={self.hooks_dir}")
        debug_print(f"  scripts_dir={self.scripts_dir}")
        debug_print(f"  config_dir={self.config_dir}")
        debug_print(f"  logs_dir={self.logs_dir}")


class TaskBinary:
    def __init__(self, config: Config):
        self.config = config
        self.binary_path = self._find_task()
    
    def _find_task(self) -> Optional[str]:
        configured = self.config.get('paths', 'taskwarrior_bin', 'auto')
        
        if configured != 'auto':
            if os.path.isfile(configured) and os.access(configured, os.X_OK):
                debug_print(f"Using configured task: {configured}")
                return configured
            else:
                warning(f"Configured task binary not found: {configured}")
        
        path_env = os.environ.get('PATH', '')
        for path_dir in path_env.split(os.pathsep):
            task_path = os.path.join(path_dir, 'task')
            if os.path.isfile(task_path) and os.access(task_path, os.X_OK):
                debug_print(f"Found task in PATH: {task_path}")
                return task_path
        
        return None
    
    def get_version(self) -> Optional[str]:
        if not self.binary_path:
            return None
        
        try:
            result = subprocess.run(
                [self.binary_path, '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split()[0]
        except Exception:
            return None


class Registry:
    def __init__(self, paths: PathManager):
        self.paths = paths
        self._apps = None
    
    def load_apps(self) -> Dict[str, Dict]:
        if self._apps is not None:
            return self._apps
        
        self._apps = {}
        
        if not self.paths.registry_dir.exists():
            warning(f"Registry directory not found: {self.paths.registry_dir}")
            return self._apps
        
        for meta_file in self.paths.registry_dir.glob('*.meta'):
            try:
                app = self._parse_meta(meta_file)
                if app:
                    self._apps[app['name']] = app
            except Exception as e:
                warning(f"Error loading {meta_file.name}: {e}")
        
        debug_print(f"Loaded {len(self._apps)} apps from registry")
        return self._apps
    
    def _parse_meta(self, meta_file: Path) -> Optional[Dict]:
        app = {}
        current_key = None
        current_value = []
        
        with open(meta_file, 'r') as f:
            for line in f:
                line = line.rstrip()
                
                if not line or line.startswith('#'):
                    continue
                
                if line[0].isspace():
                    if current_key:
                        current_value.append(line.strip())
                    continue
                
                if current_key:
                    app[current_key] = '\n'.join(current_value) if len(current_value) > 1 else current_value[0]
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    current_key = key.strip()
                    current_value = [value.strip()]
        
        if current_key:
            app[current_key] = '\n'.join(current_value) if len(current_value) > 1 else current_value[0]
        
        return app if 'name' in app else None
    
    def get_app(self, name: str) -> Optional[Dict]:
        apps = self.load_apps()
        return apps.get(name)


class Manifest:
    def __init__(self, paths: PathManager):
        self.paths = paths
        self._installed = None
    
    def load(self) -> Dict[str, Dict]:
        if self._installed is not None:
            return self._installed
        
        self._installed = {}
        
        if not self.paths.manifest_file.exists():
            return self._installed
        
        with open(self.paths.manifest_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) == 5:
                    name, version, checksum, install_date, repo_url = parts
                    self._installed[name] = {
                        'version': version,
                        'checksum': checksum,
                        'install_date': install_date,
                        'repo_url': repo_url
                    }
        
        debug_print(f"Loaded {len(self._installed)} installed apps")
        return self._installed
    
    def save(self) -> None:
        with open(self.paths.manifest_file, 'w') as f:
            f.write("# awesome-taskwarrior installation manifest\n")
            f.write("# Format: name|version|checksum|install_date|repo_url\n")
            f.write("#\n")
            
            for name, data in sorted(self._installed.items()):
                f.write(f"{name}|{data['version']}|{data['checksum']}|")
                f.write(f"{data['install_date']}|{data['repo_url']}\n")
    
    def add(self, name: str, version: str, checksum: str, repo_url: str) -> None:
        installed = self.load()
        installed[name] = {
            'version': version,
            'checksum': checksum,
            'install_date': datetime.now().isoformat(),
            'repo_url': repo_url
        }
        self.save()
    
    def remove(self, name: str) -> None:
        installed = self.load()
        if name in installed:
            del installed[name]
            self.save()
    
    def is_installed(self, name: str) -> bool:
        return name in self.load()


class Installer:
    def __init__(self, paths: PathManager, registry: Registry, manifest: Manifest, dry_run: bool = False):
        self.paths = paths
        self.registry = registry
        self.manifest = manifest
        self.dry_run = dry_run
    
    def install(self, name: str) -> bool:
        app = self.registry.get_app(name)
        if not app:
            error(f"App not found in registry: {name}")
            return False
        
        if self.manifest.is_installed(name):
            warning(f"{name} is already installed")
            info("Use --update to update, or --remove then --install to reinstall")
            return False
        
        if self.dry_run:
            info(f"[DRY RUN] Would install {name}...")
            print(f"  Repository: {app.get('repo', 'unknown')}")
            print(f"  Version: {app.get('version', 'unknown')}")
            print(f"  Type: {app.get('type', 'unknown')}")
            
            # Show where it would be installed
            app_type = app.get('type', 'unknown')
            short_name = app.get('short_name', name.replace('tw-', ''))
            if app_type == 'hook':
                install_path = self.paths.hooks_dir / short_name
            elif app_type in ['wrapper', 'utility']:
                install_path = self.paths.scripts_dir / short_name
            else:
                install_path = self.paths.install_root / short_name
            
            print(f"  Would clone to: {install_path}")
            
            if 'provides' in app:
                print(f"  Provides: {app['provides']}")
            if 'requires' in app:
                print(f"  Requires: {app['requires']}")
            print(f"  Installer: {app['install_script']}")
            
            if app_type == 'hook':
                print(f"  Would create hook symlinks in: {self.paths.hooks_dir}")
            elif app_type in ['wrapper', 'utility']:
                print(f"  Would create script symlinks in: {self.paths.scripts_dir}")
            
            print(f"  Would add to manifest")
            success(f"[DRY RUN] Installation preview complete")
            return True
        
        info(f"Installing {name}...")
        
        installer_script = self.paths.installers_dir / app['install_script']
        if not installer_script.exists():
            error(f"Installer script not found: {installer_script}")
            return False
        
        if not self._run_installer(installer_script, 'install'):
            error(f"Installation failed for {name}")
            return False
        
        self.manifest.add(
            name,
            app.get('version', 'unknown'),
            app.get('checksum', ''),
            app.get('repo', '')
        )
        
        success(f"✓ Installed {name}")
        return True
    
    def remove(self, name: str) -> bool:
        if not self.manifest.is_installed(name):
            error(f"{name} is not installed")
            return False
        
        app = self.registry.get_app(name)
        
        if self.dry_run:
            info(f"[DRY RUN] Would remove {name}...")
            installed_info = self.manifest.load()[name]
            print(f"  Installed version: {installed_info['version']}")
            print(f"  Install date: {installed_info['install_date']}")
            if app:
                print(f"  Would run uninstaller: {app['install_script']}")
            print(f"  Would remove from manifest")
            success(f"[DRY RUN] Removal preview complete")
            return True
        
        info(f"Removing {name}...")
        
        if app:
            installer_script = self.paths.installers_dir / app['install_script']
        else:
            installer_script = self.paths.installers_dir / f"{name}.install"
        
        if installer_script.exists():
            if not self._run_installer(installer_script, 'uninstall'):
                error(f"Uninstallation failed for {name}")
                return False
        else:
            warning(f"Installer script not found, removing from manifest only")
        
        self.manifest.remove(name)
        success(f"✓ Removed {name}")
        return True
    
    def update(self, name: str) -> bool:
        if not self.manifest.is_installed(name):
            error(f"{name} is not installed")
            return False
        
        app = self.registry.get_app(name)
        if not app:
            error(f"App not found in registry: {name}")
            return False
        
        if self.dry_run:
            info(f"[DRY RUN] Would update {name}...")
            installed_info = self.manifest.load()[name]
            print(f"  Current version: {installed_info['version']}")
            print(f"  Available version: {app.get('version', 'unknown')}")
            print(f"  Would run updater or reinstall")
            success(f"[DRY RUN] Update preview complete")
            return True
        
        info(f"Updating {name}...")
        
        installer_script = self.paths.installers_dir / app['install_script']
        if not installer_script.exists():
            error(f"Installer script not found: {installer_script}")
            return False
        
        if self._run_installer(installer_script, 'update', allow_fail=True):
            success(f"✓ Updated {name}")
        else:
            info("Update function not available, reinstalling...")
            if not self.remove(name) or not self.install(name):
                return False
        
        return True
    
    def _run_installer(self, script: Path, command: str, allow_fail: bool = False) -> bool:
        env = os.environ.copy()
        env['INSTALL_DIR'] = str(self.paths.install_root)
        env['HOOKS_DIR'] = str(self.paths.hooks_dir)
        env['SCRIPTS_DIR'] = str(self.paths.scripts_dir)
        env['CONFIG_DIR'] = str(self.paths.config_dir)
        env['LOGS_DIR'] = str(self.paths.logs_dir)
        env['TASKRC'] = str(self.paths.taskrc)
        env['TW_DEBUG'] = '1' if DEBUG else '0'
        
        debug_print(f"Running: {script} {command}")
        
        try:
            result = subprocess.run(
                ['bash', str(script), command],
                env=env,
                check=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            if not allow_fail:
                error(f"Installer exited with code {e.returncode}")
            return False
        except Exception as e:
            error(f"Failed to run installer: {e}")
            return False


class AppLister:
    def __init__(self, registry: Registry, manifest: Manifest):
        self.registry = registry
        self.manifest = manifest
    
    def list_all(self) -> None:
        apps = self.registry.load_apps()
        installed = self.manifest.load()
        
        if not apps:
            info("No apps available in registry")
            return
        
        by_type = {}
        for name, app in apps.items():
            app_type = app.get('type', 'unknown')
            if app_type not in by_type:
                by_type[app_type] = []
            by_type[app_type].append((name, app))
        
        print(colorize("\nAvailable Taskwarrior Extensions:\n", Colors.BOLD))
        
        for app_type in ['hook', 'wrapper', 'utility', 'web']:
            if app_type not in by_type:
                continue
            
            print(colorize(f"{app_type.upper()}S", Colors.BOLD))
            
            for name, app in sorted(by_type[app_type]):
                status = ""
                if name in installed:
                    status = colorize(f"[installed v{installed[name]['version']}]", Colors.GREEN)
                
                desc = app.get('short_desc', 'No description')
                print(f"  {name:20} {status:30} {desc}")
            
            print()
        
        print("Use 'tw --info <name>' for details")
        print("Use 'tw --install <name>' to install\n")
    
    def list_installed(self) -> None:
        installed = self.manifest.load()
        
        if not installed:
            info("No apps installed")
            print("Use 'tw --list' to see available apps\n")
            return
        
        print(colorize("\nInstalled Extensions:\n", Colors.BOLD))
        
        for name, data in sorted(installed.items()):
            print(f"  {name:20} v{data['version']:10} {data['install_date']}")
        
        print()
    
    def list_tags(self) -> None:
        apps = self.registry.load_apps()
        
        all_tags = set()
        for app in apps.values():
            if 'tags' in app:
                tags = [t.strip() for t in app['tags'].split(',')]
                all_tags.update(tags)
        
        if not all_tags:
            info("No tags defined")
            return
        
        print(colorize("\nAvailable Tags:\n", Colors.BOLD))
        for tag in sorted(all_tags):
            count = sum(1 for app in apps.values() 
                       if 'tags' in app and tag in app['tags'])
            print(f"  +{tag:20} ({count} app{'s' if count != 1 else ''})")
        print()
        print("Use 'tw --list +tag1 +tag2' to filter\n")
    
    def list_by_tags(self, tags: List[str]) -> None:
        apps = self.registry.load_apps()
        installed = self.manifest.load()
        
        matching = []
        for name, app in apps.items():
            if 'tags' not in app:
                continue
            app_tags = [t.strip() for t in app['tags'].split(',')]
            if all(tag in app_tags for tag in tags):
                matching.append((name, app))
        
        if not matching:
            info(f"No apps with tags: {', '.join(['+'+t for t in tags])}")
            return
        
        tag_display = ' '.join([colorize(f'+{t}', Colors.BLUE) for t in tags])
        print(f"\nApps matching {tag_display}:\n")
        
        for name, app in sorted(matching):
            status = ""
            if name in installed:
                status = colorize(f"[installed v{installed[name]['version']}]", Colors.GREEN)
            
            desc = app.get('short_desc', 'No description')
            all_tags = app.get('tags', '')
            print(f"  {name:20} {status:30} {desc}")
            print(f"    Tags: {all_tags}")
        
        print()
    
    def show_info(self, name: str) -> None:
        app = self.registry.get_app(name)
        if not app:
            error(f"App not found: {name}")
            return
        
        installed = self.manifest.load()
        
        print(colorize(f"\n{app['name']}", Colors.BOLD))
        print("=" * 60)
        
        print(f"Type:        {app.get('type', 'unknown')}")
        print(f"Version:     {app.get('version', 'unknown')}")
        
        if name in installed:
            print(colorize(f"Installed:   Yes (v{installed[name]['version']})", Colors.GREEN))
        else:
            print(f"Installed:   No")
        
        if 'short_name' in app:
            print(f"Short name:  {app['short_name']}")
        
        print(f"Author:      {app.get('author', 'unknown')}")
        print(f"Repository:  {app.get('repo', 'unknown')}")
        
        if 'requires' in app:
            print(f"Requires:    {app['requires']}")
        
        if 'tags' in app:
            tags = ' '.join([f'+{t.strip()}' for t in app['tags'].split(',')])
            print(f"Tags:        {tags}")
        
        if 'wrapper' in app and app['wrapper'] == 'yes':
            print(colorize("Wrapper:     Yes (can be used in wrapper chain)", Colors.BLUE))
        
        print()
        desc = app.get('long_desc', app.get('short_desc', 'No description available'))
        print(desc)
        print()


def generate_completion_script():
    """Generate bash completion script for tw"""
    script = '''# Bash completion for tw (awesome-taskwarrior)
_tw_completion() {
    local cur prev words cword
    _init_completion -n : || return

    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Complete tw flags
    if [[ "$cur" == --* ]]; then
        local flags="--list --list-installed --info --install --remove --update"
        flags="$flags --version --help --debug --dry-run --get-completion"
        COMPREPLY=($(compgen -W "$flags" -- "$cur"))
        return 0
    fi

    # Complete app names after --info, --install, --remove, --update
    case "$prev" in
        --info|--install|--remove|--update)
            local apps=$(tw --complete-apps 2>/dev/null)
            COMPREPLY=($(compgen -W "$apps" -- "$cur"))
            return 0
            ;;
    esac

    # Special handling for --list
    if [[ "$prev" == "--list" ]]; then
        # Complete "tags" or "+tag"
        if [[ "$cur" == +* ]]; then
            local tags=$(tw --complete-tags 2>/dev/null)
            COMPREPLY=($(compgen -W "$tags" -- "$cur"))
        else
            COMPREPLY=($(compgen -W "tags" -- "$cur"))
        fi
        return 0
    fi

    # Complete additional tags after "tw --list +sometag"
    if [[ "${COMP_WORDS[1]}" == "--list" ]] && [[ "$cur" == +* ]]; then
        local tags=$(tw --complete-tags 2>/dev/null)
        COMPREPLY=($(compgen -W "$tags" -- "$cur"))
        return 0
    fi

    # For tw-specific commands that need no further completion
    case "${COMP_WORDS[1]}" in
        --list-installed|--version|--help|--get-completion|-h)
            return 0
            ;;
    esac

    # If first word is a tw flag, no further completion
    if [[ "${COMP_WORDS[1]}" == --* ]]; then
        return 0
    fi

    # Otherwise, delegate to task completion for normal task commands
    if declare -F _task >/dev/null 2>&1; then
        # Modify COMP_WORDS in place for task
        local i
        for ((i=0; i < ${#COMP_WORDS[@]}; i++)); do
            if [[ $i -eq 0 ]]; then
                COMP_WORDS[i]="task"
            fi
        done
        
        _task
        return 0
    fi
    
    # No task completion available, return empty to avoid file completion
    COMPREPLY=()
    return 0
}

complete -F _tw_completion tw
'''
    print(script)


def complete_apps(registry: Registry):
    """Output app names for completion"""
    apps = registry.load_apps()
    print(' '.join(sorted(apps.keys())))


def complete_tags(registry: Registry):
    """Output tags for completion"""
    apps = registry.load_apps()
    all_tags = set()
    for app in apps.values():
        if 'tags' in app:
            tags = [t.strip() for t in app['tags'].split(',')]
            all_tags.update(tags)
    print(' '.join([f'+{tag}' for tag in sorted(all_tags)]))


def handle_version(task_bin: TaskBinary) -> None:
    print(f"tw.py version {VERSION}")
    
    if task_bin.binary_path:
        tw_version = task_bin.get_version()
        if tw_version:
            print(f"taskwarrior {tw_version}")
        else:
            print("taskwarrior version unknown")
    else:
        warning("taskwarrior not found")
        print("Install with: tw --install-taskwarrior")


def passthrough_to_task(task_bin: TaskBinary, args: List[str]) -> int:
    if not task_bin.binary_path:
        error("Taskwarrior not found in PATH")
        print("Install with: tw --install-taskwarrior")
        return 1
    
    debug_print(f"Passthrough: {' '.join([task_bin.binary_path] + args)}")
    
    try:
        os.execv(task_bin.binary_path, ['task'] + args)
    except OSError as e:
        error(f"Error executing task: {e}")
        return 1


def main():
    global DEBUG
    
    dry_run = False
    if '--debug' in sys.argv:
        DEBUG = True
        sys.argv.remove('--debug')
        debug_print("Debug mode enabled")
    
    if '--dry-run' in sys.argv:
        dry_run = True
        sys.argv.remove('--dry-run')
        info("[DRY RUN MODE]\n")
    
    config = Config()
    paths = PathManager(config)
    task_bin = TaskBinary(config)
    registry = Registry(paths)
    manifest = Manifest(paths)
    installer = Installer(paths, registry, manifest, dry_run)
    lister = AppLister(registry, manifest)
    
    if len(sys.argv) < 2:
        return passthrough_to_task(task_bin, [])
    
    arg = sys.argv[1]
    
    # Completion handlers (before other flags)
    if arg == '--get-completion':
        generate_completion_script()
        return 0
    
    elif arg == '--complete-apps':
        complete_apps(registry)
        return 0
    
    elif arg == '--complete-tags':
        complete_tags(registry)
        return 0
    
    # Regular command handlers
    if arg == '--version':
        handle_version(task_bin)
        return 0
    
    elif arg == '--list':
        if len(sys.argv) > 2:
            if sys.argv[2] == 'tags':
                lister.list_tags()
                return 0
            elif sys.argv[2].startswith('+'):
                tags = [a[1:] for a in sys.argv[2:] if a.startswith('+')]
                if tags:
                    lister.list_by_tags(tags)
                    return 0
        
        lister.list_all()
        return 0
    
    elif arg == '--list-installed':
        lister.list_installed()
        return 0
    
    elif arg == '--info':
        if len(sys.argv) < 3:
            error("--info requires app name")
            return 1
        lister.show_info(sys.argv[2])
        return 0
    
    elif arg == '--install':
        if len(sys.argv) < 3:
            error("--install requires app name")
            return 1
        return 0 if installer.install(sys.argv[2]) else 1
    
    elif arg == '--remove':
        if len(sys.argv) < 3:
            error("--remove requires app name")
            return 1
        return 0 if installer.remove(sys.argv[2]) else 1
    
    elif arg == '--update':
        if len(sys.argv) < 3:
            error("--update requires app name")
            return 1
        return 0 if installer.update(sys.argv[2]) else 1
    
    elif arg == '--help' or arg == '-h':
        print(f"""tw.py v{VERSION} - Taskwarrior wrapper and extension manager

USAGE:
    tw [OPTIONS] [TASK_COMMAND]

PACKAGE MANAGEMENT:
    --list                  List all available extensions
    --list tags             List all available tags
    --list +tag1 +tag2      Filter by tags (AND logic)
    --list-installed        List installed extensions
    --info <app>            Show detailed info
    --install <app>         Install extension
    --remove <app>          Remove extension
    --update <app>          Update extension

OPTIONS:
    --dry-run               Preview without making changes
    --version               Show version
    --help, -h              Show this help
    --debug                 Enable debug output
    --get-completion        Output bash completion script

COMPLETION:
    Add to ~/.bashrc:       eval "$(tw --get-completion)"
    Then use tab completion with tw commands and app names

DIRECTORY STRUCTURE:
    ~/.task/hooks/          Hook projects and symlinks
    ~/.task/scripts/        Wrapper projects and symlinks
    ~/.task/config/         Configuration files
    ~/.task/logs/           Debug and test logs

EXAMPLES:
    tw --list
    tw --list tags
    tw --list +hook +scheduling
    tw --dry-run --install tw-recurrence
    tw --install tw-recurrence
    tw next

For more: README.md and DEVELOPERS.md
""")
        return 0
    
    else:
        return passthrough_to_task(task_bin, sys.argv[1:])


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        if DEBUG:
            raise
        error(f"Unexpected error: {e}")
        sys.exit(1)
