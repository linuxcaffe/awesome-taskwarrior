# make-awesome.py v4.2.2 - Hotfix

## Release Date: 2026-01-28

## Summary
Fixes registry commit failure when registry has other uncommitted changes.

---

## The Problem

**Scenario:**
```bash
cd ~/dev/awesome-taskwarrior
# Make some changes to make-awesome.py
# Add some dev notes
# DON'T commit them yet

cd ~/dev/tw-agenda-hook
make-awesome.py --push "Update registry"
```

**Error:**
```
[make] Updating registry...
On branch main
Changes not staged for commit:
	modified:   make-awesome.py
Untracked files:
	dev/notes.md
no changes added to commit
[make] ✗ Registry update failed: Command '['git', 'commit', '-m', 'Updated registry for agenda-edate']' returned non-zero exit status 1.
```

**Root Cause:** Git won't commit when there are other unstaged changes in the working tree, even if you only `git add` specific files.

---

## The Git Issue

**What was happening:**
```bash
cd ~/dev/awesome-taskwarrior
git add installers/agenda-edate.install
git add registry.d/agenda-edate.meta
git commit -m "Updated registry for agenda-edate"

# Git says:
# Error: Changes not staged for commit:
#   modified: make-awesome.py
# no changes added to commit
```

**Why:** Standard `git commit` requires a clean working tree OR all changes to be staged.

**Solution:** Use `git commit --only <files>` to commit only the specified files, ignoring other changes.

---

## The Fix in v4.2.2

### Added `--only` Flag to Registry Commit ✅

**Old code:**
```python
subprocess.run(['git', 'add', 'installers/file.install', 'registry.d/file.meta'])
subprocess.run(['git', 'commit', '-m', 'Updated registry'])
# Fails if other files are modified!
```

**New code:**
```python
subprocess.run(['git', 'add', 'installers/file.install', 'registry.d/file.meta'])
subprocess.run(['git', 'commit', '--only', '-m', 'Updated registry',
               'installers/file.install', 'registry.d/file.meta'])
# Works even with other modified files!
```

**The `--only` flag:**
- Commits only the specified files
- Ignores other changes in working tree
- Allows partial commits in dirty repos

---

### Handle "Nothing to Commit" in Registry ✅

**Added same logic as main repo:**
```python
result = subprocess.run(['git', 'commit', '--only', ...],
                       capture_output=True, text=True)

if result.returncode != 0:
    if 'nothing to commit' in result.stdout:
        msg("Registry files unchanged, nothing to commit")
        msg("Skipping registry push")
        return True  # Success
```

If registry files haven't changed, that's fine - skip the push.

---

## New Behavior

### Scenario 1: Dirty Registry (Common Case)
```bash
cd ~/dev/awesome-taskwarrior
# Working on make-awesome.py improvements
# Dev notes scattered around
# NOT committed yet

cd ~/dev/tw-agenda-hook
make-awesome.py --push "Update registry"

# Output:
# [make] Copying to registry...
# [make] ✓ Copied files
# [make] Updating registry...
# [make] ✓ Registry updated       # ← Works now!
# [make] ✓ Push complete!
```

✅ Registry gets updated despite other uncommitted changes

### Scenario 2: Clean Registry
```bash
cd ~/dev/awesome-taskwarrior
git status
# nothing to commit, working tree clean

cd ~/dev/tw-agenda-hook
make-awesome.py --push "Update registry"

# Output:
# [make] Updating registry...
# [make] ✓ Registry updated
# [make] ✓ Push complete!
```

✅ Works as before

### Scenario 3: Registry Files Unchanged
```bash
# Run push twice without changes
make-awesome.py --push "First push"
# → Registry updated ✓

make-awesome.py --push "Second push"
# → Registry files unchanged, nothing to commit
# → Skipping registry push
# → Push complete! ✓
```

✅ Idempotent behavior

---

## Why This Matters

**Real-world workflow:**
```bash
# You're developing make-awesome.py improvements
cd ~/dev/awesome-taskwarrior
vim make-awesome.py
# Making changes, testing, iterating...

# Meanwhile, you need to update an extension
cd ~/dev/tw-need-priority-hook
vim on-add-need-priority.py
# Fix a bug

make-awesome.py --push "Fixed priority bug"
# Before v4.2.2: FAILS because awesome-taskwarrior is dirty ✗
# After v4.2.2: WORKS! ✓
```

**The registry repo can be dirty during development!**

---

## Code Changes

### update_registry() function

**Changed commit command:**
```python
# Before:
subprocess.run(['git', 'commit', '-m', f"Updated registry for {project_name}"])

# After:
subprocess.run(['git', 'commit', '--only', '-m',
               f"Updated registry for {project_name}",
               f'installers/{install_file.name}',
               f'registry.d/{meta_file.name}'])
```

**Added error handling:**
```python
result = subprocess.run([...], capture_output=True, text=True)

if result.returncode != 0:
    if 'nothing to commit' in result.stdout:
        return True  # Success
    else:
        return False  # Real error
```

---

## Git `--only` Flag Explained

**Purpose:** Commit only specified files, ignoring other changes.

**Example:**
```bash
# Working tree:
# M  make-awesome.py        (modified, not staged)
# ?? dev/notes.md           (untracked)
# M  installers/foo.install (modified, staged)

# Regular commit fails:
git commit -m "Update"
# Error: Changes not staged for commit

# Commit with --only succeeds:
git commit --only -m "Update" installers/foo.install
# Success! Only commits foo.install
```

**Result:** Clean partial commits even in dirty repos.

---

## Testing

### Test 1: Dirty Registry
```bash
# Make registry dirty
cd ~/dev/awesome-taskwarrior
echo "# TODO" >> make-awesome.py

# Update extension
cd ~/dev/tw-need-priority-hook
make-awesome.py --push "Test v4.2.2"

# Should succeed:
# [make] ✓ Registry updated
```

### Test 2: Full Pipeline with Dirty Registry
```bash
cd ~/dev/awesome-taskwarrior
vim make-awesome.py  # Make changes, don't commit

cd ~/dev/tw-agenda-hook
make-awesome.py "Release v2.0"

# All 4 stages should complete:
# ✓ Debug
# ✓ Test (stub)
# ✓ Install
# ✓ Push (with registry update) ← Should work now!
```

---

## Files Changed

- **make-awesome.py**
  - Line 14: Version 4.2.1 → 4.2.2
  - Line 27: VERSION = "4.2.2"
  - Lines 1189-1256: `update_registry()` - added `--only` flag, error handling

---

## Summary

**v4.2.2 makes registry updates robust:**
- ✅ Works with dirty registry repos
- ✅ Works with clean registry repos
- ✅ Works when files unchanged (idempotent)
- ✅ Only commits the files it needs
- ✅ Doesn't interfere with other work

**The registry can now be a working development repo!** 🎉

---

**Version:** 4.2.2  
**Release Date:** 2026-01-28  
**Type:** Hotfix  
**Author:** David (awesome-taskwarrior maintainer)  
**Status:** Production-ready
