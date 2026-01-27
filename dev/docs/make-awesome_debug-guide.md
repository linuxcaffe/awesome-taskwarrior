# make-awesome.sh - User Guide

**Version:** 2.0.0  
**Purpose:** Multi-purpose project setup tool for awesome-taskwarrior extensions

## Overview

`make-awesome.sh` is a comprehensive tool for developing Taskwarrior extensions. It helps you:

- Generate installer packages for the awesome-taskwarrior registry (`--install`)
- Create debug-enabled versions of your Python code (`--debug`)
- Set up test suites for your projects (`--test`, coming soon)

## Installation

```bash
# Download from awesome-taskwarrior repository
curl -O https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/make-awesome.sh
chmod +x make-awesome.sh

# Or if you're already in the repo
cp /path/to/awesome-taskwarrior/make-awesome.sh .
```

## Basic Usage

```bash
./make-awesome.sh --install    # Generate package files
./make-awesome.sh --debug      # Create debug versions
./make-awesome.sh --test       # Generate test suite (not yet implemented)
./make-awesome.sh --help       # Show help
```

---

## Mode 1: Package Generation (`--install`)

Creates `.install` and `.meta` files for submitting your extension to the awesome-taskwarrior registry.

### When to Use

Use `--install` when you're ready to:
- Package your extension for distribution
- Submit a PR to awesome-taskwarrior
- Share your extension with the community

### Prerequisites

Your project directory should contain:
- **Hooks**: `on-add*.py`, `on-modify*.py`, `on-exit*.py`
- **Scripts**: Executable `.py` or `.sh` files (not hooks)
- **Configs**: `.rc` or `.conf` files
- **Docs**: `README.md`, `USAGE.md`, `INSTALL.md`

### Usage

```bash
cd /path/to/your-extension
./make-awesome.sh --install
```

The script will:
1. **Auto-detect** project information (name, version, files)
2. **Prompt you** for metadata (description, author, license, tags)
3. **Generate** two files:
   - `your-extension.meta` - Metadata file
   - `your-extension.install` - Self-contained installer script

### Example Session

```bash
$ ./make-awesome.sh --install

============================================================================
make-awesome.sh v2.0.0 --install
Generate installer and metadata for awesome-taskwarrior
============================================================================

[make] Detecting project information...
[make] ✓ Project: tw-recurrence
[make] ✓ Version: 2.1.0
[make] ✓ GitHub: https://github.com/yourusername/tw-recurrence

[make] Detecting project files...
[make] ✓ Hooks: on-modify-recurrence.py:hook
[make] ✓ Configs: recurrence.rc:config
[make] ✓ Docs: README.md:doc

[make] Gathering metadata...

App name [tw-recurrence]: 
Version [2.1.0]: 
Type: (1) hook, (2) script, (3) config, (4) theme
Select [1]: 1
Short description: Enhanced recurrence system with multi-iteration support
GitHub repo [yourusername/tw-recurrence]: 
Author [Your Name]: 
License [MIT]: 
Requires Taskwarrior version [2.6.0]: 2.6.2
Requires Python version (leave blank if N/A): 3.8

[make] Tags help users find your extension
Examples: hook, script, priority, recurrence, gtd, python, bash, stable, beta
Suggested tags for your extension:
  - hook python

Tags (comma-separated): hook,python,recurrence,stable

[make] Calculating SHA256 checksums...
[make] ✓ on-modify-recurrence.py: a1b2c3d4...
[make] ✓ recurrence.rc: e5f6g7h8...
[make] ✓ README.md: i9j0k1l2...

[make] Generating tw-recurrence.meta...
[make] ✓ Created tw-recurrence.meta

[make] Generating tw-recurrence.install...
[make] ✓ Created tw-recurrence.install

============================================================================
[make] ✓ Package created successfully!
============================================================================
```

### Generated Files

**`.meta` file** - Contains:
- Extension metadata (name, version, description)
- File manifest with checksums
- Requirements (Taskwarrior version, Python version)
- Tags for discoverability
- Author and license information

**`.install` file** - A self-contained Bash script that:
- Downloads all extension files from GitHub
- Places them in the correct directories
- Updates `.taskrc` if needed
- Tracks installation in manifest
- Supports both `install` and `remove` operations

### Next Steps After Generation

1. **Test the installer locally:**
   ```bash
   ./your-extension.install install
   ```

2. **Fork awesome-taskwarrior:**
   ```bash
   # Visit: https://github.com/linuxcaffe/awesome-taskwarrior/fork
   ```

3. **Add your files:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/awesome-taskwarrior.git
   cd awesome-taskwarrior
   cp /path/to/your-extension.meta registry.d/
   cp /path/to/your-extension.install installers/
   ```

4. **Create PR:**
   ```bash
   git add registry.d/your-extension.meta installers/your-extension.install
   git commit -m "Add your-extension v1.0.0"
   git push origin main
   # Then create PR on GitHub
   ```

---

## Mode 2: Debug Mode (`--debug`)

Creates debug-enabled versions of your Python files with comprehensive logging infrastructure.

### When to Use

Use `--debug` when you need to:
- Troubleshoot hook execution
- Trace data flow through your code
- Debug integration with Taskwarrior
- Profile performance issues

### How It Works

`make-awesome.sh --debug` scans your current directory for Python files and creates debug versions with the `debug.` prefix.

**Example:**
- `on-modify-agenda.py` → `debug.on-modify-agenda.py`
- `recurrence_helper.py` → `debug.recurrence_helper.py`

### Usage

```bash
cd /path/to/your-extension
./make-awesome.sh --debug
```

### What Gets Added

Each debug version includes:

1. **Dual Activation Modes:**
   ```python
   DEBUG_MODE = 0  # Set to 1 to enable debug output
   
   # Also checks TW_DEBUG environment variable
   tw_debug_level = os.environ.get('TW_DEBUG', '0')
   debug_active = DEBUG_MODE == 1 or tw_debug_level > 0
   ```

2. **Smart Log Directory Detection:**
   - **Dev Mode** (has `.git` directory): `./logs/debug/`
   - **Production Mode** (installed): `~/.task/logs/debug/`

3. **Session-Based Logging:**
   - Timestamped log files: `script_debug_20250125_143022.log`
   - Logs to both file and stderr (with color)
   - Automatic log rotation (keeps last 10 sessions)

4. **Debug Function:**
   ```python
   debug_log("Starting execution", level=1)
   debug_log("Processing task: " + task['uuid'], level=2)
   debug_log("Detailed state dump", level=3)
   ```

### Example Output

```bash
$ ./make-awesome.sh --debug

============================================================================
make-awesome.sh v2.0.0 --debug
Create debug versions of Python files
============================================================================

[make] Scanning for Python files in current directory...
[make] ✓ Found 2 Python file(s)

[make] Creating debug version: debug.on-modify-recurrence.py
[make] ✓ Created: debug.on-modify-recurrence.py

[make] Creating debug version: debug.recurrence_helper.py
[make] ✓ Created: debug.recurrence_helper.py

============================================================================
[make] ✓ Debug versions created!
============================================================================

[make] Debug files created in current directory with 'debug.' prefix
[make] To use:
  1. Set DEBUG_MODE=1 in the debug file, or
  2. Run with: tw --debug [command]

[make] Logs will be written to:
  • Dev mode (in project):    ./logs/debug/
  • Production mode:          ~/.task/logs/debug/
```

### Using Debug Versions

#### Method 1: Internal Toggle

Edit the debug file and change:
```python
DEBUG_MODE = 0  # Set to 1 to enable
```
to:
```python
DEBUG_MODE = 1  # Set to 1 to enable
```

Then symlink or copy the debug version to your hooks directory:
```bash
ln -sf $(pwd)/debug.on-modify-agenda.py ~/.task/hooks/on-modify-agenda.py
```

#### Method 2: With tw --debug

If you're using awesome-taskwarrior's `tw` wrapper:
```bash
tw --debug add "test task"
```

This sets `TW_DEBUG` environment variable which debug versions automatically detect.

### Smart Update Behavior

When you run `--debug` again:
- **Existing compatible debug files** (already have TW_DEBUG support) are preserved
- **Incompatible or missing debug files** are regenerated
- You won't lose manually added debug code if it's compatible

### Log File Example

```
======================================================================
Debug Session - 2025-01-25 14:30:22
Script: on-modify-recurrence.py
Debug Mode: 0
TW_DEBUG Level: 2
Session ID: 20250125_143022
======================================================================

14:30:22.145 [DEBUG-1] Debug logging initialized: ./logs/debug/on-modify-recurrence.py_debug_20250125_143022.log
14:30:22.156 [DEBUG-1] Starting recurrence hook execution
14:30:22.167 [DEBUG-2] Processing task UUID: a1b2c3d4-5678-90ef-ghij-klmnopqrstuv
14:30:22.178 [DEBUG-2] Task has recur field: daily
14:30:22.189 [DEBUG-3] Full task data: {'description': 'Test task', ...}
```

### Tips for Debug Development

1. **Start with level 1** for major operations
2. **Use level 2** for detailed flow
3. **Use level 3** for data dumps
4. **Add debug_log() calls** throughout your code
5. **Test with different TW_DEBUG levels**: `tw --debug=1`, `tw --debug=2`, `tw --debug=3`

---

## Mode 3: Test Mode (`--test`)

**Status:** Not yet implemented

This mode will generate starter test suites for your extensions once the test architecture is finalized.

### Planned Features

- Generate test directory structure
- Create TAP-compatible test files
- Set up isolated test environments
- Provide test templates for hooks and scripts

---

## Common Workflows

### Workflow 1: New Extension Development

```bash
# 1. Create your extension files
cd ~/projects/my-hook
vim on-modify-my-hook.py

# 2. Create debug version for development
./make-awesome.sh --debug

# 3. Develop using debug version
ln -sf $(pwd)/debug.on-modify-my-hook.py ~/.task/hooks/on-modify-my-hook.py
# Edit debug.on-modify-my-hook.py, set DEBUG_MODE=1

# 4. Test thoroughly
task add "test task"
# Check ./logs/debug/ for output

# 5. When ready to release, generate package
./make-awesome.sh --install

# 6. Test the installer
./my-hook.install install

# 7. Submit to awesome-taskwarrior
# (follow PR workflow above)
```

### Workflow 2: Debugging Existing Extension

```bash
# 1. Navigate to your installed extension source
cd ~/taskwarrior-extensions/tw-recurrence

# 2. Generate debug versions
./make-awesome.sh --debug

# 3. Replace production version temporarily
cp ~/.task/hooks/on-modify-recurrence.py ~/.task/hooks/on-modify-recurrence.py.backup
ln -sf $(pwd)/debug.on-modify-recurrence.py ~/.task/hooks/on-modify-recurrence.py

# 4. Enable debug in the file or use tw --debug
tw --debug=2 add "reproduce issue"

# 5. Check logs
ls -lt ./logs/debug/
cat ./logs/debug/on-modify-recurrence.py_debug_*.log

# 6. Fix issues, test, restore
rm ~/.task/hooks/on-modify-recurrence.py
mv ~/.task/hooks/on-modify-recurrence.py.backup ~/.task/hooks/on-modify-recurrence.py
```

### Workflow 3: Updating Extension Package

```bash
# 1. Update your code and version
vim on-modify-my-hook.py
vim VERSION  # Update version number

# 2. Regenerate package files
./make-awesome.sh --install

# 3. Test the new installer
./my-hook.install remove
./my-hook.install install

# 4. Update your fork and create PR
cd ~/awesome-taskwarrior
git pull upstream main
cp /path/to/my-hook.meta registry.d/
cp /path/to/my-hook.install installers/
git commit -am "Update my-hook to v1.1.0"
git push origin main
```

---

## Troubleshooting

### Issue: "No files detected"

**Problem:** Script can't find hooks, scripts, configs, or docs.

**Solution:**
- Ensure files have correct naming patterns:
  - Hooks: `on-add*.py`, `on-modify*.py`, `on-exit*.py`
  - Scripts: Executable `.py` or `.sh` files
  - Configs: `.rc` or `.conf` files
  - Docs: `README.md`, `USAGE.md`, `INSTALL.md`
- Make scripts executable: `chmod +x my-script.py`

### Issue: Debug logs not appearing

**Problem:** Running debug version but no logs are created.

**Solution:**
- Check that either `DEBUG_MODE=1` in the file OR `TW_DEBUG` is set
- Verify log directory exists and is writable
- Check stderr output for error messages
- Run directly to test: `./debug.on-modify-my-hook.py`

### Issue: Debug version overwrites custom code

**Problem:** Running `--debug` again removes your custom debug statements.

**Solution:**
- Make sure your debug file checks `TW_DEBUG` environment variable
- If compatible, the script will skip regeneration
- Consider keeping custom debug code in the original file instead

### Issue: Installer fails during download

**Problem:** Generated installer can't download files from GitHub.

**Solution:**
- Ensure files are committed and pushed to GitHub
- Check that `base_url` in `.meta` file is correct
- Test URL manually: `curl -I https://raw.githubusercontent.com/user/repo/main/file.py`
- Make sure branch is `main` (not `master`)

---

## File Naming Conventions

### Hooks
- Must start with `on-add`, `on-modify`, or `on-exit`
- Examples: `on-modify-agenda.py`, `on-add-tags.sh`

### Scripts
- Any executable file that's not a hook
- Examples: `task-report.py`, `backup-tasks.sh`

### Configs
- End with `.rc` or `.conf`
- Examples: `my-extension.rc`, `custom.conf`

### Docs
- `README.md`, `USAGE.md`, `INSTALL.md`
- Will be renamed to `{extension}_README.md` when installed

---

## Environment Variables

### TW_DEBUG

Set by `tw --debug` to indicate debug level (1-3).

**Usage:**
```bash
tw --debug=1  # Basic debug output
tw --debug=2  # Detailed debug output  
tw --debug=3  # Verbose debug output
```

Debug-enabled files automatically check this variable.

---

## Best Practices

### For Package Generation

1. **Test locally first** - Always test your installer before submitting
2. **Use semantic versioning** - Follow semver (1.0.0, 1.1.0, 2.0.0)
3. **Write good descriptions** - Help users understand what your extension does
4. **Tag appropriately** - Use relevant tags (hook, python, gtd, priority, etc.)
5. **Include documentation** - At minimum, include a README.md
6. **Calculate checksums** - The script does this automatically for verification

### For Debug Development

1. **Start with higher levels** - Use level 1 for key operations, level 3 for dumps
2. **Log context** - Include task UUIDs, operation types, etc.
3. **Test both modes** - Verify dev mode (in project) and production mode (installed)
4. **Clean up before release** - Remove debug versions from final package
5. **Use descriptive messages** - `debug_log("Processing task")` not `debug_log("here")`

### For Extension Development

1. **Follow Taskwarrior conventions** - Use standard hook names and patterns
2. **Handle errors gracefully** - Don't crash hooks on unexpected input
3. **Document dependencies** - List required Python packages, Taskwarrior versions
4. **Test edge cases** - Empty tasks, missing fields, concurrent modifications
5. **Respect user data** - Don't modify tasks unexpectedly

---

## Advanced Usage

### Custom Debug Locations

You can modify the `get_log_dir()` function in generated debug files:

```python
def get_log_dir():
    """Custom log directory logic"""
    # Force logs to specific directory
    log_dir = Path('/var/log/taskwarrior-debug')
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
```

### Adding Custom Debug Checks

After generation, you can add custom debug logic:

```python
# After the auto-generated debug infrastructure
if debug_active:
    debug_log("Custom startup check", 1)
    
    # Add performance tracking
    import time
    start_time = time.time()
    
    # ... your code ...
    
    elapsed = time.time() - start_time
    debug_log(f"Execution time: {elapsed:.3f}s", 2)
```

### Multi-File Projects

For projects with multiple Python files:

```bash
# Generate debug versions for all
./make-awesome.sh --debug

# Import debug_log from main file in helpers
# In debug.helper.py:
from debug.main_hook import debug_log
```

---

## Support and Contributing

### Getting Help

- **Issues:** https://github.com/linuxcaffe/awesome-taskwarrior/issues
- **Discussions:** https://github.com/linuxcaffe/awesome-taskwarrior/discussions
- **Taskwarrior Docs:** https://taskwarrior.org/docs/

### Contributing to make-awesome.sh

1. Fork the awesome-taskwarrior repository
2. Make your changes to `make-awesome.sh`
3. Test thoroughly with different project types
4. Submit a PR with clear description of changes

### Reporting Bugs

Include:
- make-awesome.sh version
- Command you ran
- Expected vs actual behavior
- Example project structure (file names, not contents)

---

## Version History

### 2.0.0 (2025-01-25)
- Renamed from `make-awesome-install.sh` to `make-awesome.sh`
- Added `--debug` mode for creating debug versions
- Added mode-based argument parsing
- Reserved `--test` for future test suite generation
- Improved help and usage documentation

### 1.0.0
- Initial release as `make-awesome-install.sh`
- Package generation for awesome-taskwarrior registry

---

## Quick Reference

```bash
# Package generation
./make-awesome.sh --install

# Debug development
./make-awesome.sh --debug

# Help
./make-awesome.sh --help

# Environment variable for debug
export TW_DEBUG=2
task add "test"

# Or use tw wrapper
tw --debug=2 add "test"
```

---

## License

This tool is part of the awesome-taskwarrior project and follows the same license as the repository.
