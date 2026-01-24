#!/usr/bin/env python3
"""
tw.py - awesome-taskwarrior package manager and wrapper
Version: 2.0.0

A unified wrapper for Taskwarrior that provides:
- Transparent pass-through to task command
- Package management for Taskwarrior extensions (hooks, wrappers, configs)
- Hybrid mode: uses local files (dev) or GitHub (production)
- Per-file manifest tracking
- Checksum verification

Architecture Changes in v2.0.0:
- Removed git-based operations
- Direct file placement via curl
- Per-file manifest tracking (app|version|file|checksum|date)
- GitHub API integration for remote registry
- Self-contained installers that work with or without tw.py
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import hashlib
import shutil
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import tempfile
import glob

VERSION = "2.0.0"

# Enable colors (terminal supports ANSI codes)
USE_COLORS = True

def colorize(text, color_code):
    """Add ANSI color codes if terminal supports it"""
    if USE_COLORS:
        return f"\033[{color_code}m{text}\033[0m"
    return text

def green(text):
    """Green text"""
    return colorize(text, "32")

def yellow(text):
    """Yellow text"""
    return colorize(text, "33")

def gray(text):
    """Gray text"""
    return colorize(text, "90")

def blue(text):
    """Blue text"""
    return colorize(text, "34")

# GitHub configuration
GITHUB_REPO = "linuxcaffe/awesome-taskwarrior"
GITHUB_BRANCH = "main"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

class DebugLogger:
    """Manages debug output and logging"""
    
    def __init__(self, level=0, log_dir=None):
        self.level = level
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set up log directory
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".task" / "logs" / "debug"
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session log file
        if self.level > 0:
            self.log_file = self.log_dir / f"tw_debug_{self.session_id}.log"
            self._init_log()
            self._cleanup_old_logs()
        else:
            self.log_file = None
    
    def _init_log(self):
        """Initialize log file with header"""
        with open(self.log_file, 'w') as f:
            f.write(f"{'='*70}\n")
            f.write(f"tw.py Debug Session - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Debug Level: {self.level}\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"{'='*70}\n\n")
    
    def _cleanup_old_logs(self, keep_last=10):
        """Keep only the last N debug session logs"""
        if not self.log_dir.exists():
            return
        
        log_files = sorted(self.log_dir.glob("tw_debug_*.log"))
        
        # Remove older logs, keep last N
        if len(log_files) > keep_last:
            for old_log in log_files[:-keep_last]:
                try:
                    old_log.unlink()
                except:
                    pass
    
    def debug(self, message, context='', level=1):
        """Log debug message if current level >= required level"""
        if self.level < level:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if context:
            formatted = f"[debug] {timestamp} | {context:30s} | {message}"
        else:
            formatted = f"[debug] {timestamp} | {message}"
        
        # Print to stderr (colored)
        print(blue(formatted), file=sys.stderr)
        
        # Write to log file
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(formatted + '\n')
    
    def set_environment(self):
        """Set debug environment variables for subprocesses"""
        os.environ['TW_DEBUG'] = str(self.level)
        os.environ['TW_DEBUG_LEVEL'] = str(self.level)
        os.environ['DEBUG_HOOKS'] = '1' if self.level >= 2 else '0'
        
        if self.log_file:
            os.environ['TW_DEBUG_LOG'] = str(self.log_file.parent)
        
        self.debug(f"Environment variables set", "DebugLogger.set_environment")
        self.debug(f"  TW_DEBUG={self.level}", "", level=2)
        self.debug(f"  DEBUG_HOOKS={os.environ['DEBUG_HOOKS']}", "", level=2)
    
    def log_subprocess(self, cmd, context=''):
        """Log subprocess execution"""
        if self.level >= 2:
            cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
            self.debug(f"Executing: {cmd_str}", context, level=2)

# Global debug logger (initialized in main)
debug_logger = None

def debug(message, context='', level=1):
    """Convenience function for debug logging"""
    if debug_logger:
        debug_logger.debug(message, context, level)

class TagFilter:
    """Parse and apply tag filters (+tag includes, -tag excludes)"""
    
    def __init__(self, filter_args=None):
        self.include_tags = []  # +tag or tag (must have ALL)
        self.exclude_tags = []  # -tag (must have NONE)
        
        if filter_args:
            self._parse(filter_args)
    
    def _parse(self, filter_args):
        """Parse tag filter arguments
        
        Supports:
        - +tag (include)
        - -tag (exclude)
        - tag (include, no prefix)
        - Multiple tags: +hook +priority -deprecated
        """
        # Handle both string and list
        if isinstance(filter_args, str):
            tags = filter_args.split()
        else:
            tags = filter_args
        
        for tag in tags:
            tag = tag.strip()
            if not tag:
                continue
                
            if tag.startswith('+'):
                # Include tag
                self.include_tags.append(tag[1:].lower())
            elif tag.startswith('-'):
                # Exclude tag
                self.exclude_tags.append(tag[1:].lower())
            else:
                # No prefix = include
                self.include_tags.append(tag.lower())
        
        debug(f"Tag filter: include={self.include_tags}, exclude={self.exclude_tags}", 
              "TagFilter._parse", level=2)
    
    def matches(self, app_tags):
        """Check if app's tags match this filter
        
        Rules:
        - Must have ALL include tags (AND logic)
        - Must have NONE of the exclude tags
        - Empty filter matches everything
        """
        if not app_tags:
            app_tags = []
        
        # Normalize app tags to lowercase
        app_tag_set = set(tag.lower().strip() for tag in app_tags if tag.strip())
        
        # If no filters, match everything
        if not self.include_tags and not self.exclude_tags:
            return True
        
        # Must have ALL include tags (AND logic)
        if self.include_tags:
            if not all(tag in app_tag_set for tag in self.include_tags):
                return False
        
        # Must NOT have ANY exclude tags
        if self.exclude_tags:
            if any(tag in app_tag_set for tag in self.exclude_tags):
                return False
        
        return True
    
    def __str__(self):
        """String representation for display"""
        parts = []
        if self.include_tags:
            parts.extend([f"+{tag}" for tag in self.include_tags])
        if self.exclude_tags:
            parts.extend([f"-{tag}" for tag in self.exclude_tags])
        return " ".join(parts) if parts else "none"

class PathManager:
    """Manages all filesystem paths for awesome-taskwarrior"""
    
    def __init__(self):
        debug("Initializing PathManager", "PathManager.__init__")
        
        self.home = Path.home()
        self.task_dir = self.home / ".task"
        self.hooks_dir = self.task_dir / "hooks"
        self.scripts_dir = self.task_dir / "scripts"
        self.config_dir = self.task_dir / "config"
        self.docs_dir = self.task_dir / "docs"
        self.logs_dir = self.task_dir / "logs"
        self.taskrc = self.home / ".taskrc"
        self.manifest_file = self.config_dir / ".tw_manifest"  # Moved to config dir
        
        debug(f"task_dir: {self.task_dir}", "PathManager", level=2)
        debug(f"manifest: {self.manifest_file}", "PathManager", level=2)
        
        # Check if we're in a local repo (dev mode)
        self.tw_root = Path(__file__).parent.absolute()
        self.local_registry = self.tw_root / "registry.d"
        self.local_installers = self.tw_root / "installers"
        self.lib_dir = self.tw_root / "lib"
        
        # Determine mode: local (dev) or remote (production)
        self.is_dev_mode = self.local_registry.exists() and self.local_installers.exists()
        
        debug(f"is_dev_mode: {self.is_dev_mode}", "PathManager", level=2)
        
        # Only announce dev mode (production is normal/expected)
        if self.is_dev_mode:
            print("[tw] DEV mode: using local registry")
        
        # Check if ~/.task/scripts is in PATH
        self._check_path()
    
    def init_directories(self):
        """Create all required directories"""
        for dir_path in [
            self.hooks_dir, self.scripts_dir, self.config_dir,
            self.docs_dir, self.logs_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _check_path(self):
        """Check if ~/.task/scripts is in PATH and warn if not"""
        scripts_dir = str(self.scripts_dir)
        path_dirs = os.environ.get('PATH', '').split(':')
        
        if scripts_dir not in path_dirs:
            # Only warn if not running from the scripts dir itself
            # (i.e., if tw is elsewhere and scripts dir not in PATH)
            tw_path = Path(__file__).resolve()
            if tw_path.parent != self.scripts_dir:
                print(f"[tw] ⚠ Warning: {scripts_dir} is not in your PATH")
                print(f'[tw] Add it with: echo \'export PATH="$HOME/.task/scripts:$PATH"\' >> ~/.bashrc')
                print(f"[tw] Then run: source ~/.bashrc")
                print()

class MetaFile:
    """Parses and manages .meta files for applications"""
    
    def __init__(self, content):
        """Initialize with content string (from file or URL)"""
        self.data = {}
        self._parse(content)
    
    def _parse(self, content):
        """Parse the .meta file content"""
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                self.data[key.strip()] = value.strip()
    
    def get(self, key, default=None):
        """Get a value from the meta file"""
        return self.data.get(key, default)
    
    def get_tags(self):
        """Parse tags= field into list of tags
        
        Format: tags=hook,python,stable,advanced
        Returns: ['hook', 'python', 'stable', 'advanced']
        """
        tags_str = self.get('tags', '')
        if not tags_str:
            return []
        
        # Split by comma, strip whitespace, filter empty, lowercase
        tags = [tag.strip().lower() for tag in tags_str.split(',')]
        return [tag for tag in tags if tag]
    
    def get_files(self):
        """Parse files= field into list of (filename, type) tuples
        
        Format: files=file1.py:hook,file2.sh:script,config.rc:config
        Returns: [('file1.py', 'hook'), ('file2.sh', 'script'), ...]
        """
        files_str = self.get('files', '')
        if not files_str:
            return []
        
        result = []
        for item in files_str.split(','):
            item = item.strip()
            if ':' in item:
                filename, file_type = item.split(':', 1)
                result.append((filename.strip(), file_type.strip()))
            else:
                # Default to 'file' type if not specified
                result.append((item, 'file'))
        
        return result
    
    def get_base_url(self):
        """Get base URL for file downloads"""
        return self.get('base_url', '')
    
    def get_checksums(self):
        """Parse checksums= field into list of checksums
        
        Format: checksums=hash1,hash2,hash3
        Returns: ['hash1', 'hash2', 'hash3']
        """
        checksums_str = self.get('checksums', '')
        if not checksums_str:
            return []
        
        return [c.strip() for c in checksums_str.split(',') if c.strip()]

class RegistryManager:
    """Manages app registry - local or remote"""
    
    def __init__(self, paths):
        self.paths = paths
        self.is_dev_mode = paths.is_dev_mode
    
    def get_available_apps(self):
        """Get list of available app names"""
        if self.is_dev_mode:
            return self._get_local_apps()
        else:
            return self._get_remote_apps()
    
    def _get_local_apps(self):
        """Get apps from local registry.d/"""
        apps = []
        if self.paths.local_registry.exists():
            for meta_file in self.paths.local_registry.glob("*.meta"):
                app_name = meta_file.stem
                apps.append(app_name)
        return sorted(apps)
    
    def _get_remote_apps(self):
        """Get apps from GitHub registry.d/"""
        debug("Fetching apps from GitHub", "RegistryManager._get_remote_apps")
        
        try:
            url = f"{GITHUB_API_BASE}/contents/registry.d"
            debug(f"URL: {url}", "RegistryManager", level=2)
            
            req = Request(url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            response = urlopen(req)
            files = json.loads(response.read().decode('utf-8'))
            
            apps = []
            for file_info in files:
                if file_info['name'].endswith('.meta'):
                    app_name = file_info['name'].replace('.meta', '')
                    apps.append(app_name)
            
            debug(f"Found {len(apps)} apps", "RegistryManager", level=2)
            return sorted(apps)
        
        except (URLError, HTTPError) as e:
            debug(f"Failed to fetch: {e}", "RegistryManager._get_remote_apps")
            print(f"[tw] ✗ Failed to fetch registry from GitHub: {e}")
            return []
    
    def get_meta(self, app_name):
        """Get MetaFile object for an app"""
        if self.is_dev_mode:
            return self._get_local_meta(app_name)
        else:
            return self._get_remote_meta(app_name)
    
    def _get_local_meta(self, app_name):
        """Get meta from local file"""
        meta_path = self.paths.local_registry / f"{app_name}.meta"
        if not meta_path.exists():
            return None
        
        with open(meta_path, 'r') as f:
            content = f.read()
        
        return MetaFile(content)
    
    def _get_remote_meta(self, app_name):
        """Get meta from GitHub"""
        try:
            url = f"{GITHUB_RAW_BASE}/registry.d/{app_name}.meta"
            response = urlopen(url)
            content = response.read().decode('utf-8')
            return MetaFile(content)
        
        except (URLError, HTTPError) as e:
            print(f"[tw] ✗ Failed to fetch {app_name}.meta from GitHub: {e}")
            return None
    
    def get_installer_path(self, app_name):
        """Get path to installer (local or download from GitHub)"""
        if self.is_dev_mode:
            installer_path = self.paths.local_installers / f"{app_name}.install"
            if installer_path.exists():
                return str(installer_path)
            return None
        else:
            # Download from GitHub to temp file
            return self._download_installer(app_name)
    
    def _download_installer(self, app_name):
        """Download installer from GitHub to temp file"""
        try:
            url = f"{GITHUB_RAW_BASE}/installers/{app_name}.install"
            print(f"[tw] Downloading installer from GitHub...")
            
            response = urlopen(url)
            content = response.read().decode('utf-8')
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.install', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            os.chmod(temp_path, 0o755)
            return temp_path
        
        except (URLError, HTTPError) as e:
            print(f"[tw] ✗ Failed to download installer from GitHub: {e}")
            return None

class Manifest:
    """Manages the installation manifest"""
    
    def __init__(self, manifest_path):
        self.manifest_path = Path(manifest_path)
        self.entries = []
        self._load()
    
    def _load(self):
        """Load manifest from file"""
        if not self.manifest_path.exists():
            return
        
        with open(self.manifest_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 5:
                    self.entries.append({
                        'app': parts[0],
                        'version': parts[1],
                        'file': parts[2],
                        'checksum': parts[3],
                        'date': parts[4]
                    })
    
    def add(self, app, version, file_path, checksum=''):
        """Add an entry to the manifest"""
        # Remove any existing entry for this file
        self.entries = [e for e in self.entries 
                       if not (e['app'] == app and e['file'] == file_path)]
        
        # Add new entry
        entry = {
            'app': app,
            'version': version,
            'file': file_path,
            'checksum': checksum,
            'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        self.entries.append(entry)
        self._save()
    
    def remove_app(self, app):
        """Remove all entries for an app"""
        self.entries = [e for e in self.entries if e['app'] != app]
        self._save()
    
    def get_files(self, app):
        """Get list of files for an app"""
        return [e['file'] for e in self.entries if e['app'] == app]
    
    def get_apps(self):
        """Get list of installed apps with versions"""
        apps = {}
        for entry in self.entries:
            app = entry['app']
            if app not in apps:
                apps[app] = entry['version']
        return apps
    
    def is_installed(self, app):
        """Check if an app is installed"""
        return any(e['app'] == app for e in self.entries)
    
    def get_version(self, app):
        """Get installed version of an app"""
        for e in self.entries:
            if e['app'] == app:
                return e['version']
        return None
    
    def _save(self):
        """Save manifest to file"""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, 'w') as f:
            for entry in self.entries:
                line = '|'.join([
                    entry['app'],
                    entry['version'],
                    entry['file'],
                    entry['checksum'],
                    entry['date']
                ])
                f.write(line + '\n')

class AppManager:
    """Manages application installation, removal, and updates"""
    
    def __init__(self, paths, registry):
        self.paths = paths
        self.registry = registry
        self.manifest = Manifest(paths.manifest_file)
    
    def _install_tw_itself(self, dry_run=False):
        """Install/update tw.py itself to ~/.task/scripts/"""
        tw_script_path = self.paths.scripts_dir / "tw"
        tw_doc_path = self.paths.docs_dir / "tw_README.md"
        
        if dry_run:
            print(f"[tw] [DRY RUN] Would install tw.py to {tw_script_path}")
            return True
        
        print(f"[tw] Installing tw.py to ~/.task/scripts/...")
        
        try:
            # Download tw.py from GitHub
            url = f"{GITHUB_RAW_BASE}/tw.py"
            response = urlopen(url)
            tw_content = response.read().decode('utf-8')
            
            # Write to ~/.task/scripts/tw
            self.paths.scripts_dir.mkdir(parents=True, exist_ok=True)
            with open(tw_script_path, 'w') as f:
                f.write(tw_content)
            
            os.chmod(tw_script_path, 0o755)
            
            # Download README
            try:
                readme_url = f"{GITHUB_RAW_BASE}/README.md"
                readme_response = urlopen(readme_url)
                readme_content = readme_response.read().decode('utf-8')
                
                with open(tw_doc_path, 'w') as f:
                    f.write(readme_content)
                
                print(f"[tw] ✓ Documentation: {tw_doc_path}")
            except:
                pass  # README is optional
            
            # Add to manifest
            self.manifest.add("tw", VERSION, str(tw_script_path))
            if tw_doc_path.exists():
                self.manifest.add("tw", VERSION, str(tw_doc_path))
            
            print(f"[tw] ✓ Installed tw.py to {tw_script_path}")
            print(f"\n[tw] Make sure ~/.task/scripts is in your PATH:")
            print(f'[tw]   echo \'export PATH="$HOME/.task/scripts:$PATH"\' >> ~/.bashrc')
            print(f"[tw]   source ~/.bashrc")
            
            return True
            
        except Exception as e:
            print(f"[tw] ✗ Failed to install tw.py: {e}")
            return False
    
    def install(self, app_name, dry_run=False):
        """Install an application using its installer script"""
        debug(f"Installing {app_name} (dry_run={dry_run})", "AppManager.install")
        
        # Special case: installing tw.py itself
        if app_name == "tw":
            return self._install_tw_itself(dry_run)
        
        # Check if already installed
        if self.manifest.is_installed(app_name):
            installed_version = self.manifest.get_version(app_name)
            debug(f"{app_name} already installed (v{installed_version})", "AppManager.install", level=2)
            print(f"[tw] ℹ {app_name} v{installed_version} is already installed")
            print(f"[tw] Use --update {app_name} to reinstall/upgrade")
            return True
        
        # Get installer
        debug(f"Getting installer for {app_name}", "AppManager.install", level=2)
        installer_path = self.registry.get_installer_path(app_name)
        
        if not installer_path:
            debug(f"Installer not found for {app_name}", "AppManager.install")
            print(f"[tw] ✗ Installer not found: {app_name}")
            return False
        
        debug(f"Installer path: {installer_path}", "AppManager.install", level=2)
        
        # Set environment variables for the installer
        env = os.environ.copy()
        env.update({
            'INSTALL_DIR': str(self.paths.task_dir),
            'HOOKS_DIR': str(self.paths.hooks_dir),
            'SCRIPTS_DIR': str(self.paths.scripts_dir),
            'CONFIG_DIR': str(self.paths.config_dir),
            'DOCS_DIR': str(self.paths.docs_dir),
            'LOGS_DIR': str(self.paths.logs_dir),
            'TASKRC': str(self.paths.taskrc),
            'TW_COMMON': str(self.paths.lib_dir / 'tw-common.sh') if self.paths.is_dev_mode else ''
        })
        
        debug(f"Environment configured for installer", "AppManager.install", level=3)
        
        if dry_run:
            env['TW_DRY_RUN'] = '1'
            print(f"[tw] [DRY RUN] Would execute: {installer_path} install")
            return True
        
        try:
            print(f"[tw] Installing {app_name}...")
            
            if debug_logger and debug_logger.level >= 2:
                debug_logger.log_subprocess([installer_path, 'install'], "AppManager.install")
            
            result = subprocess.run(
                [installer_path, 'install'],
                env=env,
                check=False
            )
            
            debug(f"Installer exit code: {result.returncode}", "AppManager.install", level=2)
            
            # Clean up temp file if in production mode
            if not self.paths.is_dev_mode:
                try:
                    os.unlink(installer_path)
                    debug(f"Cleaned up temp installer", "AppManager.install", level=3)
                except:
                    pass
            
            if result.returncode == 0:
                # Reload manifest
                self.manifest = Manifest(self.paths.manifest_file)
                debug(f"Installation successful, manifest reloaded", "AppManager.install")
                print(f"[tw] ✓ Successfully installed {app_name}")
                return True
            else:
                debug(f"Installation failed", "AppManager.install")
                print(f"[tw] ✗ Installation failed (exit code {result.returncode})")
                return False
        
        except Exception as e:
            debug(f"Installation error: {e}", "AppManager.install")
            print(f"[tw] ✗ Installation error: {e}")
            if not self.paths.is_dev_mode:
                try:
                    os.unlink(installer_path)
                except:
                    pass
            return False
    
    def remove(self, app_name):
        """Remove an application"""
        debug(f"Removing {app_name}", "AppManager.remove")
        
        # Special case: removing tw.py itself
        if app_name == "tw":
            debug("Attempting to remove tw.py itself", "AppManager.remove", level=2)
            print(f"[tw] ⚠ Warning: This will remove tw.py itself!")
            print(f"[tw] You'll need to reinstall using the bootstrap script")
            print(f"[tw] Continue? (yes/no): ", end='')
            response = input().strip().lower()
            if response != "yes":
                debug("Removal cancelled by user", "AppManager.remove")
                print(f"[tw] Cancelled")
                return False
        
        if not self.manifest.is_installed(app_name):
            debug(f"{app_name} not installed", "AppManager.remove", level=2)
            print(f"[tw] ✗ Not installed: {app_name}")
            return False
        
        # Get installer
        debug(f"Getting installer for {app_name}", "AppManager.remove", level=2)
        installer_path = self.registry.get_installer_path(app_name)
        
        if installer_path:
            debug(f"Using installer: {installer_path}", "AppManager.remove", level=2)
            
            # Use installer's remove function
            env = os.environ.copy()
            env['TW_COMMON'] = str(self.paths.lib_dir / 'tw-common.sh') if self.paths.is_dev_mode else ''
            
            try:
                print(f"[tw] Removing {app_name}...")
                
                if debug_logger and debug_logger.level >= 2:
                    debug_logger.log_subprocess([installer_path, 'remove'], "AppManager.remove")
                
                result = subprocess.run(
                    [installer_path, 'remove'],
                    env=env,
                    check=False
                )
                
                debug(f"Installer exit code: {result.returncode}", "AppManager.remove", level=2)
                
                # Clean up temp file if in production mode
                if not self.paths.is_dev_mode:
                    try:
                        os.unlink(installer_path)
                        debug("Cleaned up temp installer", "AppManager.remove", level=3)
                    except:
                        pass
                
                if result.returncode == 0:
                    self.manifest = Manifest(self.paths.manifest_file)
                    debug("Removal successful, manifest reloaded", "AppManager.remove")
                    print(f"[tw] ✓ Successfully removed {app_name}")
                    return True
                else:
                    debug("Removal failed", "AppManager.remove")
                    print(f"[tw] ✗ Removal failed")
                    return False
            
            except Exception as e:
                print(f"[tw] ✗ Removal error: {e}")
                if not self.paths.is_dev_mode:
                    try:
                        os.unlink(installer_path)
                    except:
                        pass
                return False
        else:
            # Fallback: use manifest to remove files
            print(f"[tw] Installer not found, using manifest for removal")
            files = self.manifest.get_files(app_name)
            for file_path in files:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    print(f"[tw]   Removed: {file_path}")
            
            self.manifest.remove_app(app_name)
            print(f"[tw] ✓ Removed: {app_name}")
            return True
    
    def update(self, app_name):
        """Update an application (reinstall)"""
        debug(f"Updating {app_name}", "AppManager.update")
        
        # Special case: updating tw.py itself
        if app_name == "tw":
            print(f"[tw] Updating tw.py...")
            debug("Self-updating tw.py", "AppManager.update", level=2)
            return self._install_tw_itself(dry_run=False)
        
        print(f"[tw] Updating {app_name}...")
        if self.manifest.is_installed(app_name):
            debug(f"Removing existing installation", "AppManager.update", level=2)
            if not self.remove(app_name):
                debug("Update failed: removal failed", "AppManager.update")
                return False
        debug(f"Installing updated version", "AppManager.update", level=2)
        return self.install(app_name)
    
    def list_all_tags(self):
        """List all tags used across all applications"""
        debug("Listing all tags", "AppManager.list_all_tags")
        
        # Collect all tags with app counts
        tag_counts = {}
        tag_apps = {}  # tag -> [app names]
        
        for app_name in self.registry.get_available_apps():
            meta = self.registry.get_meta(app_name)
            if meta:
                tags = meta.get_tags()
                for tag in tags:
                    if tag not in tag_counts:
                        tag_counts[tag] = 0
                        tag_apps[tag] = []
                    tag_counts[tag] += 1
                    tag_apps[tag].append(app_name)
        
        if not tag_counts:
            print("\nNo tags found in registry")
            return
        
        print(f"\n{'='*70}")
        print(f"AVAILABLE TAGS ({len(tag_counts)} tags across {len(self.registry.get_available_apps())} applications)")
        print(f"{'='*70}\n")
        
        # Sort by count (descending), then alphabetically
        sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))
        
        for tag, count in sorted_tags:
            print(f"  {tag:<25} ({count} app{'s' if count != 1 else ''})")
        
        print(f"\nUse: tw --list +tag to filter by tag")
        print(f"     tw --list +tag1 +tag2 to require multiple tags")
        print(f"     tw --list +tag -exclude to include/exclude tags")
        print()
    
    def list_apps(self, tag_filter=None):
        """List all applications (installed and available) with status
        
        Args:
            tag_filter: TagFilter object or None
        """
        debug("Listing applications", "AppManager.list_apps")
        
        # Get all available apps from registry
        available_apps = self.registry.get_available_apps()
        
        if not available_apps:
            debug("No apps found in registry", "AppManager.list_apps")
            print("[tw] No applications found in registry")
            return
        
        # Apply tag filter if provided
        if tag_filter:
            debug(f"Applying tag filter: {tag_filter}", "AppManager.list_apps", level=2)
            filtered_apps = []
            for app_name in available_apps:
                meta = self.registry.get_meta(app_name)
                if meta:
                    app_tags = meta.get_tags()
                    if tag_filter.matches(app_tags):
                        filtered_apps.append(app_name)
            available_apps = filtered_apps
            debug(f"Filtered to {len(available_apps)} apps", "AppManager.list_apps", level=2)
        
        # Get installed apps
        installed_apps = self.manifest.get_apps()
        
        debug(f"Found {len(available_apps)} available, {len(installed_apps)} installed", 
              "AppManager.list_apps", level=2)
        
        # Count installed from filtered list
        installed_count = sum(1 for app in available_apps if self.manifest.is_installed(app))
        total_count = len(available_apps)
        
        print(f"\n{'='*70}")
        if tag_filter and str(tag_filter) != "none":
            print(f"APPLICATIONS ({installed_count} installed / {total_count} matching)")
            print(f"Filters: {tag_filter}")
        else:
            print(f"APPLICATIONS ({installed_count} installed / {total_count} available)")
        print(f"tw.py version {VERSION} | Colors: {'enabled' if USE_COLORS else 'disabled'}")
        print(f"{'='*70}\n")
        
        if not available_apps:
            print("No applications match the filter.")
            return
        
        for app_name in sorted(available_apps):
            meta = self.registry.get_meta(app_name)
            if not meta:
                continue
            
            # Check if installed
            is_installed = self.manifest.is_installed(app_name)
            installed_version = self.manifest.get_version(app_name) if is_installed else None
            
            # Get metadata
            registry_version = meta.get('version', 'unknown')
            desc = meta.get('description', 'No description')
            tags = meta.get_tags()
            
            # Format status
            if is_installed:
                # Green checkmark for installed
                status = green("✓")
                version_display = f"v{installed_version}"
                if installed_version != registry_version:
                    version_display += f" {yellow(f'(v{registry_version} available)')}"
            else:
                # Gray circle for not installed
                status = gray("○")
                version_display = gray(f"v{registry_version}")
            
            # Print app line with tags
            tag_display = f"[{', '.join(tags)}]" if tags else ""
            print(f"{status} {app_name:<40} {version_display}")
            
            # Print description and tags (indented, gray if not installed)
            if is_installed:
                print(f"    {desc}")
                if tag_display:
                    print(f"    {tag_display}")
            else:
                print(f"    {gray(desc)}")
                if tag_display:
                    print(f"    {gray(tag_display)}")
            print()
        
        print()
    
    def show_info(self, app_name):
        """Show information about an application"""
        meta = self.registry.get_meta(app_name)
        
        if not meta:
            print(f"[tw] ✗ Application not found: {app_name}")
            return False
        
        print(f"\n{'='*70}")
        print(f"APPLICATION: {app_name}")
        print(f"{'='*70}\n")
        
        print(f"Name:        {meta.get('name', 'N/A')}")
        print(f"Version:     {meta.get('version', 'N/A')}")
        print(f"Type:        {meta.get('type', 'N/A')}")
        print(f"Description: {meta.get('description', 'N/A')}")
        print(f"Repository:  {meta.get('repo', 'N/A')}")
        
        # Show additional metadata if present
        for key in ['author', 'license', 'requires_taskwarrior', 'requires_python']:
            value = meta.get(key)
            if value:
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        print()
        
        # Show files
        files = meta.get_files()
        if files:
            print(f"Files ({len(files)}):")
            for filename, file_type in files:
                print(f"  • {filename} ({file_type})")
            print()
        
        # Show installation status
        if self.manifest.is_installed(app_name):
            installed_version = self.manifest.get_version(app_name)
            print(f"Status:      ✓ Installed (v{installed_version})")
            
            # Show installed files
            installed_files = self.manifest.get_files(app_name)
            print(f"\nInstalled files ({len(installed_files)}):")
            for filepath in installed_files:
                exists = "✓" if Path(filepath).exists() else "✗"
                print(f"  {exists} {filepath}")
            
            # Show README location if it exists
            readme_path = self.paths.docs_dir / f"{app_name}_README.md"
            if readme_path.exists():
                print(f"\nDocumentation: {readme_path}")
        else:
            print(f"Status:      Not installed")
        
        print()
        return True
    
    def verify(self, app_name):
        """Verify checksums of installed files"""
        if not self.manifest.is_installed(app_name):
            print(f"[tw] ✗ Not installed: {app_name}")
            return False
        
        meta = self.registry.get_meta(app_name)
        if not meta:
            print(f"[tw] ⚠ Meta file not found for {app_name}")
            return False
        
        checksums = meta.get_checksums()
        files = meta.get_files()
        
        if not checksums:
            print(f"[tw] ⚠ No checksums available for {app_name}")
            return True
        
        print(f"[tw] Verifying {app_name}...")
        all_valid = True
        
        for i, (filename, file_type) in enumerate(files):
            if i >= len(checksums):
                break
            
            expected_checksum = checksums[i]
            if not expected_checksum:
                continue
            
            # Find file path
            target_dir = self._get_target_dir(file_type)
            file_path = target_dir / filename
            
            if not file_path.exists():
                print(f"[tw] ✗ File not found: {file_path}")
                all_valid = False
                continue
            
            # Calculate checksum
            actual_checksum = self._calculate_checksum(file_path)
            
            if actual_checksum == expected_checksum:
                print(f"[tw] ✓ {filename}")
            else:
                print(f"[tw] ✗ {filename} (checksum mismatch)")
                all_valid = False
        
        if all_valid:
            print(f"[tw] ✓ All files verified")
        else:
            print(f"[tw] ✗ Verification failed")
        
        return all_valid
    
    def _get_target_dir(self, file_type):
        """Get target directory for a file type"""
        type_map = {
            'hook': self.paths.hooks_dir,
            'script': self.paths.scripts_dir,
            'config': self.paths.config_dir,
            'doc': self.paths.docs_dir
        }
        return type_map.get(file_type, self.paths.task_dir)
    
    def _calculate_checksum(self, file_path):
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

def pass_through_to_task(args):
    """Pass command through to task"""
    try:
        # Find task executable
        task_bin = shutil.which('task')
        if not task_bin:
            print("[tw] ✗ task executable not found")
            return 1
        
        # Execute task with arguments
        # If debug level 3, enable taskwarrior's debug.hooks
        if debug_logger and debug_logger.level >= 3:
            debug("Enabling taskwarrior debug.hooks=2", "task_passthrough")
            args = ['rc.debug.hooks=2'] + args
        
        if debug_logger and debug_logger.level >= 2:
            debug_logger.log_subprocess([task_bin] + args, "task_passthrough")
        
        result = subprocess.run([task_bin] + args, check=False)
        
        debug(f"task exit code: {result.returncode}", "task_passthrough", level=2)
        return result.returncode
        
    except Exception as e:
        print(f"[tw] ✗ Error executing task: {e}")
        return 1

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='awesome-taskwarrior package manager and wrapper',
        add_help=False
    )
    
    # Package management commands
    parser.add_argument('--install', metavar='APP', help='Install an application')
    parser.add_argument('--remove', metavar='APP', help='Remove an application')
    parser.add_argument('--update', metavar='APP', help='Update an application')
    parser.add_argument('--list', action='store_true', help='List all applications (installed and available)')
    parser.add_argument('--info', metavar='APP', help='Show application info')
    parser.add_argument('--verify', metavar='APP', help='Verify application checksums')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Utility commands
    parser.add_argument('--version', action='store_true', help='Show tw.py version')
    parser.add_argument('--help', action='store_true', help='Show this help')
    parser.add_argument('--debug', nargs='?', const='1', metavar='LEVEL',
                       help='Enable debug output (1=basic, 2=detailed, 3=all+taskwarrior)')
    parser.add_argument('--tags', nargs='*', metavar='TAG',
                       help='Filter by tags (+include, -exclude, or list all if no args)')
    
    # Parse known args, let the rest pass through to task
    args, remaining = parser.parse_known_args()
    
    # Initialize debug logger if requested
    global debug_logger
    if args.debug:
        try:
            debug_level = int(args.debug)
        except ValueError:
            # Allow named modes: tw, hooks, task, all, verbose
            mode_map = {
                'tw': 1,
                'hooks': 2,
                'task': 3,
                'all': 3,
                'verbose': 3
            }
            debug_level = mode_map.get(args.debug.lower(), 1)
        
        debug_logger = DebugLogger(level=debug_level)
        debug_logger.set_environment()
        debug(f"Debug mode enabled (level {debug_level})", "main")
        debug(f"Log file: {debug_logger.log_file}", "main", level=2)
    
    # Handle tw.py commands
    if args.version:
        print(f"tw.py version {VERSION}")
        # Try to get taskwarrior version
        try:
            result = subprocess.run(['task', '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  check=False)
            if result.returncode == 0:
                tw_version = result.stdout.strip()
                print(f"taskwarrior {tw_version}")
        except:
            pass
        return 0
    
    if args.help:
        parser.print_help()
        print("\nFor Taskwarrior help: tw help")
        return 0
    
    # Initialize paths
    paths = PathManager()
    paths.init_directories()
    
    # Initialize registry
    registry = RegistryManager(paths)
    
    # Package management commands
    app_manager = AppManager(paths, registry)
    
    # Handle --tags command
    if args.tags is not None:
        if len(args.tags) == 0:
            # No arguments: list all tags
            app_manager.list_all_tags()
            return 0
        else:
            # Arguments provided: filter --list by tags
            tag_filter = TagFilter(args.tags)
            app_manager.list_apps(tag_filter)
            return 0
    
    if args.install:
        return 0 if app_manager.install(args.install, dry_run=args.dry_run) else 1
    
    if args.remove:
        return 0 if app_manager.remove(args.remove) else 1
    
    if args.update:
        return 0 if app_manager.update(args.update) else 1
    
    if args.list:
        # Check if we have tag arguments from remaining args
        # (e.g., tw --list +hook +python)
        tag_args = [arg for arg in remaining if arg.startswith('+') or arg.startswith('-')]
        if tag_args:
            tag_filter = TagFilter(tag_args)
            app_manager.list_apps(tag_filter)
        else:
            app_manager.list_apps()
        return 0
    
    if args.info:
        return 0 if app_manager.show_info(args.info) else 1
    
    if args.verify:
        return 0 if app_manager.verify(args.verify) else 1
    
    # If no tw.py commands, pass through to task
    if remaining or (not any(vars(args).values())):
        return pass_through_to_task(remaining if remaining else sys.argv[1:])
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
