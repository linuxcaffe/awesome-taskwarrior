# CHANGES - Dev Mode Indicator

## Version 2.1.2 (2026-01-25)

### Added
- **Dev Mode Indicator**: Package management commands now display a clear indicator when running in dev mode
  - Shows: `[tw] DEV MODE - using local registry: <path>`
  - Appears for: --install, --remove, --update, --list, --info, --tags, --verify
  - Only shown in dev mode (when registry.d/ and installers/ exist locally)
  - Production mode shows clean output with no indicator
  - Helps developers immediately know which registry source is being used

### Benefits
- **Immediate Feedback**: Developers can instantly see they're using local files vs GitHub
- **Prevents Confusion**: No more wondering "am I testing my local changes or pulling from GitHub?"
- **Clean Production**: Normal users see no extra output
- **Path Transparency**: Shows exact local registry path being used

### Technical Details
- Dev mode detected by PathManager checking for local registry.d/ and installers/ directories
- `show_dev_mode_if_needed()` function added to main() scope
- Called once per package management command before execution
- Zero impact on pass-through to task command
- No changes to non-package-management commands (--version, --help, --shell)

### Example Output

**In Dev Mode:**
```
$ tw --list
[tw] DEV MODE - using local registry: /home/djp/awesome-taskwarrior/registry.d
[tw] Installed applications:
[tw]   tw-recurrence (v1.0.0)
```

**In Production Mode:**
```
$ tw --list
[tw] Installed applications:
[tw]   tw-recurrence (v1.0.0)
```

## Version 2.1.1 (2026-01-25)

### Fixed
- Unicode symbol corruption → ASCII equivalents
  - ✓ → `[+]` (success/checkmark)
  - ✗ → `[X]` (error/cross)  
  - ⚠ → `[!]` (warning)
  - → → `->` (arrow)
- Added PathManager.registry_dir property for compatibility
- Fixed formatting: added newline before def update()

### Changed
- tw.py: 11 unicode replacements
- tw-common.sh: 3 unicode replacements
