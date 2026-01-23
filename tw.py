#!/usr/bin/env python3
"""
tw.py - Taskwarrior Awesome Package Manager
Version: 2.0.0
Architecture: Curl-based coordination with per-file manifest tracking

This tool coordinates installation of Taskwarrior extensions but does NOT
control them. Each .install script must work standalone. tw.py adds:
- Manifest tracking for clean uninstalls
- Batch operations across multiple apps
- File integrity verification
- Convenient discovery of available apps

Key Principles:
1. Installers are independent - they work with OR without tw.py
2. tw.py coordinates - it does not control
3. Curl-based downloads - no git operations
4. Per-file manifest - track individual files, not repos
5. Direct placement - no symlinks by default
"""

import argparse
import hashlib
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PathManager:
    """Manages standard Taskwarrior directory structure."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize with base directory (defaults to ~/.task)."""
        self.base_dir = base_dir or Path.home() / ".task"
        self.hooks_dir = self.base_dir / "hooks"
        self.scripts_dir = self.base_dir / "scripts"
        self.config_dir = self.base_dir / "config"
        self.docs_dir = self.base_dir / "docs"
        self.logs_dir = self.base_dir / "logs"
        self.lib_dir = self.base_dir / "lib"
        self.manifest_file = self.base_dir / ".tw_manifest"
        
    def ensure_directories(self):
        """Create all standard directories if they don't exist."""
        for dir_path in [
            self.hooks_dir,
            self.scripts_dir,
            self.config_dir,
            self.docs_dir,
            self.logs_dir,
            self.lib_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_env_dict(self) -> Dict[str, str]:
        """Return environment variables for passing to installers."""
        return {
            "HOOKS_DIR": str(self.hooks_dir),
            "SCRIPTS_DIR": str(self.scripts_dir),
            "CONFIG_DIR": str(self.config_dir),
            "DOCS_DIR": str(self.docs_dir),
            "LOGS_DIR": str(self.logs_dir),
            "TASKRC": os.environ.get("TASKRC", str(Path.home() / ".taskrc")),
        }


class MetaFile:
    """Parser for .meta files that describe an application."""
    
    def __init__(self, meta_path: Path):
        """Initialize with path to .meta file."""
        self.meta_path = meta_path
        self.data = self._parse()
        
    def _parse(self) -> Dict[str, str]:
        """Parse .meta file into dictionary."""
        data = {}
        with open(self.meta_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    data[key.strip()] = value.strip()
        return data
    
    def get_name(self) -> str:
        """Get application name."""
        return self.data.get("name", "")
    
    def get_version(self) -> str:
        """Get application version."""
        return self.data.get("version", "unknown")
    
    def get_description(self) -> str:
        """Get application description."""
        return self.data.get("description", "")
    
    def get_requires(self) -> List[str]:
        """Get list of requirements."""
        requires = self.data.get("requires", "")
        return [r.strip() for r in requires.split(",") if r.strip()]
    
    def get_files(self) -> List[Tuple[str, str]]:
        """
        Get list of (filename, type) tuples from files= field.
        Format: files=file1.py:hook,file2:script,file3.rc:config
        Returns: [("file1.py", "hook"), ("file2", "script"), ("file3.rc", "config")]
        """
        files_str = self.data.get("files", "")
        if not files_str:
            return []
        
        files = []
        for item in files_str.split(","):
            item = item.strip()
            if ":" in item:
                filename, file_type = item.split(":", 1)
                files.append((filename.strip(), file_type.strip()))
        return files
    
    def get_base_url(self) -> str:
        """Get base URL for downloading files."""
        return self.data.get("base_url", "")
    
    def get_checksums(self) -> Dict[str, str]:
        """
        Get checksums dictionary from checksums= field.
        Format: checksums=sha256:abc123,sha256:def456
        Returns: {"file1.py": "abc123", "file2": "def456"}
        """
        checksums_str = self.data.get("checksums", "")
        if not checksums_str:
            return {}
        
        checksums = {}
        files = self.get_files()
        checksum_list = [c.strip() for c in checksums_str.split(",")]
        
        for i, (filename, _) in enumerate(files):
            if i < len(checksum_list):
                checksum = checksum_list[i]
                if checksum.startswith("sha256:"):
                    checksums[filename] = checksum[7:]  # Remove "sha256:" prefix
                else:
                    checksums[filename] = checksum
        
        return checksums


class Manifest:
    """Manages per-file installation manifest."""
    
    def __init__(self, manifest_path: Path):
        """Initialize with path to manifest file."""
        self.manifest_path = manifest_path
        self.entries = self._load()
    
    def _load(self) -> List[Dict[str, str]]:
        """Load manifest entries from file."""
        entries = []
        if not self.manifest_path.exists():
            return entries
        
        with open(self.manifest_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("|")
                if len(parts) >= 4:
                    entries.append({
                        "app": parts[0],
                        "version": parts[1],
                        "file": parts[2],
                        "checksum": parts[3] if len(parts) > 3 else "",
                        "date": parts[4] if len(parts) > 4 else "",
                    })
        return entries
    
    def _save(self):
        """Save manifest entries to file."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w") as f:
            for entry in self.entries:
                f.write(f"{entry['app']}|{entry['version']}|{entry['file']}|"
                       f"{entry['checksum']}|{entry['date']}\n")
    
    def add_file(self, app: str, version: str, filepath: str, checksum: str = ""):
        """Add a file to the manifest."""
        # Remove existing entry for this file if present
        self.entries = [e for e in self.entries if e["file"] != filepath]
        
        # Add new entry
        self.entries.append({
            "app": app,
            "version": version,
            "file": filepath,
            "checksum": checksum,
            "date": datetime.now().isoformat(),
        })
        self._save()
    
    def remove_app(self, app: str) -> List[str]:
        """
        Remove all files for an app from manifest.
        Returns list of filepaths that were tracked.
        """
        files = [e["file"] for e in self.entries if e["app"] == app]
        self.entries = [e for e in self.entries if e["app"] != app]
        self._save()
        return files
    
    def get_app_files(self, app: str) -> List[Dict[str, str]]:
        """Get all manifest entries for an app."""
        return [e for e in self.entries if e["app"] == app]
    
    def get_installed_apps(self) -> List[str]:
        """Get list of installed app names."""
        apps = set(e["app"] for e in self.entries)
        return sorted(apps)
    
    def is_installed(self, app: str) -> bool:
        """Check if an app is installed."""
        return any(e["app"] == app for e in self.entries)


class AwesomeTaskwarrior:
    """Main application class."""
    
    def __init__(self, args):
        """Initialize with parsed arguments."""
        self.args = args
        self.paths = PathManager()
        self.manifest = Manifest(self.paths.manifest_file)
        
        # Determine registry and installer directories
        script_dir = Path(__file__).parent.resolve()
        self.registry_dir = script_dir / "registry.d"
        self.installers_dir = script_dir / "installers"
    
    def _run_installer(self, installer_path: Path, command: str) -> bool:
        """Run an installer script with the specified command."""
        if not installer_path.exists():
            print(f"ERROR: Installer not found: {installer_path}", file=sys.stderr)
            return False
        
        # Prepare environment
        env = os.environ.copy()
        env.update(self.paths.get_env_dict())
        
        # Run installer
        try:
            result = subprocess.run(
                ["bash", str(installer_path), command],
                env=env,
                capture_output=True,
                text=True,
            )
            
            # Show output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"ERROR: Failed to run installer: {e}", file=sys.stderr)
            return False
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _find_installed_files(self, meta: MetaFile) -> List[Path]:
        """
        Find files that were installed for an app.
        Uses the files list from .meta and searches in appropriate directories.
        """
        files = []
        type_to_dir = {
            "hook": self.paths.hooks_dir,
            "script": self.paths.scripts_dir,
            "config": self.paths.config_dir,
            "doc": self.paths.docs_dir,
        }
        
        for filename, file_type in meta.get_files():
            target_dir = type_to_dir.get(file_type)
            if not target_dir:
                continue
            
            # For docs, check for renamed file (appname_README.md pattern)
            if file_type == "doc" and filename == "README.md":
                app_name = meta.get_name()
                renamed = target_dir / f"{app_name}_README.md"
                if renamed.exists():
                    files.append(renamed)
                    continue
            
            # Check for file in target directory
            filepath = target_dir / filename
            if filepath.exists():
                files.append(filepath)
        
        return files
    
    def cmd_install(self) -> int:
        """Install an application."""
        app_name = self.args.app
        
        # Check if already installed
        if self.manifest.is_installed(app_name):
            print(f"WARNING: {app_name} is already installed. Use --update to upgrade.")
            return 1
        
        # Find .meta file
        meta_path = self.registry_dir / f"{app_name}.meta"
        if not meta_path.exists():
            print(f"ERROR: Application not found in registry: {app_name}", file=sys.stderr)
            return 1
        
        # Parse .meta file
        meta = MetaFile(meta_path)
        
        # Find .install script
        installer_path = self.installers_dir / f"{app_name}.install"
        if not installer_path.exists():
            print(f"ERROR: Installer not found: {app_name}", file=sys.stderr)
            return 1
        
        # Ensure directories exist
        self.paths.ensure_directories()
        
        # Run installer
        print(f"Installing {app_name} v{meta.get_version()}...")
        if not self._run_installer(installer_path, "install"):
            print(f"ERROR: Installation failed for {app_name}", file=sys.stderr)
            return 1
        
        # Update manifest with installed files
        installed_files = self._find_installed_files(meta)
        checksums = meta.get_checksums()
        
        for filepath in installed_files:
            checksum = checksums.get(filepath.name, "")
            self.manifest.add_file(
                app_name,
                meta.get_version(),
                str(filepath),
                checksum
            )
        
        print(f"SUCCESS: Installed {app_name} v{meta.get_version()}")
        return 0
    
    def cmd_remove(self) -> int:
        """Remove an application."""
        app_name = self.args.app
        
        # Check if installed
        if not self.manifest.is_installed(app_name):
            print(f"WARNING: {app_name} is not installed.", file=sys.stderr)
            return 1
        
        # Find installer
        installer_path = self.installers_dir / f"{app_name}.install"
        if not installer_path.exists():
            print(f"WARNING: Installer not found: {app_name}", file=sys.stderr)
            print("Removing from manifest only...")
        else:
            # Run uninstall
            print(f"Uninstalling {app_name}...")
            if not self._run_installer(installer_path, "remove"):
                print(f"WARNING: Uninstall script failed for {app_name}", file=sys.stderr)
        
        # Remove from manifest
        removed_files = self.manifest.remove_app(app_name)
        
        print(f"SUCCESS: Removed {app_name} ({len(removed_files)} files)")
        return 0
    
    def cmd_update(self) -> int:
        """Update an application."""
        app_name = self.args.app
        
        # Check if installed
        if not self.manifest.is_installed(app_name):
            print(f"ERROR: {app_name} is not installed. Use --install first.", file=sys.stderr)
            return 1
        
        # Remove and reinstall
        print(f"Updating {app_name}...")
        
        # Store current namespace for remove
        remove_args = argparse.Namespace(app=app_name)
        original_args = self.args
        self.args = remove_args
        
        if self.cmd_remove() != 0:
            self.args = original_args
            return 1
        
        self.args = original_args
        return self.cmd_install()
    
    def cmd_info(self) -> int:
        """Show information about an application."""
        app_name = self.args.app
        
        # Find .meta file
        meta_path = self.registry_dir / f"{app_name}.meta"
        if not meta_path.exists():
            print(f"ERROR: Application not found in registry: {app_name}", file=sys.stderr)
            return 1
        
        # Parse .meta file
        meta = MetaFile(meta_path)
        
        # Show info
        print(f"Application: {meta.get_name()}")
        print(f"Version: {meta.get_version()}")
        print(f"Description: {meta.get_description()}")
        
        requires = meta.get_requires()
        if requires:
            print(f"Requirements: {', '.join(requires)}")
        
        files = meta.get_files()
        if files:
            print(f"Files ({len(files)}):")
            for filename, file_type in files:
                print(f"  - {filename} ({file_type})")
        
        # Show installation status
        if self.manifest.is_installed(app_name):
            entries = self.manifest.get_app_files(app_name)
            print(f"Status: Installed ({len(entries)} files)")
            if entries:
                print("Installed files:")
                for entry in entries:
                    print(f"  - {entry['file']}")
        else:
            print("Status: Not installed")
        
        return 0
    
    def cmd_list(self) -> int:
        """List available or installed applications."""
        if self.args.installed:
            # List installed apps
            installed = self.manifest.get_installed_apps()
            if not installed:
                print("No applications installed.")
                return 0
            
            print("Installed applications:")
            for app_name in installed:
                entries = self.manifest.get_app_files(app_name)
                version = entries[0]["version"] if entries else "unknown"
                print(f"  - {app_name} (v{version})")
            
            return 0
        
        # List available apps
        if not self.registry_dir.exists():
            print("No applications available in registry.")
            return 0
        
        meta_files = sorted(self.registry_dir.glob("*.meta"))
        if not meta_files:
            print("No applications available in registry.")
            return 0
        
        print("Available applications:")
        for meta_path in meta_files:
            meta = MetaFile(meta_path)
            installed = " [INSTALLED]" if self.manifest.is_installed(meta.get_name()) else ""
            print(f"  - {meta.get_name()} (v{meta.get_version()}){installed}")
            if meta.get_description():
                print(f"    {meta.get_description()}")
        
        return 0
    
    def cmd_verify(self) -> int:
        """Verify installed files against checksums."""
        app_name = self.args.app
        
        # Check if installed
        if not self.manifest.is_installed(app_name):
            print(f"ERROR: {app_name} is not installed.", file=sys.stderr)
            return 1
        
        # Get manifest entries
        entries = self.manifest.get_app_files(app_name)
        
        print(f"Verifying {app_name}...")
        all_ok = True
        
        for entry in entries:
            filepath = Path(entry["file"])
            stored_checksum = entry["checksum"]
            
            # Check file exists
            if not filepath.exists():
                print(f"  ✗ {filepath.name} - MISSING")
                all_ok = False
                continue
            
            # Check checksum if available
            if stored_checksum:
                actual_checksum = self._calculate_checksum(filepath)
                if actual_checksum == stored_checksum:
                    print(f"  ✓ {filepath.name} - OK")
                else:
                    print(f"  ✗ {filepath.name} - CHECKSUM MISMATCH")
                    all_ok = False
            else:
                print(f"  ? {filepath.name} - NO CHECKSUM")
        
        if all_ok:
            print(f"SUCCESS: All files verified for {app_name}")
            return 0
        else:
            print(f"WARNING: Verification failed for {app_name}", file=sys.stderr)
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Taskwarrior Awesome Package Manager v2.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install an application")
    install_parser.add_argument("app", help="Application name")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an application")
    remove_parser.add_argument("app", help="Application name")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update an application")
    update_parser.add_argument("app", help="Application name")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show application information")
    info_parser.add_argument("app", help="Application name")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List applications")
    list_parser.add_argument("--installed", action="store_true", help="List only installed apps")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify installed files")
    verify_parser.add_argument("app", help="Application name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create application instance
    app = AwesomeTaskwarrior(args)
    
    # Dispatch to command handler
    command_map = {
        "install": app.cmd_install,
        "remove": app.cmd_remove,
        "update": app.cmd_update,
        "info": app.cmd_info,
        "list": app.cmd_list,
        "verify": app.cmd_verify,
    }
    
    handler = command_map.get(args.command)
    if not handler:
        print(f"ERROR: Unknown command: {args.command}", file=sys.stderr)
        return 1
    
    return handler()


if __name__ == "__main__":
    sys.exit(main())
