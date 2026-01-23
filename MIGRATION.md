# Migrating from v1.3.0 to v2.0.0

## Overview

Version 2.0.0 represents a fundamental architectural shift in how awesome-taskwarrior installs and manages Taskwarrior extensions.

## What Changed

### Installation Method

- **v1.3.0**: Git clone to subdirectories + symlinks
- **v2.0.0**: Curl direct file placement

### Directory Structure

**v1.3.0:**
```
~/.task/
├── hooks/
│   └── recurrence/          # Git repo
│       ├── on-add.py
│       └── .git/
├── scripts/
│   └── nicedates/           # Git repo
```

**v2.0.0:**
```
~/.task/
├── hooks/
│   ├── on-add_recurrence.py # Direct file
│   └── on-modify_recurrence.py
├── scripts/
│   └── nicedates            # Direct file
├── config/
│   └── recurrence.rc
└── docs/
    └── recurrence_README.md
```

### Installer Independence

- **v1.3.0**: Installers required tw-common.sh functions
- **v2.0.0**: Installers are completely self-contained

### File Management

- **v1.3.0**: Symlink forests, git submodules
- **v2.0.0**: Direct file placement, no symlinks (except when needed within same directory)

## Why We Changed

### Problems with v1.3.0

1. **Nested git repos**: Cloning under ~/.task/ created nested repos
2. **Unnecessary files**: CHANGELOG, DEVELOPERS.md, .git/ cluttered ~/.task/
3. **Fragile symlinks**: Complex symlink management prone to breakage
4. **Tight coupling**: Installers depended on tw.py

### Benefits of v2.0.0

1. **Clean ~/.task/**: No git repos, only needed files
2. **Simple installation**: Direct file placement
3. **Independence**: Installers work standalone
4. **Maintainable**: Each installer self-contained
5. **Flexible**: tw.py adds convenience, not dependency

## Migration Steps

### For Users

1. **Backup your current setup:**

```bash
cp -r ~/.task ~/.task.backup.v1.3.0
cp ~/.taskrc ~/.taskrc.backup.v1.3.0
```

2. **Uninstall v1.3.0 apps:**

```bash
tw --remove tw-recurrence
tw --remove tw-nicedates
# etc for each app
```

3. **Update awesome-taskwarrior:**

```bash
cd ~/awesome-taskwarrior
git pull
# or download v2.0.0 release
```

4. **Reinstall apps with v2.0.0:**

```bash
tw --install tw-recurrence
tw --install tw-nicedates
```

### For Developers

#### Update Your .meta Files

**v1.3.0 format:**
```ini
name=tw-recurrence
version=1.0.0
description=Enhanced recurrence system
requires=python3
```

**v2.0.0 format:**
```ini
name=tw-recurrence
version=2.0.0
description=Enhanced recurrence system
requires=python3
files=on-add_recurrence.py:hook,on-modify_recurrence.py:hook,recurrence.rc:config,README.md:doc
base_url=https://raw.githubusercontent.com/user/repo/main/
checksums=sha256:abc123...,sha256:def456...
```

#### Update Your .install Scripts

**v1.3.0 pattern:**
```bash
install() {
    tw_clone_to_project hook recurrence "$REPO_URL" || return 1
    tw_symlink_hook "$INSTALL_DIR/recurrence" "on-add_recurrence.py" || return 1
    tw_add_config "include $CONFIG_DIR/recurrence/recurrence.rc"
}
```

**v2.0.0 pattern:**
```bash
install() {
    # Environment detection
    : ${HOOKS_DIR:=~/.task/hooks}
    : ${CONFIG_DIR:=~/.task/config}
    : ${DOCS_DIR:=~/.task/docs}
    
    # Download
    curl -fsSL "$BASE_URL/on-add_recurrence.py" -o "/tmp/on-add_recurrence.py" || return 1
    curl -fsSL "$BASE_URL/recurrence.rc" -o "/tmp/recurrence.rc" || return 1
    
    # Install
    mv "/tmp/on-add_recurrence.py" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/on-add_recurrence.py"
    mv "/tmp/recurrence.rc" "$CONFIG_DIR/"
    
    # Configure
    if ! grep -q "include.*recurrence.rc" ~/.taskrc; then
        echo "include $CONFIG_DIR/recurrence.rc" >> ~/.taskrc
    fi
}
```

#### Repository Structure

**Organize for curl-friendly installation:**
```
your-repo/
├── on-add_myapp.py      # Will go to ~/.task/hooks/
├── myapp                # Will go to ~/.task/scripts/
├── myapp.rc             # Will go to ~/.task/config/
├── README.md            # Will go to ~/.task/docs/ as myapp_README.md
├── myapp.meta           # For awesome-taskwarrior registry
├── myapp.install        # Self-contained installer
└── tests/               # Your test suite
```

## Breaking Changes

- **No SHORT_NAME variable**: Apps referenced by full name only
- **No git operations**: tw_clone_to_project() removed
- **No symlink helpers**: tw_symlink_hook() removed
- **Manifest format changed**: Now per-file tracking
- **Directory structure**: Files in root dirs, not subdirs

## Compatibility

- **Taskwarrior**: Still requires v2.6.2
- **Bash**: Still requires 4.0+
- **Python**: Still requires 3.6+
- **Existing hooks**: May need path updates if they reference subdirectories

## Questions?

See [DEVELOPERS.md](DEVELOPERS.md) for detailed v2.0.0 architecture documentation.

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to update your apps.
