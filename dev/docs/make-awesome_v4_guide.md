# make-awesome.py v4.0.0

## The Complete Development-to-Deployment Pipeline

### 🎯 Your Evil Plan, Implemented

```bash
# Single command does it ALL:
make-awesome.py "Added awesome feature X"

# Internally runs (each gated on previous success):
1. --debug    → Enhance with debug (tw --debug=2)
2. --test     → Run test suite [STUB - coming soon]
3. --install  → Generate .install and .meta files
4. --push     → Git commit/push + registry update
```

### 🚀 Quick Start

```bash
# Make it awesome
chmod +x make-awesome.py

# Run full pipeline
./make-awesome.py "Initial release"

# Or run individual stages
./make-awesome.py --debug      # Just debug
./make-awesome.py --install    # Just installer
./make-awesome.py --push "msg" # Just push
```

## The Four Stages

### Stage 1: --debug (Smart Enhancement)

**What it does:**
- Detects existing debug patterns in your code
- Enhances rather than replaces
- Keeps DEBUG values as-is (no reset to 0)
- Preserves path constants (CONFIG_DIR stays CONFIG_DIR)
- Keeps all imports together at top
- Adds tw --debug=2 support
- Adds file logging to ./logs/debug/ or ~/.task/logs/debug/

**Trigger level:** `tw --debug=2` (not debug=1)

**Example:**
```bash
./make-awesome.py --debug

# Output:
# ============================================================================
# make-awesome.py v4.0.0 --debug
# ============================================================================
# 
# Found 3 file(s)
# 
# Processing: on-add-need-priority.py
#   - Found: DEBUG = 1
#   - Found: debug_print()
#   - Found 2 path constants (preserving)
# Enhancing existing debug...
# ✓ Created: debug.on-add-need-priority.py
# 
# Processed 3 file(s)
# Triggered by: tw --debug=2
```

**Key Features:**
- ✅ Preserves DEBUG = 1 (doesn't reset to 0)
- ✅ Keeps CONFIG_DIR = "~/.task/config" (doesn't change to HOOK_DIR)
- ✅ All imports together (no 65-line splits)
- ✅ Wraps existing debug_print() with file logging
- ✅ Adds TW_DEBUG environment variable support
- ✅ Auto-detects dev vs production mode

### Stage 2: --test (Coming Soon)

**Status:** STUB - Test infrastructure planned

**Planned features:**
- Automatic test discovery
- TAP output compatibility
- Integration with `tw --test`
- Hook testing with mock task data
- Python and bash test support

**Current behavior:**
```bash
./make-awesome.py --test
# Outputs: "Test infrastructure not yet implemented"
# Returns: 0 (success, doesn't block pipeline)
```

### Stage 3: --install (Registry Generator)

**What it does:**
- Auto-detects project info (name, version, GitHub repo)
- Detects files (hooks, scripts, configs, docs)
- Prompts for metadata (description, tags, author, etc.)
- Calculates SHA256 checksums
- Generates `{project}.meta` file
- Generates `{project}.install` bash installer

**Example session:**
```bash
./make-awesome.py --install

# ============================================================================
# make-awesome.py v4.0.0 --install
# ============================================================================
# 
# Project: need-priority
# Version: 0.0.2
# GitHub: davidwneary/tw-need-priority
# 
# Detecting files...
#   Hook: on-add-need-priority.py
#   Hook: on-exit-need-priority.py
#   Hook: on-modify-need-priority.py
#   Script: nn
#   Config: need.rc
#   Doc: README.md
# 
# Gathering metadata...
# 
# App name [need-priority]: 
# Version [0.0.2]: 
# Type: (1) hook, (2) script, (3) config, (4) theme
# Select [1]: 1
# Description: Maslow's hierarchy of needs priority system
# GitHub repo [davidwneary/tw-need-priority]: 
# Author [David]: 
# License [MIT]: 
# Requires TW [2.6.0]: 2.6.2
# Requires Python (blank if N/A): 3.6
# 
# Tags (e.g., hook, script, python, bash, stable)
# Tags: hook,python,priority,needs,stable
# 
# Calculating checksums...
#   on-add-need-priority.py: a3f8b2c1d4e5...
#   on-exit-need-priority.py: 7f8e9d0c1b2a...
#   on-modify-need-priority.py: 3b4c5d6e7f8a...
#   nn: 9e0f1a2b3c4d...
#   need.rc: 5d6e7f8a9b0c...
#   README.md: 1a2b3c4d5e6f...
# 
# Generating need-priority.meta...
# ✓ Created need-priority.meta
# Generating need-priority.install...
# ✓ Created need-priority.install
# 
# ============================================================================
# ✓ Installation files generated!
# ============================================================================
```

**Generated files:**

`need-priority.meta`:
```ini
# need-priority.meta
# Maslow's hierarchy of needs priority system

name=need-priority
version=0.0.2
type=hook
description=Maslow's hierarchy of needs priority system
repo=https://github.com/davidwneary/tw-need-priority
base_url=https://raw.githubusercontent.com/davidwneary/tw-need-priority/main/
files=on-add-need-priority.py:hook,on-exit-need-priority.py:hook,on-modify-need-priority.py:hook,nn:script,need.rc:config,README.md:doc
tags=hook,python,priority,needs,stable

checksums=a3f8b2c1d4e5...,7f8e9d0c1b2a...,3b4c5d6e7f8a...,9e0f1a2b3c4d...,5d6e7f8a9b0c...,1a2b3c4d5e6f...

author=David
license=MIT
requires_taskwarrior=2.6.2
requires_python=3.6
```

`need-priority.install`:
Bash installer script with:
- TW_DEBUG support
- Curl downloads from GitHub
- Directory creation (~/.task/hooks, scripts, config, docs)
- .taskrc config inclusion
- Manifest tracking
- Remove/uninstall support

### Stage 4: --push (Git + Registry)

**What it does:**
- Checks git status (warns if dirty)
- `git add .`
- `git commit -m "message"`
- `git push`
- Copies .install to `~/dev/awesome-taskwarrior/installers/`
- Copies .meta to `~/dev/awesome-taskwarrior/registry.d/`
- Commits and pushes registry repo

**Safety checks:**
- ✅ Warns if working directory not clean
- ✅ Prompts for confirmation
- ✅ Verifies registry path exists
- ✅ Checks .install and .meta files exist
- ✅ Atomic operations (fails fast)

**Example:**
```bash
./make-awesome.py --push "Updated docs"

# ============================================================================
# make-awesome.py v4.0.0 --push
# ============================================================================
# 
# Git add...
# Commit: Updated docs
# Push...
# ✓ Git push complete
# 
# Copying to registry...
# ✓ Copied need-priority.install to installers/
# ✓ Copied need-priority.meta to registry.d/
# Updating registry...
# ✓ Registry updated
# 
# ============================================================================
# ✓ Push complete!
# ============================================================================
```

## Full Pipeline

### The Magic Command

```bash
make-awesome.py "Your commit message here"
```

This runs ALL four stages in sequence. If any stage fails, the pipeline stops.

**Example full run:**
```bash
./make-awesome.py "Initial release v1.0"

# ============================================================================
# make-awesome.py v4.0.0 - FULL PIPELINE
# Message: Initial release v1.0
# ============================================================================
# 
# STAGE 1/4: Debug
# ============================================================================
# [debug enhancement output...]
# ✓ Processed 3 file(s)
# 
# STAGE 2/4: Test
# ============================================================================
# ⚠ Test infrastructure not yet implemented
# 
# STAGE 3/4: Install
# ============================================================================
# [install generation - prompts for metadata...]
# ✓ Installation files generated!
# 
# STAGE 4/4: Push
# ============================================================================
# [git and registry push...]
# ✓ Push complete!
# 
# ============================================================================
# ✓ PIPELINE COMPLETE!
# ============================================================================
```

## Stage Independence

Each stage can be run independently:

```bash
# Just enhance debug
./make-awesome.py --debug

# Just generate installer (skips debug)
./make-awesome.py --install

# Just push (assumes .install/.meta exist)
./make-awesome.py --push "Updated feature"

# Combine multiple stages
./make-awesome.py --debug --install  # Not implemented yet
```

**Note:** Currently, stages must be run individually OR as full pipeline (with commit message). Combining specific stages (e.g., `--debug --install`) is not yet implemented.

## How It's "Evil" (Brilliant)

1. **Single Command Deployment** - One command takes you from code to published
2. **Gated Stages** - Each stage must succeed before next runs
3. **Smart, Not Dumb** - Analyzes code, doesn't just template
4. **Preserves Intent** - Keeps your DEBUG=1, your paths, your style
5. **Automated QA** - (When --test is implemented) catches bugs before push
6. **Registry Integration** - Automatically updates awesome-taskwarrior
7. **Fail-Fast** - Stops at first error, no half-done publishes

## Comparison with make-awesome.sh

| Feature | make-awesome.sh | make-awesome.py v4.0 |
|---------|----------------|----------------------|
| **Language** | Bash | Python |
| **Debug** | Template only | Smart pattern detection |
| **Install** | ✅ Full | ✅ Full |
| **Test** | ❌ Not present | 🚧 Stub (planned) |
| **Push** | ❌ Not present | ✅ Full |
| **Pipeline** | ❌ Manual steps | ✅ Automated |
| **Import handling** | ❌ Splits with 65 lines | ✅ Keeps together |
| **Path preservation** | ❌ Changes paths | ✅ Preserves |
| **DEBUG value** | ❌ Resets to 0 | ✅ Preserves |
| **Pattern detection** | ❌ None | ✅ Full analysis |

## Requirements

- Python 3.6+
- Git
- curl (for installers)
- Registry at `~/dev/awesome-taskwarrior` (for --push)

## Installation

```bash
# In your awesome-taskwarrior project
curl -o make-awesome.py https://example.com/make-awesome.py
chmod +x make-awesome.py
```

## Workflow Examples

### New Project Setup
```bash
# 1. Create your extension
vim on-add-my-hook.py

# 2. Add basic debug
# Add: DEBUG = 1 and debug_print() function

# 3. Run full pipeline
./make-awesome.py "Initial release"

# Done! Your extension is:
#   - Debug-enhanced
#   - Installer-ready
#   - Committed to git
#   - Published to registry
```

### Development Iteration
```bash
# 1. Make changes
vim on-add-my-hook.py

# 2. Debug locally
./make-awesome.py --debug
task add test +bug rc.debug=2  # Triggers debug logs

# 3. Check logs
cat ./logs/debug/on-add-my-hook_*.log

# 4. When ready, full push
./make-awesome.py "Fixed bug in priority handling"
```

### Registry Update Only
```bash
# Already have .install and .meta
# Just update registry

./make-awesome.py --push "Updated documentation"
```

## Debug Activation Methods

Your enhanced files support multiple debug triggers:

**Method 1: Manual (in file)**
```python
DEBUG = 1  # Enable always
```

**Method 2: Command line**
```bash
task add test rc.debug=2  # Triggers TW_DEBUG=2
```

**Method 3: Environment**
```bash
TW_DEBUG=2 task add test
```

**Method 4: Taskrc**
```ini
# In ~/.taskrc
debug=2
```

**Debug levels:**
- `debug=1` or `TW_DEBUG=1`: Normal task debug (not your code)
- `debug=2` or `TW_DEBUG=2`: **Triggers your debug code**

## Troubleshooting

### "No Python files found"
- Make sure you're in project directory
- Check files have `.py` extension or Python shebang
- Make files executable: `chmod +x my-script`

### "Already enhanced"
- Remove `debug.*` files to regenerate
- Or remove the marker from source file

### "Registry not found"
- Check `~/dev/awesome-taskwarrior` exists
- Clone it: `git clone git@github.com:user/awesome-taskwarrior.git ~/dev/`

### "Git working directory not clean"
- Commit or stash changes first
- Or answer 'y' to continue anyway (not recommended)

## Future Enhancements

- [ ] Combine stages: `--debug --install`
- [ ] Full test infrastructure with TAP
- [ ] Bash script enhancement
- [ ] Configurable registry location
- [ ] Dry-run mode
- [ ] Rollback capability
- [ ] Version bump automation

## The Evil Plan™ Is Complete

You now have a single tool that:
1. **Enhances** your code intelligently
2. **Tests** it thoroughly (coming soon)
3. **Packages** it professionally
4. **Publishes** it automatically

All with one command: `make-awesome.py "message"`

**This is not evil. This is engineering excellence.** 🎯

---

**Version:** 4.0.0  
**Author:** David (awesome-taskwarrior maintainer)  
**Status:** Production-ready (test stage stub)  
**License:** MIT
