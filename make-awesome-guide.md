# make-awesome-install.sh - Usage Guide

Automated tool to package your Taskwarrior extension for awesome-taskwarrior registry.

## What It Does

1. **Detects** your project files (hooks, scripts, configs, docs)
2. **Prompts** for metadata (name, version, description, etc.)
3. **Calculates** SHA256 checksums
4. **Generates** `.meta` file for the registry
5. **Creates** `.install` installer script
6. **Ready** for PR to awesome-taskwarrior!

## Quick Start

```bash
# 1. Download the script
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/make-awesome-install.sh -o make-awesome-install.sh
chmod +x make-awesome-install.sh

# 2. Run it in your project root
cd ~/my-taskwarrior-extension
../make-awesome-install.sh

# 3. Follow the prompts
# 4. Test the installer
./my-extension.install install

# 5. Submit to awesome-taskwarrior (see below)
```

## Example Session

```bash
$ cd ~/tw-priority-hook
$ ~/make-awesome-install.sh

============================================================================
make-awesome-install.sh v1.0.0
Generate installer and metadata for awesome-taskwarrior
============================================================================

[make] Detecting project information...
[make] ✓ Project: tw-priority-hook
[make] ✓ Version: 1.0.0
[make] ✓ GitHub: https://github.com/djp/tw-priority-hook

[make] Detecting project files...
[make] ✓ Hooks: on-add_priority.py:hook on-modify_priority.py:hook
[make] ✓ Configs: priority.rc:config
[make] ✓ Docs: README.md:doc

[make] Gathering metadata...

App name [tw-priority-hook]: 
Version [1.0.0]: 
Type: (1) hook, (2) script, (3) config, (4) theme
Select [1]: 1
Short description: Priority management based on Maslow's hierarchy
GitHub repo [djp/tw-priority-hook]: 
Author [David J Patrick]: 
License [MIT]: 
Requires Taskwarrior version [2.6.0]: 
Requires Python version (leave blank if N/A): 3.6

[make] Calculating SHA256 checksums...
[make] ✓ on-add_priority.py: abc123...
[make] ✓ on-modify_priority.py: def456...
[make] ✓ priority.rc: ghi789...
[make] ✓ README.md: jkl012...

[make] Generating tw-priority-hook.meta...
[make] ✓ Created tw-priority-hook.meta

[make] Generating tw-priority-hook.install...
[make] ✓ Created tw-priority-hook.install

============================================================================
[make] ✓ Package created successfully!
============================================================================

[make] Generated files:
  • tw-priority-hook.meta
  • tw-priority-hook.install

[make] Next steps:
  1. Test the installer...
  2. Fork awesome-taskwarrior...
  3. Clone and add files...
  4. Commit and create PR...

[make] ✓ Done! Happy contributing to awesome-taskwarrior!
```

## What Gets Detected

### Hooks
- `on-add*.py` or `on-add*.sh`
- `on-exit*.py` or `on-exit*.sh`
- `on-modify*.py` or `on-modify*.sh`

### Scripts
- Executable `.py` or `.sh` files (excluding hooks)

### Configs
- `*.rc` files
- `*.conf` files

### Documentation
- `README.md`
- `USAGE.md`
- `INSTALL.md`

## Generated Files

### `.meta` File
```ini
name=my-extension
version=1.0.0
type=hook
description=Brief description
repo=https://github.com/user/my-extension
base_url=https://raw.githubusercontent.com/user/my-extension/main/
files=hook.py:hook,config.rc:config,README.md:doc
checksums=abc123...,def456...,ghi789...
author=Your Name
license=MIT
requires_taskwarrior=2.6.0
requires_python=3.6
```

### `.install` File
Self-contained bash installer that:
- Downloads files from your GitHub repo
- Installs to proper directories
- Adds config to .taskrc
- Tracks in manifest
- Provides clean removal

## Testing Your Package

```bash
# Test installation
./my-extension.install install

# Verify files
ls -la ~/.task/hooks/
ls -la ~/.task/config/
cat ~/.task/config/.tw_manifest

# Test functionality
task add "Test task"

# Test removal
./my-extension.install remove
```

## Submitting to awesome-taskwarrior

### Step 1: Fork
Go to https://github.com/linuxcaffe/awesome-taskwarrior and click "Fork"

### Step 2: Clone and Add Files
```bash
git clone https://github.com/YOUR_USERNAME/awesome-taskwarrior.git
cd awesome-taskwarrior

# Copy generated files
cp ~/my-extension/my-extension.meta registry.d/
cp ~/my-extension/my-extension.install installers/

# Make installer executable
chmod +x installers/my-extension.install
```

### Step 3: Test with tw.py
```bash
# Test in dev mode
./tw.py --list          # Should show your extension
./tw.py --info my-extension
./tw.py --install my-extension
./tw.py --remove my-extension
```

### Step 4: Commit and Push
```bash
git add registry.d/my-extension.meta installers/my-extension.install
git commit -m "Add my-extension v1.0.0

- Brief description of what it does
- Key features
- Any requirements or notes"

git push origin main
```

### Step 5: Create PR
1. Go to your fork on GitHub
2. Click "Pull Request"
3. Add description:
   - What the extension does
   - Why it's useful
   - Link to your extension repo
   - Testing you've done

## Updating Your Extension

When you release a new version:

```bash
# 1. Update version in your project
# 2. Commit and push to GitHub

# 3. Re-run make-awesome-install.sh
cd ~/my-extension
make-awesome-install.sh

# 4. Submit PR with updated files
# Same process as initial submission
```

## Troubleshooting

### Script doesn't detect my files
Make sure:
- Hooks are named `on-add*`, `on-exit*`, or `on-modify*`
- Scripts are executable (`chmod +x`)
- Configs end in `.rc` or `.conf`

### Missing GitHub repo
Initialize git if not already:
```bash
git init
git remote add origin https://github.com/user/repo.git
```

Or manually enter repo URL when prompted.

### Checksums change
Checksums are calculated from current files. If you edit files after running the script, re-run it to get updated checksums.

### Installer doesn't work
Test the installer before submitting:
```bash
./my-extension.install install
./my-extension.install remove
```

Check that BASE_URL points to your GitHub repo's raw files.

## Advanced: Manual Customization

After generation, you can edit the files:

### Custom installer logic
Edit the `.install` file to add:
- Special installation steps
- Additional dependencies
- Custom configuration

### Additional metadata
Edit the `.meta` file to add:
- More detailed description
- Additional requirements
- Custom fields

## Pro Tips

1. **Test locally first** - Use `tw.py --install` in dev mode
2. **Good description** - Clear, concise, explains value
3. **Check checksums** - Re-run if files change
4. **Version tags** - Tag releases in your repo
5. **Documentation** - Include good README.md
6. **License** - Include LICENSE file in your repo

## Getting Help

- Issues: https://github.com/linuxcaffe/awesome-taskwarrior/issues
- Examples: Look at existing extensions in registry.d/
- Community: taskwarrior.org forums

## Example Projects to Package

Good candidates for awesome-taskwarrior:
- Custom hooks (priority, context, sync)
- Helper scripts (reporting, migration)
- Theme configurations
- Integration tools

Not suitable:
- Non-taskwarrior tools
- Proprietary/closed-source
- Unmaintained projects
