# Contributing to awesome-taskwarrior v2.0.0

Thank you for your interest in contributing to awesome-taskwarrior! This guide will help you create and submit applications that work with the v2.0.0 curl-based architecture.

## Table of Contents

- [Quick Start](#quick-start)
- [Repository Structure](#repository-structure)
- [Creating .meta Files](#creating-meta-files)
- [Creating .install Scripts](#creating-install-scripts)
- [Testing Your Contribution](#testing-your-contribution)
- [Submission Process](#submission-process)
- [Code Standards](#code-standards)

## Quick Start

### Prerequisites

- Bash 4.0+
- curl
- Taskwarrior 2.6.0+ (for testing)
- Git

### Development Workflow

1. **Create your Taskwarrior extension** in its own repository
2. **Create self-contained .install script** that works standalone
3. **Create .meta file** describing your application
4. **Test standalone** (without tw.py)
5. **Test with tw.py** (submit to awesome-taskwarrior)
6. **Submit pull request** with .meta and .install files

## Repository Structure

### Your Extension Repository

Organize your repository for curl-friendly installation:

```
your-extension-repo/
├── on-add_yourapp.py       # Hooks (if applicable)
├── on-modify_yourapp.py
├── yourapp                 # Scripts (if applicable)
├── yourapp.rc              # Config (if applicable)
├── README.md               # Documentation
├── yourapp.install         # Self-contained installer
├── yourapp.meta            # Metadata for registry
├── tests/                  # Your test suite
├── CHANGELOG.md
└── LICENSE
```

**Key Principles:**

- **Files to be installed go in repository root**
- **Name files with your app identifier** (e.g., `on-add_yourapp.py`)
- **Development files stay in repo** (tests, docs, etc. not installed)
- **README.md will be renamed** to `yourapp_README.md` when installed

### File Naming Conventions

| Type | Naming Pattern | Example |
|------|----------------|---------|
| Hook | `on-{event}_{appname}.py` | `on-add_recurrence.py` |
| Script | `{appname}` or `{appname}-{tool}` | `nicedates`, `taskopen-list` |
| Config | `{appname}.rc` | `recurrence.rc` |
| Doc | `README.md` (renamed on install) | → `recurrence_README.md` |

## Creating .meta Files

The `.meta` file describes your application for the awesome-taskwarrior registry.

### Format

```ini
# Required fields
name=yourapp
version=1.0.0
description=One-line description of what your app does

# Optional but recommended
requires=python3,taskwarrior>=2.6.0

# Files to install (filename:type,filename:type,...)
files=on-add_yourapp.py:hook,yourapp.rc:config,README.md:doc

# Base URL for raw file downloads
base_url=https://raw.githubusercontent.com/username/yourapp/main/

# Optional: File integrity checksums
checksums=sha256:abc123...,sha256:def456...,sha256:789xyz...
```

### Field Reference

#### name (required)

Application identifier used in commands:

```bash
tw.py install yourapp  # Uses this name
```

**Rules:**
- Lowercase letters, numbers, hyphens, underscores only
- Should match repository name convention
- Typically prefixed with `tw-` (e.g., `tw-recurrence`)

#### version (required)

Semantic version number:

```ini
version=1.0.0
version=2.1.3-beta
```

#### description (required)

One-line description shown in listings:

```ini
description=Enhanced recurrence system with chained and periodic modes
```

**Best practices:**
- Keep under 80 characters
- Describe what, not how
- Avoid marketing language

#### requires (optional)

Comma-separated list of dependencies:

```ini
requires=python3,taskwarrior>=2.6.0,jq
requires=bash>=4.0
```

**Supported formats:**
- `command` - Just command name
- `command>=version` - Minimum version
- `command==version` - Exact version

#### files (required)

Comma-separated list of `filename:type` pairs:

```ini
files=on-add_app.py:hook,on-modify_app.py:hook,app.rc:config,README.md:doc
```

**File types:**

| Type | Target Directory | Purpose |
|------|------------------|---------|
| `hook` | `~/.task/hooks/` | Taskwarrior hook scripts |
| `script` | `~/.task/scripts/` | Executable wrapper scripts |
| `config` | `~/.task/config/` | Configuration files |
| `doc` | `~/.task/docs/` | Documentation |

**Important:**
- Order matters (matches checksums order)
- Use actual filenames from repository
- README.md will be auto-renamed to `appname_README.md`

#### base_url (required)

Base URL for downloading files via curl:

```ini
# GitHub (most common)
base_url=https://raw.githubusercontent.com/username/repo/main/

# GitHub with subdirectory
base_url=https://raw.githubusercontent.com/username/repo/main/src/

# GitLab
base_url=https://gitlab.com/username/repo/-/raw/main/

# Bitbucket
base_url=https://bitbucket.org/username/repo/raw/main/
```

**Requirements:**
- Must be publicly accessible
- Must serve raw file content (not HTML)
- Should point to stable branch (main/master) or tagged release

#### checksums (optional but recommended)

SHA256 checksums for file integrity verification:

```ini
checksums=sha256:abc123...,sha256:def456...,sha256:789xyz...
```

**Generating checksums:**

```bash
# Generate for each file in order
sha256sum on-add_app.py on-modify_app.py app.rc README.md

# Format for .meta file (remove filenames, keep hashes)
# Add sha256: prefix to each, join with commas
```

**Helper script:**

```bash
#!/bin/bash
# generate-checksums.sh

files=(
    "on-add_yourapp.py"
    "on-modify_yourapp.py"
    "yourapp.rc"
    "README.md"
)

checksums=""
for file in "${files[@]}"; do
    sum=$(sha256sum "$file" | cut -d' ' -f1)
    if [[ -n "$checksums" ]]; then
        checksums+=","
    fi
    checksums+="sha256:$sum"
done

echo "checksums=$checksums"
```

### Complete Example

```ini
# tw-recurrence.meta
name=tw-recurrence
version=2.0.0
description=Enhanced recurrence system with chained and periodic modes
requires=python3>=3.6,taskwarrior>=2.6.2
files=on-add_recurrence.py:hook,on-modify_recurrence.py:hook,on-exit_recurrence.py:hook,recurrence.rc:config,README.md:doc
base_url=https://raw.githubusercontent.com/linuxcaffe/tw-recurrence_overhaul-hook/main/
checksums=
```

## Creating .install Scripts

The `.install` script is a self-contained bash script that handles installation and removal.

### Template

See `dev/models/hook-template.install` and `dev/models/wrapper-template.install` for full templates.

### Core Structure

```bash
#!/usr/bin/env bash
set -euo pipefail

# === CONFIGURATION ===
APP_NAME="yourapp"
APP_VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/yourapp/main"

# === OPTIONAL HELPER SOURCING ===
if [[ -f ~/.task/lib/tw-common.sh ]]; then
    source ~/.task/lib/tw-common.sh
else
    tw_msg() { echo "[INFO] $*"; }
    tw_error() { echo "[ERROR] $*" >&2; }
fi

# === ENVIRONMENT DETECTION ===
: ${HOOKS_DIR:=~/.task/hooks}
: ${CONFIG_DIR:=~/.task/config}
: ${DOCS_DIR:=~/.task/docs}
: ${TASKRC:=~/.taskrc}

# === INSTALL FUNCTION ===
install() {
    # Create directories
    mkdir -p "$HOOKS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
    
    # Download files
    curl -fsSL "$BASE_URL/file.py" -o "$HOOKS_DIR/file_$APP_NAME.py"
    
    # Make executable
    chmod +x "$HOOKS_DIR"/*.py
    
    # Configure
    echo "include $CONFIG_DIR/$APP_NAME.rc" >> "$TASKRC"
    
    return 0
}

# === REMOVE FUNCTION ===
remove() {
    # Remove files
    rm -f "$HOOKS_DIR/file_$APP_NAME.py"
    rm -f "$CONFIG_DIR/$APP_NAME.rc"
    
    # Remove config
    grep -Fxv "include $CONFIG_DIR/$APP_NAME.rc" "$TASKRC" > "$TASKRC.tmp"
    mv "$TASKRC.tmp" "$TASKRC"
    
    return 0
}

# === MAIN DISPATCHER ===
case "${1:-}" in
    install) install ;;
    remove|uninstall) remove ;;
    *) echo "Usage: $0 {install|remove}"; exit 1 ;;
esac
```

### Required Features

#### 1. Environment Detection

Always provide defaults:

```bash
: ${HOOKS_DIR:=~/.task/hooks}
: ${SCRIPTS_DIR:=~/.task/scripts}
: ${CONFIG_DIR:=~/.task/config}
: ${DOCS_DIR:=~/.task/docs}
: ${TASKRC:=~/.taskrc}
```

#### 2. Standalone Operation

Must work without tw.py or tw-common.sh:

```bash
# Check if helper available, else use fallback
if type tw_curl_and_place &>/dev/null; then
    tw_curl_and_place "$URL" "$DIR" "$FILE"
else
    curl -fsSL "$URL" -o "$DIR/$FILE"
fi
```

#### 3. Error Handling

Check return codes and fail gracefully:

```bash
curl -fsSL "$URL" -o "$FILE" || {
    echo "ERROR: Failed to download $URL" >&2
    return 1
}
```

#### 4. Idempotence

Safe to run multiple times:

```bash
# Check before adding to .taskrc
if ! grep -Fxq "$config_line" "$TASKRC"; then
    echo "$config_line" >> "$TASKRC"
fi
```

#### 5. Complete Cleanup

Remove everything in remove():

```bash
remove() {
    # Remove all installed files
    rm -f "$HOOKS_DIR/on-add_$APP_NAME.py"
    rm -f "$HOOKS_DIR/on-modify_$APP_NAME.py"
    rm -f "$CONFIG_DIR/$APP_NAME.rc"
    rm -f "$DOCS_DIR/${APP_NAME}_README.md"
    
    # Remove config entries
    grep -Fxv "include $CONFIG_DIR/$APP_NAME.rc" "$TASKRC" > "$TASKRC.tmp"
    mv "$TASKRC.tmp" "$TASKRC"
}
```

### Special Cases

#### Creating Symlinks

If hooks share the same file:

```bash
# Download main file
curl -fsSL "$BASE_URL/hook.py" -o "$HOOKS_DIR/on-modify_$APP_NAME.py"

# Create symlink for on-add
ln -sf "on-modify_$APP_NAME.py" "$HOOKS_DIR/on-add_$APP_NAME.py"

# Cleanup in remove()
rm -f "$HOOKS_DIR/on-add_$APP_NAME.py"  # Remove symlink
rm -f "$HOOKS_DIR/on-modify_$APP_NAME.py"  # Remove file
```

#### README Renaming

Avoid conflicts by renaming:

```bash
# Download with renamed filename
curl -fsSL "$BASE_URL/README.md" -o "$DOCS_DIR/${APP_NAME}_README.md"
```

#### Multiple Config Entries

Add multiple includes:

```bash
echo "include $CONFIG_DIR/$APP_NAME.rc" >> "$TASKRC"
echo "include $CONFIG_DIR/$APP_NAME-extra.rc" >> "$TASKRC"
```

## Testing Your Contribution

### 1. Standalone Testing

Test without tw.py first:

```bash
# Setup test environment
export HOOKS_DIR=/tmp/test-tw/hooks
export CONFIG_DIR=/tmp/test-tw/config
export DOCS_DIR=/tmp/test-tw/docs
export TASKRC=/tmp/test-tw/.taskrc

# Create structure
mkdir -p /tmp/test-tw/{hooks,config,docs}
touch /tmp/test-tw/.taskrc

# Test install
bash yourapp.install install

# Verify
echo "=== Installed Files ==="
ls -la $HOOKS_DIR
ls -la $CONFIG_DIR
ls -la $DOCS_DIR

echo "=== .taskrc Contents ==="
cat $TASKRC

# Test remove
bash yourapp.install remove

# Verify cleanup
ls -la $HOOKS_DIR $CONFIG_DIR $DOCS_DIR

# Cleanup
rm -rf /tmp/test-tw
```

### 2. Integration Testing with tw.py

After standalone tests pass:

```bash
# Clone awesome-taskwarrior
git clone https://github.com/linuxcaffe/awesome-taskwarrior.git
cd awesome-taskwarrior

# Add your files
cp /path/to/yourapp.meta registry.d/
cp /path/to/yourapp.install installers/

# Test with tw.py
./tw.py list
./tw.py info yourapp
./tw.py install yourapp

# Verify
./tw.py list --installed
ls -la ~/.task/hooks/ ~/.task/config/ ~/.task/docs/

# Test verification
./tw.py verify yourapp

# Test removal
./tw.py remove yourapp
```

### 3. Test Checklist

Before submitting, verify:

- [ ] Installer works standalone (no tw.py)
- [ ] Installer works without tw-common.sh
- [ ] All files download successfully
- [ ] Files placed in correct directories
- [ ] Hooks are executable (chmod +x)
- [ ] README renamed to `appname_README.md`
- [ ] .taskrc includes added correctly
- [ ] No duplicate .taskrc entries (idempotent)
- [ ] Remove function cleans up completely
- [ ] Remove function removes .taskrc includes
- [ ] Works with tw.py install/remove
- [ ] Manifest tracking accurate
- [ ] Checksums verify (if provided)

## Submission Process

### 1. Prepare Your Repository

Ensure your extension repository has:

- [ ] Files in repository root (not subdirectories)
- [ ] Clear README.md with usage instructions
- [ ] LICENSE file
- [ ] CHANGELOG.md
- [ ] Working .install script in repo
- [ ] .meta file in repo

### 2. Test Thoroughly

Complete all tests from [Testing](#testing-your-contribution) section.

### 3. Submit Pull Request

Submit to awesome-taskwarrior with:

**Files to include:**
- `registry.d/yourapp.meta`
- `installers/yourapp.install`

**PR Description should include:**

```markdown
## Application: yourapp

**Description:** Brief description of what your app does

**Repository:** https://github.com/username/yourapp

**Testing:**
- [x] Standalone installer tested
- [x] tw.py integration tested
- [x] Install/remove tested
- [x] Checksums verified (if applicable)

**Changes:**
- Add yourapp.meta to registry
- Add yourapp.install installer

**Dependencies:**
- python3 >= 3.6
- taskwarrior >= 2.6.0
```

### 4. Review Process

Maintainers will check:

1. **Installer independence** - Works standalone
2. **Code quality** - Follows bash best practices
3. **Documentation** - Clear .meta descriptions
4. **Testing** - Verification that it works
5. **Compatibility** - Works with v2.0.0 architecture

## Code Standards

### Bash Style

Follow these conventions:

```bash
# Use set -euo pipefail
set -euo pipefail

# Functions in lowercase with underscores
install_hooks() {
    # ...
}

# Constants in UPPERCASE
APP_NAME="myapp"
BASE_URL="https://..."

# Local variables
local file_path="/path/to/file"

# Check return codes
curl -fsSL "$URL" -o "$FILE" || return 1

# Quote variables
rm -f "$HOOKS_DIR/$APP_NAME.py"

# Use [[ ]] for conditionals
if [[ -f "$file" ]]; then
    # ...
fi
```

### Error Messages

Be specific and helpful:

```bash
# Good
tw_error "Failed to download on-add_myapp.py from $BASE_URL"

# Bad
tw_error "Download failed"
```

### Comments

Document non-obvious behavior:

```bash
# Create symlink because on-add and on-modify share same code
ln -sf "on-modify_$APP_NAME.py" "$HOOKS_DIR/on-add_$APP_NAME.py"
```

### Function Organization

Organize functions logically:

```bash
# 1. Configuration
APP_NAME="..."

# 2. Helper sourcing
if [[ -f ... ]]; then

# 3. Environment detection
: ${HOOKS_DIR:=...}

# 4. Helper functions
check_requirements() { }
download_files() { }

# 5. Main functions
install() { }
remove() { }

# 6. Dispatcher
case "${1:-}" in
```

## Getting Help

- **Documentation:** Read [DEVELOPERS.md](DEVELOPERS.md) and [API.md](dev/API.md)
- **Examples:** See `installers/tw-recurrence.install` for a real-world example
- **Templates:** Use `dev/models/hook-template.install` as starting point
- **Issues:** Open an issue on GitHub for questions
- **Discussion:** Join Taskwarrior community channels

## Additional Resources

- [Taskwarrior Docs](https://taskwarrior.org/docs/)
- [Hook API Documentation](https://taskwarrior.org/docs/hooks.html)
- [Bash Best Practices](https://mywiki.wooledge.org/BashGuide)

Thank you for contributing to awesome-taskwarrior!
