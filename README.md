# awesome-taskwarrior

A package manager and registry for Taskwarrior extensions (hooks, scripts, and configurations).

## Features

✅ **Registry-based** - Like npm, PyPI, or cargo  
✅ **Self-installing** - One command bootstrap  
✅ **Self-updating** - `tw --update tw` keeps it current  
✅ **Self-contained** - Everything in `~/.task/`  
✅ **GitHub integration** - Fetches from GitHub on-demand  
✅ **Clean installs** - Manifest tracking for easy removal  
✅ **Developer friendly** - Local dev mode for testing  

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/install.sh | bash
```

This will:
1. Install tw.py to `~/.task/scripts/tw`
2. Add `~/.task/scripts` to your PATH
3. Set up documentation in `~/.task/docs/`

## Usage

### Browse Extensions
```bash
tw --list
```

### Install an Extension
```bash
tw --install tw-recurrence
```

### Update an Extension
```bash
tw --update tw-recurrence
```

### Remove an Extension
```bash
tw --remove tw-recurrence
```

### Show Extension Info
```bash
tw --info tw-recurrence
```

### Update tw.py Itself
```bash
tw --update tw
```

### Verify Checksums
```bash
tw --verify tw-recurrence
```

### Check Version
```bash
tw --version
```

### Debug Mode
```bash
tw --debug <command>           # Basic debug (level 1)
tw --debug=2 <command>         # Detailed debug
tw --debug=3 <command>         # Full debug + taskwarrior hooks

# Examples:
tw --debug --list
tw --debug=2 --install tw-recurrence
tw --debug=3 task next

# Check logs:
ls ~/.task/logs/debug/
cat ~/.task/logs/debug/tw_debug_*.log
```

**Debug levels:**
- **1**: Basic operations (default)
- **2**: Detailed + file operations
- **3**: Everything + taskwarrior debug.hooks

**Debug output:**
- Color-coded to stderr
- Logged to `~/.task/logs/debug/`
- Separate logs for tw.py and each extension

## How It Works

awesome-taskwarrior is a **registry** that points to extension repositories:

```
┌─────────────────────────────────────────┐
│  awesome-taskwarrior (Registry)         │
│  ├── tw.py (package manager)            │
│  ├── registry.d/*.meta (metadata)       │
│  └── installers/*.install (installers)  │
└─────────────────────────────────────────┘
             ↓ points to
┌─────────────────────────────────────────┐
│  Extension Repos (tw-recurrence, etc)   │
│  ├── hooks, scripts, configs            │
│  └── documentation                      │
└─────────────────────────────────────────┘
```

When you install an extension:
1. tw.py fetches the installer from awesome-taskwarrior
2. Installer downloads files from the extension's repo
3. Files installed to `~/.task/`
4. Manifest tracks installation in `~/.task/config/.tw_manifest`

## Directory Structure

After installation:
```
~/.task/
├── config/
│   ├── .tw_manifest           # Installation tracking
│   └── recurrence.rc          # Extension configs
├── scripts/
│   ├── tw                     # The package manager
│   └── rr                     # Extension scripts
├── hooks/
│   ├── on-add_recurrence.py   # Extension hooks
│   └── on-exit_recurrence.py
└── docs/
    ├── tw_README.md           # tw.py docs
    └── recurrence_README.md   # Extension docs
```

## Available Extensions

Run `tw --list` to see all available extensions, or browse:
- [tw-recurrence](https://github.com/linuxcaffe/tw-recurrence_overhaul-hook) - Advanced recurrence with chained and periodic patterns

## For Developers

### Testing Extensions Locally

Clone awesome-taskwarrior and your extension:
```bash
git clone https://github.com/linuxcaffe/awesome-taskwarrior.git
cd awesome-taskwarrior
./tw.py --list  # Uses local registry (dev mode)
```

### Adding Your Extension

1. Create your extension repo with files
2. Push to GitHub
3. Create `.meta` file in `awesome-taskwarrior/registry.d/`:
   ```ini
   name=my-extension
   version=1.0.0
   type=hook
   description=Brief description
   repo=https://github.com/you/my-extension
   base_url=https://raw.githubusercontent.com/you/my-extension/main/
   files=hook.py:hook,config.rc:config
   ```
4. Create installer in `awesome-taskwarrior/installers/my-extension.install`
5. Submit PR to awesome-taskwarrior

### Installer Template

```bash
#!/usr/bin/env bash
set -euo pipefail

APPNAME="my-extension"
VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/you/my-extension/main"

: "${HOOKS_DIR:=$HOME/.task/hooks}"
: "${CONFIG_DIR:=$HOME/.task/config}"

install() {
    curl -fsSL "$BASE_URL/hook.py" -o "$HOOKS_DIR/hook.py"
    chmod +x "$HOOKS_DIR/hook.py"
    
    # Write manifest
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    mkdir -p "$(dirname "$MANIFEST_FILE")"
    echo "$APPNAME|$VERSION|$HOOKS_DIR/hook.py||$TIMESTAMP" >> "$MANIFEST_FILE"
}

remove() {
    rm -f "$HOOKS_DIR/hook.py"
}

case "${1:-}" in
    install) install ;;
    remove) remove ;;
esac
```

## Architecture

### Registry Only
awesome-taskwarrior is lightweight - just metadata and installers. Extension files stay in their own repos. This means:
- No file duplication
- No sync issues  
- Extensions update independently
- Direct from source

### Self-Contained
Everything lives in `~/.task/`:
- Extensions install to standard locations
- Manifest tracks installations
- Clean uninstalls
- Easy backups

### Self-Updating
tw.py can update itself:
```bash
tw --update tw
```
Downloads latest from GitHub and replaces itself.

## Modes

### Production Mode (Normal)
When tw.py is installed via bootstrap, it fetches registry from GitHub.

### Dev Mode
When tw.py detects local `registry.d/` and `installers/` directories, it uses local files for testing.

## Troubleshooting

### tw: command not found
Ensure `~/.task/scripts` is in your PATH:
```bash
echo 'export PATH="$HOME/.task/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Extension won't install
1. Check it's listed: `tw --list`
2. Check GitHub repo is accessible
3. Try with `--dry-run`: `tw --dry-run --install app-name`

### Update tw.py
```bash
tw --update tw
```

### Fresh start
```bash
rm -rf ~/.task/scripts/tw ~/.task/config/.tw_manifest
curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash
```

## Links

- **Repository**: https://github.com/linuxcaffe/awesome-taskwarrior
- **Issues**: https://github.com/linuxcaffe/awesome-taskwarrior/issues
- **Taskwarrior**: https://taskwarrior.org

## License

MIT - See LICENSE file

## Contributing

See CONTRIBUTING.md for guidelines on adding extensions to the registry.
