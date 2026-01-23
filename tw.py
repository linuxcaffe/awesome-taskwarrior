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

# GitHub configuration
GITHUB_REPO = "linuxcaffe/awesome-taskwarrior"
GITHUB_BRANCH = "main"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

class PathManager:
    """Manages all filesystem paths for awesome-taskwarrior"""
    
    def __init__(self):
        self.home = Path.home()
        self.task_dir = self.home / ".task"
        self.hooks_dir = self.task_dir / "hooks"
        self.scripts_dir = self.task_dir / "scripts"
        self.config_dir = self.task_dir / "config"
        self.docs_dir = self.task_dir / "docs"
        self.logs_dir = self.task_dir / "logs"
        self.taskrc = self.home / ".taskrc"
        self.manifest_file = self.task_dir / ".tw_manifest"
        
        # Check if we're in a local repo (dev mode)
        self.tw_root = Path(__file__).parent.absolute()
        self.local_registry = self.tw_root / "registry.d"
        self.local_installers = self.tw_root / "installers"
        self.lib_dir = self.tw_root / "lib"
        
        # Determine mode: local (dev) or remote (production)
        self.is_dev_mode = self.local_registry.exists() and self.local_installers.exists()
        
        if self.is_dev_mode:
            print("[tw] Running in DEV mode (using local files)")
        else:
            print("[tw] Running in PRODUCTION mode (fetching from GitHub)")
    
    def init_directories(self):
        """Create all required directories"""
        for dir_path in [
            self.hooks_dir, self.scripts_dir, self.config_dir,
            self.docs_dir, self.logs_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

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
        try:
            url = f"{GITHUB_API_BASE}/contents/registry.d"
            req = Request(url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            response = urlopen(req)
            files = json.loads(response.read().decode('utf-8'))
            
            apps = []
            for file_info in files:
                if file_info['name'].endswith('.meta'):
                    app_name = file_info['name'].replace('.meta', '')
                    apps.append(app_name)
            
            return sorted(apps)
        
        except (URLError, HTTPError) as e:
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
    
    def install(self, app_name, dry_run=False):
        """Install an application using its installer script"""
        # Check if already installed
        if self.manifest.is_installed(app_name):
            installed_version = self.manifest.get_version(app_name)
            print(f"[tw] ℹ {app_name} v{installed_version} is already installed")
            print(f"[tw] Use --update {app_name} to reinstall/upgrade")
            return True
        
        # Get installer
        installer_path = self.registry.get_installer_path(app_name)
        
        if not installer_path:
            print(f"[tw] ✗ Installer not found: {app_name}")
            return False
        
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
        
        if dry_run:
            env['TW_DRY_RUN'] = '1'
            print(f"[tw] [DRY RUN] Would execute: {installer_path} install")
            return True
        
        try:
            print(f"[tw] Installing {app_name}...")
            result = subprocess.run(
                [installer_path, 'install'],
                env=env,
                check=False
            )
            
            # Clean up temp file if in production mode
            if not self.paths.is_dev_mode:
                try:
                    os.unlink(installer_path)
                except:
                    pass
            
            if result.returncode == 0:
                # Reload manifest
                self.manifest = Manifest(self.paths.manifest_file)
                print(f"[tw] ✓ Successfully installed {app_name}")
                return True
            else:
                print(f"[tw] ✗ Installation failed (exit code {result.returncode})")
                return False
        
        except Exception as e:
            print(f"[tw] ✗ Installation error: {e}")
            if not self.paths.is_dev_mode:
                try:
                    os.unlink(installer_path)
                except:
                    pass
            return False
    
    def remove(self, app_name):
        """Remove an application"""
        if not self.manifest.is_installed(app_name):
            print(f"[tw] ✗ Not installed: {app_name}")
            return False
        
        # Get installer
        installer_path = self.registry.get_installer_path(app_name)
        
        if installer_path:
            # Use installer's remove function
            env = os.environ.copy()
            env['TW_COMMON'] = str(self.paths.lib_dir / 'tw-common.sh') if self.paths.is_dev_mode else ''
            
            try:
                print(f"[tw] Removing {app_name}...")
                result = subprocess.run(
                    [installer_path, 'remove'],
                    env=env,
                    check=False
                )
                
                # Clean up temp file if in production mode
                if not self.paths.is_dev_mode:
                    try:
                        os.unlink(installer_path)
                    except:
                        pass
                
                if result.returncode == 0:
                    self.manifest = Manifest(self.paths.manifest_file)
                    print(f"[tw] ✓ Successfully removed {app_name}")
                    return True
                else:
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
        print(f"[tw] Updating {app_name}...")
        if self.manifest.is_installed(app_name):
            if not self.remove(app_name):
                return False
        return self.install(app_name)
    
    def list_apps(self):
        """List all applications (installed and available) with status"""
        # Get all available apps from registry
        available_apps = self.registry.get_available_apps()
        
        if not available_apps:
            print("[tw] No applications found in registry")
            return
        
        # Get installed apps
        installed_apps = self.manifest.get_apps()
        
        # Count
        installed_count = len(installed_apps)
        total_count = len(available_apps)
        
        print(f"\n{'='*70}")
        print(f"APPLICATIONS ({installed_count} installed / {total_count} available)")
        print(f"tw.py version {VERSION}")
        print(f"{'='*70}\n")
        
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
            
            # Print app line
            print(f"{status} {app_name:<40} {version_display}")
            
            # Print description (indented, gray if not installed)
            if is_installed:
                print(f"    {desc}")
            else:
                print(f"    {gray(desc)}")
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
        result = subprocess.run([task_bin] + args, check=False)
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
    
    # Parse known args, let the rest pass through to task
    args, remaining = parser.parse_known_args()
    
    # Handle tw.py commands
    if args.version:
        print(f"tw.py version {VERSION}")
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
    
    if args.install:
        return 0 if app_manager.install(args.install, dry_run=args.dry_run) else 1
    
    if args.remove:
        return 0 if app_manager.remove(args.remove) else 1
    
    if args.update:
        return 0 if app_manager.update(args.update) else 1
    
    if args.list:
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
