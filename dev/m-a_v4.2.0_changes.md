# make-awesome.py v4.2.0 - Branch Detection

## Release Date: 2026-01-28

## Summary
Adds automatic detection and prompting for git branch to fix 404 errors in generated installers.

---

## The 404 Problem

**Symptom:**
```bash
tw -I agenda-edate
# curl: (22) The requested URL returned error: 404
# [tw] ✗ Failed to download on-add_agenda.py
```

**Root Cause:**
The generated .install file was hardcoded to use `main` branch:
```bash
BASE_URL="https://raw.githubusercontent.com/linuxcaffe/tw-agenda-hook/main/"
```

But the actual repository uses `master` branch!

**Result:** All file downloads returned 404 because the URLs were wrong.

---

## What Changed in v4.2.0

### 1. Branch Detection ✅ NEW FEATURE

**Auto-detects the current git branch:**
```python
# Method 1: Get current branch
git rev-parse --abbrev-ref HEAD

# Method 2: Get default branch from remote
git remote show origin | grep "HEAD branch"

# Fallback: "main"
```

**Shows in detection phase:**
```
[make] Project: tw-agenda-hook
[make] Version: 1.0.0
[make] GitHub: linuxcaffe/tw-agenda-hook
[make] Branch: master                    # ← NEW!
```

---

### 2. Branch Prompt ✅ NEW PROMPT

**New prompt added to --install:**
```
App name [agenda-edate]: 
Version [1.0.0]: 
Type: (1) hook, (2) script, (3) config, (4) theme
Select [1]: 
Description [agenda edate]: 
GitHub repo [linuxcaffe/tw-agenda-hook]: 
Branch [master]:                          # ← NEW PROMPT!
Author [linuxcaffe]: 
License [MIT]: 
```

User can:
- Press Enter to accept detected branch
- Type a different branch name (e.g., `develop`, `v2`, etc.)

---

### 3. Branch Stored in .meta ✅ PERSISTED

**The branch is embedded in base_url:**
```ini
# Before (v4.1.2):
base_url=https://raw.githubusercontent.com/linuxcaffe/tw-agenda-hook/main/

# After (v4.2.0):
base_url=https://raw.githubusercontent.com/linuxcaffe/tw-agenda-hook/master/
```

**On subsequent runs:**
- Reads branch from existing base_url
- Shows as default in prompt
- User can change if needed

---

### 4. Correct URLs Generated ✅ FIXED

**Old (broken):**
```bash
BASE_URL="https://raw.githubusercontent.com/user/repo/main/"
curl -fsSL "$BASE_URL/file.py"  # → 404 if branch is master
```

**New (working):**
```bash
BASE_URL="https://raw.githubusercontent.com/user/repo/master/"
curl -fsSL "$BASE_URL/file.py"  # → 200 ✓
```

---

## Testing

### Test 1: New Project (Auto-Detection)
```bash
cd ~/dev/tw-agenda-hook

# If current branch is "master":
make-awesome.py --install

# Should show:
# [make] Branch: master
# ...
# Branch [master]:  ← Just press Enter!

# Generated .meta will have:
# base_url=https://raw.githubusercontent.com/.../master/
```

### Test 2: Existing Project (Reads from .meta)
```bash
# If agenda-edate.meta already has base_url with "main":
make-awesome.py --install

# Prompt shows:
# Branch [main]:

# Type "master" and press Enter to fix it
Branch [main]: master

# Now .meta will have:
# base_url=https://raw.githubusercontent.com/.../master/
```

### Test 3: Installation Works
```bash
# After fixing branch in .meta:
make-awesome.py --install  # Regenerate with correct branch
make-awesome.py --push "Fixed branch"

# Now test installation:
tw -I agenda-edate

# Should work:
# [tw] Installing agenda-edate v1.0.0...
# [tw] Downloading files...
# [tw] ✓ Installed agenda-edate v1.0.0
```

---

## Code Changes

### ProjectInfo Class
**Added:**
```python
self.branch = "main"  # New field
```

### detect_project_info()
**Added:**
```python
# Detect default branch
result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], ...)
info.branch = result.stdout.strip()
```

### prompt_for_metadata()
**Added:**
```python
# Read branch from existing .meta base_url
if line.startswith('base_url='):
    url = line.split('=', 1)[1].strip()
    parts = url.split('/')
    if len(parts) >= 6:
        info.branch = parts[5]  # Extract branch from URL

# Prompt for branch
response = input(f"Branch [{info.branch}]: ").strip()
if response:
    info.branch = response
```

### generate_meta_file()
**Changed:**
```python
# Before:
base_url = f"https://raw.githubusercontent.com/{info.repo}/main/"

# After:
base_url = f"https://raw.githubusercontent.com/{info.repo}/{info.branch}/"
```

---

## Upgrade Notes

**From v4.1.2 to v4.2.0:**
- No breaking changes
- Existing .meta files work but may have wrong branch
- **Action needed:** Re-run `--install` on projects with 404 errors and correct the branch

**To fix existing projects:**
```bash
cd ~/dev/problematic-project

# Run install, fix branch when prompted
make-awesome.py --install
# When you see: Branch [main]: 
# Type the correct branch (e.g., "master")

# Regenerate installer
make-awesome.py --push "Fixed branch for installation"
```

---

## Common Scenarios

### Scenario 1: Repository uses "master"
```
Branch [main]: master     # Type "master"
```

### Scenario 2: Repository uses "main" (default is correct)
```
Branch [main]:            # Just press Enter
```

### Scenario 3: Custom branch (e.g., "develop")
```
Branch [main]: develop    # Type "develop"
```

### Scenario 4: Release branch (e.g., "v2.0")
```
Branch [main]: v2.0       # Type "v2.0"
```

---

## Why This Matters

**GitHub transitioned from "master" to "main" as default branch name in 2020.** 

This means:
- Older repos use `master`
- Newer repos use `main`
- Some use custom branches

**Before v4.2.0:** All installers broke for non-main branches  
**After v4.2.0:** Works with any branch ✓

---

## Files Changed

- **make-awesome.py**
  - Line 14: Version 4.1.2 → 4.2.0
  - Line 27: VERSION = "4.2.0"
  - Lines 520-534: `ProjectInfo.__init__()` - added branch field
  - Lines 537-593: `detect_project_info()` - added branch detection
  - Lines 647-683: `prompt_for_metadata()` - read branch from .meta, add prompt
  - Line 805: `generate_meta_file()` - use info.branch not hardcoded "main"

---

## Summary

**v4.2.0 fixes the 404 installation errors by:**
1. Auto-detecting the git branch
2. Allowing user confirmation/correction
3. Generating URLs with correct branch
4. Persisting branch in .meta for future runs

**Test your agenda-edate project again - it should install successfully now!** 🎉

---

**Version:** 4.2.0  
**Release Date:** 2026-01-28  
**Type:** Feature Release  
**Author:** David (awesome-taskwarrior maintainer)  
**Status:** Production-ready
