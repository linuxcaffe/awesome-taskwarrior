# awesome-taskwarrior Architecture - Registry Only

## Overview

awesome-taskwarrior is a **registry** (like npm, PyPI, cargo) that points to extension repos. It does NOT host the actual extension files.

## Architecture

```
┌─────────────────────────────────────────┐
│  awesome-taskwarrior (Registry)         │
│  ├── tw.py (package manager)            │
│  ├── registry.d/                        │
│  │   └── tw-recurrence.meta  ──────┐   │
│  └── installers/                    │   │
│      └── tw-recurrence.install ─────┤   │
└─────────────────────────────────────┘   │
                                          │
         Points to ↓                      │
                                          │
┌─────────────────────────────────────────┴───┐
│  tw-recurrence_overhaul-hook (Extension)    │
│  ├── on-add_recurrence.py                   │
│  ├── on-exit_recurrence.py                  │
│  ├── recurrence.rc                          │
│  ├── rr                                     │
│  └── README.md                              │
└─────────────────────────────────────────────┘
```

## How It Works

1. **tw.py fetches registry** → Gets list of available apps from GitHub
2. **User installs app** → tw.py downloads installer from awesome-taskwarrior
3. **Installer runs** → Downloads actual files from **original repo**
4. **Files installed** → Tracked in local manifest

## Key Files

### registry.d/tw-recurrence.meta
```ini
name=tw-recurrence_overhaul-hook
version=2.0.0
type=hook
repo=https://github.com/linuxcaffe/tw-recurrence_overhaul-hook
base_url=https://raw.githubusercontent.com/linuxcaffe/tw-recurrence_overhaul-hook/main/
files=on-add_recurrence.py:hook,on-exit_recurrence.py:hook,recurrence.rc:config
```

**Key:** `base_url` points to the **original extension repo**, not awesome-taskwarrior!

### installers/tw-recurrence.install
```bash
#!/usr/bin/env bash
APPNAME="tw-recurrence"
VERSION="2.0.0"
BASE_URL="https://raw.githubusercontent.com/linuxcaffe/tw-recurrence_overhaul-hook/main"

# Downloads files from tw-recurrence_overhaul-hook repo
curl -fsSL "$BASE_URL/on-add_recurrence.py" -o "$HOOKS_DIR/on-add_recurrence.py"
```

**Key:** Installer downloads from **original repo**, not awesome-taskwarrior!

## Benefits

### ✅ No File Duplication
- Extension files live only in their own repos
- awesome-taskwarrior just points to them
- No sync issues

### ✅ Single Source of Truth
- Extension repo is authoritative
- No stale copies
- Direct from source

### ✅ Lightweight Registry
- awesome-taskwarrior is tiny (just metadata)
- Fast to clone/update
- Easy to maintain

### ✅ Developer Friendly
- Push to extension repo → immediately available
- No need to update two repos
- One place to maintain code

### ✅ Like Real Package Managers
- npm points to GitHub/package repos
- PyPI points to source distributions
- apt points to package servers

## Workflow

### Adding a New Extension

1. **Developer creates extension repo** (e.g., tw-priority)
2. **Push files to GitHub**
3. **Create .meta in awesome-taskwarrior**:
   ```ini
   name=tw-priority
   version=1.0.0
   base_url=https://raw.githubusercontent.com/user/tw-priority/main/
   ```
4. **Create .install in awesome-taskwarrior** that downloads from `base_url`
5. **Done!** Users can `tw --install tw-priority`

### Updating an Extension

1. **Developer updates extension repo**
2. **Push changes**
3. **Update version in awesome-taskwarrior .meta file**
4. **Done!** Next `tw --install` gets new version

No file copying needed!

## For tw-recurrence Setup

### In tw-recurrence_overhaul-hook repo:

```bash
cd ~/dev/tw-recurrence_overhaul-hook

# Make sure these files exist and are pushed:
git add on-add_recurrence.py on-exit_recurrence.py recurrence.rc rr README.md
git commit -m "Release v2.0.0 for awesome-taskwarrior"
git push
```

### In awesome-taskwarrior repo:

```bash
cd ~/dev/awesome-taskwarrior

# Add the metadata and installer (already done)
cp /path/to/tw-recurrence.meta registry.d/
cp /path/to/tw-recurrence.install installers/

git add registry.d/tw-recurrence.meta installers/tw-recurrence.install
git commit -m "Add tw-recurrence v2.0.0 to registry"
git push
```

### Test:

```bash
# Wait a minute for GitHub to sync
tw --list
tw --install tw-recurrence
```

## Directory Structure

### awesome-taskwarrior (Registry)
```
awesome-taskwarrior/
├── tw.py
├── registry.d/
│   └── tw-recurrence.meta       # Points to tw-recurrence repo
└── installers/
    └── tw-recurrence.install    # Downloads from tw-recurrence repo
```

### tw-recurrence_overhaul-hook (Extension)
```
tw-recurrence_overhaul-hook/
├── on-add_recurrence.py         # Actual files
├── on-exit_recurrence.py
├── recurrence.rc
├── rr
└── README.md
```

## Comparison to Other Package Managers

### npm (Node.js)
```
Registry: npmjs.com (metadata only)
  ↓ points to
Packages: github.com, gitlab.com, etc.
```

### PyPI (Python)
```
Registry: pypi.org (metadata + links)
  ↓ points to
Packages: GitHub releases, wheels, etc.
```

### awesome-taskwarrior
```
Registry: awesome-taskwarrior repo (metadata + installers)
  ↓ points to
Extensions: Individual GitHub repos
```

## Key Insight

The installer IS the package. It contains:
1. Metadata (version, name, etc.)
2. Installation logic
3. URLs to download files from

The registry just hosts installers and makes them discoverable.

## Summary

**awesome-taskwarrior** = Registry (metadata + installers)  
**Extension repos** = Source of truth (actual files)  
**tw.py** = Package manager (fetches registry, runs installers)

No file duplication. No sync issues. Simple and maintainable!
