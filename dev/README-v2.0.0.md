# awesome-taskwarrior v2.0.0 - Complete Architecture Overhaul

## What's Inside

This package contains the complete v2.0.0 architecture for awesome-taskwarrior with fundamental changes from git-based to curl-based installation.

### Package Contents

```
awesome-taskwarrior-v2.0.0/
├── CHANGES.txt                          # Complete changelog and architectural notes
├── MIGRATION.md                         # v1.3.0 → v2.0.0 migration guide
├── DEVELOPERS.md                        # Architecture and development guide
├── CONTRIBUTING.md                      # Contribution guidelines
├── tw.py                                # Main coordination tool (600 lines)
├── lib/
│   └── tw-common.sh                     # Utility library (384 lines)
├── dev/
│   ├── API.md                           # tw-common.sh API documentation
│   └── models/
│       ├── hook-template.install        # Hook installer template (334 lines)
│       ├── hook-template.meta           # Hook .meta template
│       ├── wrapper-template.install     # Wrapper installer template (363 lines)
│       └── wrapper-template.meta        # Wrapper .meta template
├── installers/
│   └── tw-recurrence.install            # Real-world example (273 lines)
└── registry.d/
    └── tw-recurrence.meta               # Example .meta file
```

## Quick Start

### Extract the Archive

```bash
tar -xzf awesome-taskwarrior-v2.0.0.tar.gz
cd awesome-taskwarrior-v2.0.0
```

### Test the Example Installer

```bash
# Test tw-recurrence installer standalone
bash installers/tw-recurrence.install install

# Test with tw.py coordination
./tw.py install tw-recurrence
./tw.py info tw-recurrence
./tw.py list --installed
./tw.py verify tw-recurrence
./tw.py remove tw-recurrence
```

## Key Changes from v1.3.0

### Installation Method
- **Before**: Git clone to subdirectories + symlink forests
- **After**: Curl downloads + direct file placement

### Directory Structure
- **Before**: `~/.task/hooks/recurrence/` (git repo with many files)
- **After**: `~/.task/hooks/on-add_recurrence.py` (single file)

### Installer Philosophy
- **Before**: Required tw-common.sh, tight coupling to tw.py
- **After**: Self-contained, optional helpers, works standalone

## Architecture Principles

### 1. Installer Independence
Every `.install` script MUST work standalone:
```bash
bash installers/myapp.install install  # No tw.py required
```

### 2. Optional tw-common.sh
Installers can optionally use helper functions:
```bash
if [[ -f ~/.task/lib/tw-common.sh ]]; then
    source ~/.task/lib/tw-common.sh
else
    # Fallback definitions
fi
```

### 3. Direct File Placement
No nested git repos, no symlink forests:
```
~/.task/
├── hooks/         # Direct files
├── scripts/       # Direct files
├── config/        # Direct files
└── docs/          # Direct files (new!)
```

### 4. Type-Based Routing
Files routed by type in .meta:
```ini
files=on-add_app.py:hook,app:script,app.rc:config,README.md:doc
```

### 5. Curl-Based Downloads
```bash
curl -fsSL "$BASE_URL/file.py" -o "$HOOKS_DIR/file.py"
```

## Documentation Overview

### For Users
- **MIGRATION.md**: Step-by-step upgrade from v1.3.0
- **tw.py --help**: Command-line interface

### For Developers
- **DEVELOPERS.md**: Complete architecture guide (675 lines)
  - Repository structure
  - Creating .meta files
  - Creating .install scripts
  - Testing procedures
  
- **API.md**: tw-common.sh utility reference (641 lines)
  - Messaging functions
  - Version checking
  - File operations
  - Config management
  - Testing helpers

- **CONTRIBUTING.md**: Contribution workflow (660 lines)
  - Quick start guide
  - .meta format specification
  - .install requirements
  - Testing checklist
  - Submission process

### Templates
- **dev/models/hook-template.install**: Full hook installer template
- **dev/models/wrapper-template.install**: Full wrapper installer template
- Both .meta templates with comprehensive comments

### Examples
- **installers/tw-recurrence.install**: Real-world implementation
- **registry.d/tw-recurrence.meta**: Real-world .meta file

## File Descriptions

### Core Files

#### tw.py (600 lines)
Main coordination tool that:
- Reads .meta files from registry
- Sets environment variables
- Runs installers
- Tracks installed files in manifest
- Provides install/remove/update/info/list/verify commands

**Key Classes:**
- `PathManager`: Manages ~/.task/ directory structure
- `MetaFile`: Parses .meta files
- `Manifest`: Tracks installed files (per-file, not per-app)
- `AwesomeTaskwarrior`: Main application logic

#### lib/tw-common.sh (384 lines)
Pure utility library providing:
- **Messaging**: tw_msg, tw_success, tw_warn, tw_error, tw_die, tw_debug
- **Version Checking**: tw_check_taskwarrior_version, tw_check_python_version
- **File Ops**: tw_curl_and_place, tw_ensure_executable, tw_backup_file
- **Config**: tw_add_config, tw_remove_config, tw_config_exists
- **Testing**: tw_init_test_env, tw_cleanup_test_env

### Documentation Files

#### DEVELOPERS.md (675 lines)
Complete developer guide covering:
- Architecture principles
- Repository structure for curl-friendly installation
- .meta file format specification
- .install script patterns
- Testing procedures
- Best practices
- Troubleshooting

#### API.md (641 lines)
Complete API reference for tw-common.sh:
- Every function documented with parameters, returns, examples
- Usage patterns and best practices
- Complete installer example
- Migration guide from v1.3.0 functions

#### CONTRIBUTING.md (660 lines)
Contribution guide including:
- Quick start workflow
- .meta field reference with examples
- .install requirements and patterns
- Testing checklist
- Submission process
- Code standards

#### MIGRATION.md
User and developer migration guide:
- What changed and why
- Step-by-step migration
- Breaking changes list
- Pattern comparisons (before/after)

### Template Files

#### dev/models/hook-template.install (334 lines)
Complete self-contained hook installer template showing:
- Configuration section
- Optional tw-common.sh sourcing with fallbacks
- Environment detection
- Requirements checking
- File downloading with graceful degradation
- Hook installation and configuration
- Complete removal logic
- Main dispatcher

#### dev/models/wrapper-template.install (363 lines)
Similar to hook template but for wrapper scripts:
- Script-specific installation (goes to ~/.task/scripts/)
- PATH checking and warnings
- Optional config file handling

#### Template .meta Files
Both hook-template.meta and wrapper-template.meta include:
- Complete field documentation
- Format specifications
- Usage examples
- Inline comments

### Example Files

#### installers/tw-recurrence.install (273 lines)
Real-world example demonstrating:
- Multiple hook files
- Symlink creation (on-add → on-modify)
- Config file installation
- README renaming
- Complete standalone operation

#### registry.d/tw-recurrence.meta
Real .meta file for tw-recurrence showing:
- Actual GitHub repository URL
- Multiple files with types
- Requirements specification
- Placeholder for checksums

## Testing the Architecture

### Standalone Installer Test

```bash
# Setup test environment
export HOOKS_DIR=/tmp/test-tw/hooks
export CONFIG_DIR=/tmp/test-tw/config
export DOCS_DIR=/tmp/test-tw/docs
export TASKRC=/tmp/test-tw/.taskrc

mkdir -p /tmp/test-tw/{hooks,config,docs}
touch /tmp/test-tw/.taskrc

# Test install
bash installers/tw-recurrence.install install

# Verify files
ls -la $HOOKS_DIR
ls -la $CONFIG_DIR
cat $TASKRC

# Test remove
bash installers/tw-recurrence.install remove

# Cleanup
rm -rf /tmp/test-tw
```

### Integration Test with tw.py

```bash
# Test tw.py commands
./tw.py list
./tw.py info tw-recurrence
./tw.py install tw-recurrence
./tw.py list --installed
./tw.py verify tw-recurrence
./tw.py remove tw-recurrence
```

## Implementation Statistics

| Component | Lines | Purpose |
|-----------|-------|---------|
| tw.py | 600 | Main coordination tool |
| tw-common.sh | 384 | Utility library |
| API.md | 641 | API documentation |
| DEVELOPERS.md | 675 | Development guide |
| CONTRIBUTING.md | 660 | Contribution guide |
| hook-template.install | 334 | Hook template |
| wrapper-template.install | 363 | Wrapper template |
| tw-recurrence.install | 273 | Real example |
| **Total Core** | **~3,900 lines** | Complete architecture |

## Key Features

### For Users
- ✅ Clean ~/.task/ structure (no nested git repos)
- ✅ Fast curl-based installation
- ✅ File integrity verification (checksums)
- ✅ Easy uninstall (tracks all files)
- ✅ Standalone installers (work without tw.py)

### For Developers
- ✅ Self-contained installer pattern
- ✅ Optional utility helpers
- ✅ Comprehensive templates
- ✅ Complete documentation
- ✅ Real-world examples
- ✅ Testing guidelines

## Future Enhancements

### Planned (not in v2.0.0)
- **make-awesome-installer.py**: Generator script for creating installers
  - Will use templates and API documentation
  - Generate checksums automatically
  - Create test stubs
  - Validate installer independence

### Potential Features
- Parallel downloads for multi-file apps
- Rollback capability
- Update notifications
- Remote registry support

## Compatibility

- **Taskwarrior**: v2.6.2 (unchanged from v1.3.0)
- **Bash**: 4.0+ (unchanged)
- **Python**: 3.6+ (unchanged)
- **New Requirement**: curl (for downloads)
- **Removed Requirement**: git (no longer needed)

## Getting Help

- Read **DEVELOPERS.md** for architecture details
- Read **API.md** for function reference
- Read **CONTRIBUTING.md** for contribution workflow
- Check **installers/tw-recurrence.install** for real example
- Use **dev/models/** templates as starting point

## Credits

- **Architecture Design**: @linuxcaffe (David)
- **Implementation**: Claude (Anthropic)
- **Based on**: Taskwarrior v2.6.2
- **Date**: January 2026

## License

See individual application repositories for their licenses. The awesome-taskwarrior infrastructure itself follows the licensing of the main repository.

---

**Note**: This is a complete architectural overhaul. All v1.3.0 installers must be rewritten to work with v2.0.0. See MIGRATION.md for details.
