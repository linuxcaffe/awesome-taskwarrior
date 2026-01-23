#!/usr/bin/env python3
"""
tw.py - awesome-taskwarrior package manager and wrapper
Version: 2.0.0

A unified wrapper for Taskwarrior that provides:
- Transparent pass-through to task command
- Package management for Taskwarrior extensions (hooks, wrappers, configs)
- Curl-based installation (no git clones)
- Per-file manifest tracking
- Checksum verification

Architecture Changes in v2.0.0:
- Removed git-based operations
- Direct file placement via curl
- Per-file manifest tracking (app|version|file|checksum|date)
- Added docs_dir for README files
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

VERSION = "2.0.0"

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
        
        # awesome-taskwarrior directories
        self.tw_root = Path(__file__).parent.absolute()
        self.registry_dir = self.tw_root / "registry.d"
        self.installers_dir = self.tw_root / "installers"
        self.lib_dir = self.tw_root / "lib"
        self.installed_dir = self.tw_root / "installed"
        self.manifest_file = self.task_dir / ".tw_manifest"
        
    def init_directories(self):
        """Create all required directories"""
        for dir_path in [
            self.hooks_dir, self.scripts_dir, self.config_dir,
            self.docs_dir, self.logs_dir, self.registry_dir,
            self.installers_dir, self.installed_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

class MetaFile:
    """Parses and manages .meta files for applications"""
    
    def __init__(self, meta_path):
        self.meta_path = Path(meta_path)
        self.data = {}
        self._parse()
    
    def _parse(self):
        """Parse the .meta file"""
        if not self.meta_path.exists():
            return
        
        with open(self.meta_path, 'r') as f:
            for line in f:
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
    
    def __init__(self, paths):
        self.paths = paths
        self.manifest = Manifest(paths.manifest_file)
    
    def install(self, app_name, dry_run=False):
        """Install an application using its installer script"""
        installer_path = self.paths.installers_dir / f"{app_name}.install"
        
        if not installer_path.exists():
            print(f"[tw] ✗ Installer not found: {installer_path}")
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
            'TW_COMMON': str(self.paths.lib_dir / 'tw-common.sh')
        })
        
        if dry_run:
            env['TW_DRY_RUN'] = '1'
            print(f"[tw] DRY RUN: Would execute: bash {installer_path} install")
            
            # Show what would be installed
            meta_path = self.paths.registry_dir / f"{app_name}.meta"
            if meta_path.exists():
                meta = MetaFile(meta_path)
                files = meta.get_files()
                if files:
                    print(f"[tw] Would install {len(files)} file(s):")
                    for filename, file_type in files:
                        target_dir = self._get_target_dir(file_type)
                        print(f"[tw]   {filename} → {target_dir}/")
            return True
        
        # Execute installer
        try:
            result = subprocess.run(
                ['bash', str(installer_path), 'install'],
                env=env,
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[tw] ✓ Installed: {app_name}")
                return True
            else:
                print(f"[tw] ✗ Installation failed: {app_name}")
                return False
                
        except Exception as e:
            print(f"[tw] ✗ Error running installer: {e}")
            return False
    
    def remove(self, app_name):
        """Remove an application using its installer script"""
        if not self.manifest.is_installed(app_name):
            print(f"[tw] ⚠ Not installed: {app_name}")
            return False
        
        installer_path = self.paths.installers_dir / f"{app_name}.install"
        
        if installer_path.exists():
            # Use installer's remove function
            env = os.environ.copy()
            env.update({
                'INSTALL_DIR': str(self.paths.task_dir),
                'HOOKS_DIR': str(self.paths.hooks_dir),
                'SCRIPTS_DIR': str(self.paths.scripts_dir),
                'CONFIG_DIR': str(self.paths.config_dir),
                'DOCS_DIR': str(self.paths.docs_dir),
                'LOGS_DIR': str(self.paths.logs_dir),
                'TASKRC': str(self.paths.taskrc),
                'TW_COMMON': str(self.paths.lib_dir / 'tw-common.sh')
            })
            
            try:
                result = subprocess.run(
                    ['bash', str(installer_path), 'remove'],
                    env=env,
                    capture_output=False
                )
                
                if result.returncode == 0:
                    self.manifest.remove_app(app_name)
                    print(f"[tw] ✓ Removed: {app_name}")
                    return True
                else:
                    print(f"[tw] ✗ Removal failed: {app_name}")
                    return False
                    
            except Exception as e:
                print(f"[tw] ✗ Error running installer: {e}")
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
            self.remove(app_name)
        return self.install(app_name)
    
    def list_installed(self):
        """List all installed applications"""
        apps = {}
        for entry in self.manifest.entries:
            app = entry['app']
            if app not in apps:
                apps[app] = entry['version']
        
        if not apps:
            print("[tw] No applications installed")
            return
        
        print("[tw] Installed applications:")
        for app, version in sorted(apps.items()):
            print(f"[tw]   {app} (v{version})")
    
    def show_info(self, app_name):
        """Show information about an application"""
        meta_path = self.paths.registry_dir / f"{app_name}.meta"
        
        if not meta_path.exists():
            print(f"[tw] ✗ Application not found: {app_name}")
            return False
        
        meta = MetaFile(meta_path)
        
        print(f"[tw] Application: {app_name}")
        print(f"[tw]   Name: {meta.get('name', 'N/A')}")
        print(f"[tw]   Version: {meta.get('version', 'N/A')}")
        print(f"[tw]   Type: {meta.get('type', 'N/A')}")
        print(f"[tw]   Description: {meta.get('description', 'N/A')}")
        print(f"[tw]   Repository: {meta.get('repo', 'N/A')}")
        print(f"[tw]   Base URL: {meta.get('base_url', 'N/A')}")
        
        # Show files
        files = meta.get_files()
        if files:
            print(f"[tw]   Files ({len(files)}):")
            for filename, file_type in files:
                print(f"[tw]     {filename} ({file_type})")
        
        # Show installation status
        if self.manifest.is_installed(app_name):
            installed_version = self.manifest.get_version(app_name)
            print(f"[tw]   Status: Installed (v{installed_version})")
            
            # Show README location if it exists
            readme_path = self.paths.docs_dir / f"{app_name}_README.md"
            if readme_path.exists():
                print(f"[tw]   README: {readme_path}")
        else:
            print(f"[tw]   Status: Not installed")
        
        return True
    
    def verify(self, app_name):
        """Verify checksums of installed files"""
        if not self.manifest.is_installed(app_name):
            print(f"[tw] ✗ Not installed: {app_name}")
            return False
        
        meta_path = self.paths.registry_dir / f"{app_name}.meta"
        if not meta_path.exists():
            print(f"[tw] ⚠ Meta file not found: {meta_path}")
            return False
        
        meta = MetaFile(meta_path)
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
    parser.add_argument('--list', action='store_true', help='List installed applications')
    parser.add_argument('--info', metavar='APP', help='Show application info')
    parser.add_argument('--verify', metavar='APP', help='Verify application checksums')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Utility commands
    parser.add_argument('--version', action='store_true', help='Show tw.py version')
    parser.add_argument('--help', action='store_true', help='Show this help')
    
    # Parse known args, let the rest pass through to task
    args, remaining = parser.parse_known_args()
    
    # Initialize paths
    paths = PathManager()
    paths.init_directories()
    
    # Handle tw.py commands
    if args.version:
        print(f"tw.py version {VERSION}")
        return 0
    
    if args.help:
        parser.print_help()
        print("\nFor Taskwarrior help: tw help")
        return 0
    
    # Package management commands
    app_manager = AppManager(paths)
    
    if args.install:
        return 0 if app_manager.install(args.install, dry_run=args.dry_run) else 1
    
    if args.remove:
        return 0 if app_manager.remove(args.remove) else 1
    
    if args.update:
        return 0 if app_manager.update(args.update) else 1
    
    if args.list:
        app_manager.list_installed()
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
