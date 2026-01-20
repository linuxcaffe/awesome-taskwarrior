#!/usr/bin/env python3
"""
tw.py - Universal wrapper and package manager for Taskwarrior extensions

Version: 1.0.0
Author: awesome-taskwarrior project
License: MIT

This script serves dual purposes:
1. Transparent pass-through wrapper for Taskwarrior commands
2. Package manager for Taskwarrior extensions (hooks, wrappers, utilities)
"""

import sys
import os
import subprocess
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import configparser
import shutil

VERSION = "1.0.0"

# Enable debug mode via environment or flag
DEBUG = os.environ.get('TW_DEBUG', '0') == '1'


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    
    @classmethod
    def enabled(cls):
        """Check if colors should be used"""
        return sys.stdout.isatty()


def colorize(text: str, color: str) -> str:
    """Add color to text if terminal supports it"""
    if Colors.enabled():
        return f"{color}{text}{Colors.RESET}"
    return text


def debug_print(msg: str) -> None:
    """Print debug message if debug mode enabled"""
    if DEBUG:
        print(f"DEBUG: {msg}", file=sys.stderr)


def error(msg: str) -> None:
    """Print error message"""
    print(colorize(f"Error: {msg}", Colors.RED), file=sys.stderr)


def warning(msg: str) -> None:
    """Print warning message"""
    print(colorize(f"Warning: {msg}", Colors.YELLOW), file=sys.stderr)


def info(msg: str) -> None:
    """Print info message"""
    print(colorize(msg, Colors.BLUE))


def success(msg: str) -> None:
    """Print success message"""
    print(colorize(msg, Colors.GREEN))


class Config:
    """Configuration management for tw.py"""
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = self._find_config()
        self.load()
        
    def _find_config(self) -> Optional[Path]:
        """Find configuration file in standard locations"""
        search_paths = [
            Path.home() / '.task' / 'tw.config',
            Path(__file__).parent / 'tw.config',
            Path('/etc/tw.config'),
        ]
        
        for path in search_paths:
            if path.exists():
                debug_print(f"Found config: {path}")
                return path
        
        debug_print("No config file found, using defaults")
        return None
    
    def load(self) -> None:
        """Load configuration from file"""
        if self.config_path:
            try:
                self.config.read(self.config_path)
            except Exception as e:
                warning(f"Could not read config file: {e}")
    
    def get(self, section: str, key: str, fallback=None):
        """Get configuration value"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getboolean(self, section: str, key: str, fallback=False):
        """Get boolean configuration value"""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback


class PathManager:
    """Manage paths for installation and execution"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Get paths from config or use defaults
        self.install_root = Path(
            config.get('paths', 'install_root', str(Path.home() / '.task'))
        ).expanduser()
        
        self.hooks_dir = Path(
            config.get('paths', 'hooks_dir', str(self.install_root / 'hooks'))
        ).expanduser()
        
        self.taskrc = Path(
            config.get('paths', 'taskrc', str(Path.home() / '.taskrc'))
        ).expanduser()
        
        # Registry and installers are relative to tw.py location
        tw_dir = Path(__file__).resolve().parent
        self.registry_dir = tw_dir / 'registry.d'
        self.installers_dir = tw_dir / 'installers'
        self.manifest_file = tw_dir / 'installed' / '.manifest'
        self.lib_dir = tw_dir / 'lib'
        
        # Ensure critical directories exist
        self.install_root.mkdir(parents=True, exist_ok=True)
        self.hooks_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        
        debug_print(f"Paths initialized: install_root={self.install_root}")


class TaskBinary:
    """Manage Taskwarrior binary location and execution"""
    
    def __init__(self, config: Config):
        self.config = config
        self.binary_path = self._find_task()
    
    def _find_task(self) -> Optional[str]:
        """Locate task binary"""
        # Check config first
        configured = self.config.get('paths', 'taskwarrior_bin', 'auto')
        
        if configured != 'auto':
            if os.path.isfile(configured) and os.access(configured, os.X_OK):
                debug_print(f"Using configured task: {configured}")
                return configured
            else:
                warning(f"Configured task binary not found: {configured}")
        
        # Search PATH
        path_env = os.environ.get('PATH', '')
        for path_dir in path_env.split(os.pathsep):
            task_path = os.path.join(path_dir, 'task')
            if os.path.isfile(task_path) and os.access(task_path, os.X_OK):
                debug_print(f"Found task in PATH: {task_path}")
                return task_path
        
        return None
    
    def get_version(self) -> Optional[str]:
        """Get Taskwarrior version"""
        if not self.binary_path:
            return None
        
        try:
            result = subprocess.run(
                [self.binary_path, '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse version (format: "2.6.2")
            return result.stdout.strip().split()[0]
        except Exception:
            return None


class Registry:
    """Manage registry of available applications"""
    
    def __init__(self, paths: PathManager):
        self.paths = paths
        self._apps = None
    
    def load_apps(self) -> Dict[str, Dict]:
        """Load all .meta files from registry"""
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
        """Parse a .meta file"""
        app = {}
        current_key = None
        current_value = []
        
        with open(meta_file, 'r') as f:
            for line in f:
                line = line.rstrip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Check if this is a continuation line (starts with whitespace)
                if line[0].isspace():
                    if current_key:
                        current_value.append(line.strip())
                    continue
                
                # Save previous key-value if exists
                if current_key:
                    app[current_key] = '\n'.join(current_value) if len(current_value) > 1 else current_value[0]
                
                # Parse new key-value
                if '=' in line:
                    key, value = line.split('=', 1)
                    current_key = key.strip()
                    current_value = [value.strip()]
        
        # Save last key-value
        if current_key:
            app[current_key] = '\n'.join(current_value) if len(current_value) > 1 else current_value[0]
        
        return app if 'name' in app else None
    
    def get_app(self, name: str) -> Optional[Dict]:
        """Get app metadata by name"""
        apps = self.load_apps()
        return apps.get(name)


class Manifest:
    """Manage installation manifest"""
    
    def __init__(self, paths: PathManager):
        self.paths = paths
        self._installed = None
    
    def load(self) -> Dict[str, Dict]:
        """Load installed apps from manifest"""
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
        """Save manifest to disk"""
        with open(self.paths.manifest_file, 'w') as f:
            f.write("# awesome-taskwarrior installation manifest\n")
            f.write("# Format: name|version|checksum|install_date|repo_url\n")
            f.write("#\n")
            
            for name, data in sorted(self._installed.items()):
                f.write(f"{name}|{data['version']}|{data['checksum']}|")
                f.write(f"{data['install_date']}|{data['repo_url']}\n")
    
    def add(self, name: str, version: str, checksum: str, repo_url: str) -> None:
        """Add app to manifest"""
        installed = self.load()
        installed[name] = {
            'version': version,
            'checksum': checksum,
            'install_date': datetime.now().isoformat(),
            'repo_url': repo_url
        }
        self.save()
    
    def remove(self, name: str) -> None:
        """Remove app from manifest"""
        installed = self.load()
        if name in installed:
            del installed[name]
            self.save()
    
    def is_installed(self, name: str) -> bool:
        """Check if app is installed"""
        return name in self.load()


class Installer:
    """Handle app installation, updates, and removal"""
    
    def __init__(self, paths: PathManager, registry: Registry, manifest: Manifest):
        self.paths = paths
        self.registry = registry
        self.manifest = manifest
    
    def install(self, name: str) -> bool:
        """Install an app"""
        app = self.registry.get_app(name)
        if not app:
            error(f"App not found in registry: {name}")
            return False
        
        if self.manifest.is_installed(name):
            warning(f"{name} is already installed")
            info("Use --update to update, or --remove then --install to reinstall")
            return False
        
        info(f"Installing {name}...")
        
        # Get installer script
        installer_script = self.paths.installers_dir / app['install_script']
        if not installer_script.exists():
            error(f"Installer script not found: {installer_script}")
            return False
        
        # Run installer
        if not self._run_installer(installer_script, 'install'):
            error(f"Installation failed for {name}")
            return False
        
        # Add to manifest
        self.manifest.add(
            name,
            app.get('version', 'unknown'),
            app.get('checksum', ''),
            app.get('repo', '')
        )
        
        success(f"✓ Installed {name}")
        return True
    
    def remove(self, name: str) -> bool:
        """Remove an app"""
        if not self.manifest.is_installed(name):
            error(f"{name} is not installed")
            return False
        
        app = self.registry.get_app(name)
        if not app:
            warning(f"{name} not in registry, attempting removal anyway")
        
        info(f"Removing {name}...")
        
        # Get installer script
        if app:
            installer_script = self.paths.installers_dir / app['install_script']
        else:
            # Try to guess installer name
            installer_script = self.paths.installers_dir / f"{name}.install"
        
        if installer_script.exists():
            if not self._run_installer(installer_script, 'uninstall'):
                error(f"Uninstallation failed for {name}")
                return False
        else:
            warning(f"Installer script not found, removing from manifest only")
        
        # Remove from manifest
        self.manifest.remove(name)
        
        success(f"✓ Removed {name}")
        return True
    
    def update(self, name: str) -> bool:
        """Update an app"""
        if not self.manifest.is_installed(name):
            error(f"{name} is not installed")
            return False
        
        app = self.registry.get_app(name)
        if not app:
            error(f"App not found in registry: {name}")
            return False
        
        info(f"Updating {name}...")
        
        installer_script = self.paths.installers_dir / app['install_script']
        if not installer_script.exists():
            error(f"Installer script not found: {installer_script}")
            return False
        
        # Try update function, fall back to reinstall
        if self._run_installer(installer_script, 'update', allow_fail=True):
            success(f"✓ Updated {name}")
        else:
            info("Update function not available, reinstalling...")
            if not self.remove(name) or not self.install(name):
                return False
        
        return True
    
    def _run_installer(self, script: Path, command: str, allow_fail: bool = False) -> bool:
        """Run installer script"""
        env = os.environ.copy()
        env['INSTALL_DIR'] = str(self.paths.install_root)
        env['HOOKS_DIR'] = str(self.paths.hooks_dir)
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
    """Handle listing and displaying apps"""
    
    def __init__(self, registry: Registry, manifest: Manifest):
        self.registry = registry
        self.manifest = manifest
    
    def list_all(self) -> None:
        """List all available apps"""
        apps = self.registry.load_apps()
        installed = self.manifest.load()
        
        if not apps:
            info("No apps available in registry")
            return
        
        # Group by type
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
        """List installed apps"""
        installed = self.manifest.load()
        
        if not installed:
            info("No apps installed")
            print("Use 'tw --list' to see available apps\n")
            return
        
        print(colorize("\nInstalled Extensions:\n", Colors.BOLD))
        
        for name, data in sorted(installed.items()):
            print(f"  {name:20} v{data['version']:10} {data['install_date']}")
        
        print()
    
    def show_info(self, name: str) -> None:
        """Show detailed info about an app"""
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
        
        print(f"Author:      {app.get('author', 'unknown')}")
        print(f"Repository:  {app.get('repo', 'unknown')}")
        
        if 'requires' in app:
            print(f"Requires:    {app['requires']}")
        
        if 'wrapper' in app and app['wrapper'] == 'yes':
            print(colorize("Wrapper:     Yes (can be used in wrapper chain)", Colors.BLUE))
        
        print()
        desc = app.get('long_desc', app.get('short_desc', 'No description available'))
        print(desc)
        print()


def handle_version(task_bin: TaskBinary) -> None:
    """Handle --version flag"""
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


def handle_list(lister: AppLister, installed_only: bool = False) -> None:
    """Handle --list and --list-installed flags"""
    if installed_only:
        lister.list_installed()
    else:
        lister.list_all()


def handle_info(lister: AppLister, app_name: str) -> None:
    """Handle --info flag"""
    lister.show_info(app_name)


def handle_install_taskwarrior(paths: PathManager) -> int:
    """Handle --install-taskwarrior flag"""
    installer_script = paths.installers_dir / 'taskwarrior.install'
    
    if not installer_script.exists():
        error("Taskwarrior installer not found")
        return 1
    
    info("Installing Taskwarrior 2.6.2...")
    
    env = os.environ.copy()
    env['INSTALL_DIR'] = str(paths.install_root)
    env['TW_BINDIR'] = str(Path.home() / 'bin')
    env['TW_DEBUG'] = '1' if DEBUG else '0'
    
    try:
        result = subprocess.run(
            ['bash', str(installer_script), 'install'],
            env=env
        )
        return result.returncode
    except Exception as e:
        error(f"Installation failed: {e}")
        return 1


def passthrough_to_task(task_bin: TaskBinary, args: List[str]) -> int:
    """Pass through command to task"""
    if not task_bin.binary_path:
        error("Taskwarrior not found in PATH")
        print("Install with: tw --install-taskwarrior")
        return 1
    
    cmd = [task_bin.binary_path] + args
    debug_print(f"Passthrough: {' '.join(cmd)}")
    
    try:
        os.execv(task_bin.binary_path, ['task'] + args)
    except OSError as e:
        error(f"Error executing task: {e}")
        return 1


def main():
    """Main entry point"""
    global DEBUG
    
    # Check for --debug flag early
    if '--debug' in sys.argv:
        DEBUG = True
        sys.argv.remove('--debug')
        debug_print("Debug mode enabled")
    
    # Initialize components
    config = Config()
    paths = PathManager(config)
    task_bin = TaskBinary(config)
    registry = Registry(paths)
    manifest = Manifest(paths)
    installer = Installer(paths, registry, manifest)
    lister = AppLister(registry, manifest)
    
    # Parse arguments
    if len(sys.argv) < 2:
        # No arguments, pass through to task
        return passthrough_to_task(task_bin, [])
    
    arg = sys.argv[1]
    
    # Handle our flags
    if arg == '--version':
        handle_version(task_bin)
        return 0
    
    elif arg == '--list':
        handle_list(lister, installed_only=False)
        return 0
    
    elif arg == '--list-installed':
        handle_list(lister, installed_only=True)
        return 0
    
    elif arg == '--info':
        if len(sys.argv) < 3:
            error("--info requires app name")
            return 1
        handle_info(lister, sys.argv[2])
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
    
    elif arg == '--install-taskwarrior':
        return handle_install_taskwarrior(paths)
    
    elif arg == '--help' or arg == '-h':
        print(f"""tw.py v{VERSION} - Taskwarrior wrapper and extension manager

USAGE:
    tw [OPTIONS] [TASK_COMMAND]

PACKAGE MANAGEMENT:
    --list                  List all available extensions
    --list-installed        List installed extensions
    --info <app>            Show detailed info about an app
    --install <app>         Install an extension
    --remove <app>          Remove an extension
    --update <app>          Update an extension
    --install-taskwarrior   Install Taskwarrior 2.6.2

INFORMATION:
    --version               Show version information
    --help, -h              Show this help message
    --debug                 Enable debug output

PASS-THROUGH:
    Any other arguments are passed directly to Taskwarrior.

EXAMPLES:
    tw --list               # Browse available extensions
    tw --install tw-recurrence
    tw next                 # Normal task command
    tw add "Buy milk" due:tomorrow

For more information, see README.md and DEVELOPERS.md
""")
        return 0
    
    else:
        # Pass through to task
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
