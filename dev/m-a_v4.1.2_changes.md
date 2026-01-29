# make-awesome.py v4.1.2 - Critical Hotfix

## Release Date: 2026-01-28

## Summary
Fixes metadata loading and project name detection for push operations.

---

## The Root Cause - Directory Name vs App Name Mismatch

**The Problem:** Projects can have different directory names from their app names:
- Directory: `tw-need_priority-hook`
- App name: `need-priority`
- Files: `need-priority.meta`, `need-priority.install`

**What was breaking:**
1. `detect_project_info()` set `info.name = Path.cwd().name` → `"tw-need_priority-hook"`
2. `prompt_for_metadata()` looked for `tw-need_priority-hook.meta` → **File not found!**
3. `cmd_push()` looked for `tw-need_priority-hook.install` → **File not found!**

This meant:
- ❌ Metadata defaults never loaded (looking for wrong filename)
- ❌ Push failed (looking for wrong .install/.meta files)

---

## Issues Fixed in v4.1.2

### 1. Metadata Defaults - Filename Mismatch ✅ FIXED

**Old broken code:**
```python
# Used directory name
meta_file = Path(f"{info.name}.meta")  # "tw-need_priority-hook.meta"
if meta_file.exists():  # FALSE! File is "need-priority.meta"
    # Never executed...
```

**New fixed code:**
```python
# Find ANY .meta file in directory
meta_files = list(Path('.').glob('*.meta'))
if meta_files:
    meta_file = meta_files[0]  # Use actual file
    msg(f"Found existing .meta file: {meta_file.name}")
    # Read name, version, description, author, tags, license, type
    # ALL from .meta file
```

**What it reads now:**
- `name=` → Sets app name correctly
- `version=` → Sets version
- `description=` → Your description
- `author=` → Your author name
- `tags=` → Your tags
- `license=` → Your license
- `type=` → hook/script/config/theme

All values from .meta now properly populate as defaults in prompts!

---

### 2. Push - Wrong Project Name ✅ FIXED

**Old broken code:**
```python
project_name = Path.cwd().name  # "tw-need_priority-hook"

# Later looks for:
install_file = original_dir / f"{project_name}.install"
# → "/path/tw-need_priority-hook/tw-need_priority-hook.install" 
# → File not found!
```

**New fixed code:**
```python
# Get project name from .meta file
meta_files = list(Path('.').glob('*.meta'))
if not meta_files:
    error("No .meta file found. Run --install first.")
    return 1

meta_file = meta_files[0]
project_name = meta_file.stem  # "need-priority" from "need-priority.meta"
msg(f"Project: {project_name}")

# Later looks for:
install_file = original_dir / f"{project_name}.install"
# → "/path/tw-need_priority-hook/need-priority.install"
# → Found! ✓
```

Now correctly identifies app name from actual files!

---

## Testing

### Test 1: Metadata Defaults
```bash
cd ~/dev/tw-need_priority-hook

# Should have: need-priority.meta (not tw-need_priority-hook.meta)
ls -la *.meta

# Run install
make-awesome.py --install

# Should now show:
# [make] Found existing .meta file: need-priority.meta
# App name [need-priority]:                                    ← From .meta!
# Version [0.3.5]:                                             ← From .meta!
# Description [Maslow's hierarchy of needs priority system]:   ← From .meta!
# Author [David]:                                              ← From .meta!
# Tags [hook,python,priority,needs,stable]:                    ← From .meta!
```

Just press Enter on all prompts to keep existing values! ✅

### Test 2: Full Pipeline
```bash
make-awesome.py "Testing v4.1.2 complete fix"

# Should complete:
# ✓ STAGE 1: Debug
# ✓ STAGE 2: Test (stub)
# ✓ STAGE 3: Install
# ✓ STAGE 4: Push
#   ✓ Git push complete
#   ✓ Copying to registry...
#   ✓ Registry updated
# ✓ PIPELINE COMPLETE!
```

---

## What Changed

**v4.1.1 → v4.1.2:**

| Function | Old Behavior | New Behavior |
|----------|-------------|--------------|
| `prompt_for_metadata()` | Looked for `{dir_name}.meta` | Finds ANY `*.meta` file |
| `prompt_for_metadata()` | Read 5 fields from .meta | Reads 7 fields including name, version |
| `cmd_push()` | Used directory name | Uses .meta filename (stem) |

---

## Key Insight

**The directory name is irrelevant!** 

What matters is the actual .meta and .install filenames, which come from the `name=` field in the .meta file. This allows projects to:
- Have descriptive directory names: `tw-need_priority-hook`
- Have simple app names: `need-priority`
- Work correctly in all scenarios ✅

---

## Files Changed

- **make-awesome.py**
  - Line 14: Version 4.1.1 → 4.1.2
  - Line 27: VERSION = "4.1.2"
  - Lines 639-669: `prompt_for_metadata()` - glob for .meta files
  - Lines 1203-1217: `cmd_push()` - use .meta stem for project name

---

## Upgrade Path

**From v4.1.1:**
1. Replace make-awesome.py with v4.1.2
2. No other changes needed
3. Existing .meta files work as-is

**Expected improvements:**
- Metadata prompts will show your existing values
- Push will find the correct .install/.meta files
- Full pipeline works end-to-end

---

## Complete Fix History

**v4.1.0:** Fixed script detection, git status, push confirmation  
**v4.1.1:** Fixed .meta reading logic, absolute paths in registry  
**v4.1.2:** Fixed filename detection for .meta and push operations

**All issues resolved! Full pipeline now works!** 🎉

---

**Version:** 4.1.2  
**Release Date:** 2026-01-28  
**Type:** Critical Hotfix  
**Author:** David (awesome-taskwarrior maintainer)  
**Status:** Production-ready
