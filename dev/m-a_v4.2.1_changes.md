# make-awesome.py v4.2.1 - Hotfix

## Release Date: 2026-01-28

## Summary
Fixes git commit failure when .install/.meta files are already committed.

---

## The Problem

**Scenario:**
1. Run `--install` to generate need-priority.install and need-priority.meta
2. Files get committed to git
3. Run `--push` again to update registry
4. **Git commit fails** because there's nothing to commit

**Error:**
```
[make] Git add...
[make] Commit: m-a v4.2.0 --push test
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
[make] ✗ Git failed: Command '['git', 'commit', '-m', '...']' returned non-zero exit status 1.
```

**Result:** Pipeline fails, registry never gets updated ❌

---

## The Issue

When .install and .meta files are already committed from a previous run, there's nothing new to commit. The old code treated this as an error and stopped the pipeline.

**But this is actually fine!** The goal of `--push` is to update the registry, which can happen even if there are no new git commits to make.

---

## The Fix in v4.2.1

### 1. Check for Empty Working Tree First ✅

**Before commit attempt:**
```python
result = subprocess.run(['git', 'status', '--short'], ...)

if not result.stdout.strip():
    msg("Working tree clean, nothing to commit")
    msg("Skipping git commit (but will update registry)")
    return True  # Success - proceed to registry update
```

If working tree is clean, skip git commit/push entirely and proceed to registry update.

### 2. Handle "Nothing to Commit" Error ✅

**After commit attempt:**
```python
result = subprocess.run(['git', 'commit', '-m', commit_msg], ...)

if result.returncode != 0:
    if 'nothing to commit' in result.stdout or 'nothing to commit' in result.stderr:
        msg("Nothing to commit, working tree clean")
        msg("Skipping git push (but will update registry)")
        return True  # Success - proceed to registry update
```

If commit fails due to "nothing to commit", treat it as success and proceed.

---

## New Behavior

### Scenario 1: Files Already Committed
```bash
make-awesome.py --push "Update registry"

# Output:
# [make] Files to be committed:
# [make] Working tree clean, nothing to commit
# [make] Skipping git commit (but will update registry)
# [make] Copying to registry...
# [make] ✓ Copied files
# [make] Updating registry...
# [make] ✓ Registry updated
# [make] ✓ Push complete!
```

✅ Registry gets updated without requiring a git commit

### Scenario 2: New Changes to Commit
```bash
# Make changes to on-add-hook.py
make-awesome.py --push "Fixed bug in hook"

# Output:
# [make] Files to be committed:
#  M on-add-hook.py
# Run 'git add .'? [Y/n]: 
# [make] Git add...
# [make] Commit: Fixed bug in hook
# [make] Push...
# [make] ✓ Git push complete
# [make] Copying to registry...
# [make] ✓ Registry updated
# [make] ✓ Push complete!
```

✅ Git commit/push happens, then registry update

### Scenario 3: Only .install/.meta Changed
```bash
# Re-ran --install with updated description
make-awesome.py --push "Updated description"

# Output:
# [make] Files to be committed:
#  M need-priority.meta
# Run 'git add .'? [Y/n]: 
# [make] Git add...
# [make] Commit: Updated description
# [make] Push...
# [make] ✓ Git push complete
# [make] Copying to registry...
# [make] ✓ Registry updated
# [make] ✓ Push complete!
```

✅ Git commit/push for .meta change, then registry update

---

## Why This Matters

**Common workflow:**
```bash
# Initial setup
make-awesome.py "Initial release"
# → Commits everything, updates registry ✓

# Later: Just want to update registry (no code changes)
make-awesome.py --push "Refresh registry"
# → Before v4.2.1: FAILS ✗
# → After v4.2.1: SUCCESS ✓
```

**Use case:** When you want to push an existing project to a new registry location without making code changes.

---

## Code Changes

### git_commit_and_push() function

**Added early check:**
```python
if not result.stdout.strip():
    msg("Working tree clean, nothing to commit")
    msg("Skipping git commit (but will update registry)")
    return True
```

**Changed commit error handling:**
```python
# Old:
subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
# → Any non-zero exit = exception = failure

# New:
result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                       capture_output=True, text=True)
if result.returncode != 0:
    if 'nothing to commit' in result.stdout or 'nothing to commit' in result.stderr:
        return True  # Success!
    else:
        return False  # Real error
```

---

## Testing

### Test 1: Registry Update Without Changes
```bash
cd ~/dev/tw-need_priority-hook

# Files already committed
git status
# → nothing to commit, working tree clean

# Try to push anyway
make-awesome.py --push "Refresh registry"

# Should succeed:
# [make] Working tree clean, nothing to commit
# [make] Skipping git commit (but will update registry)
# [make] ✓ Registry updated
# [make] ✓ Push complete!
```

### Test 2: Full Pipeline (Idempotent)
```bash
# Run full pipeline twice in a row
make-awesome.py "Test 1"
# → Everything commits ✓

make-awesome.py "Test 2"
# → Stage 4 skips git commit (nothing changed)
# → Registry still updates ✓
```

---

## Files Changed

- **make-awesome.py**
  - Line 14: Version 4.2.0 → 4.2.1
  - Line 27: VERSION = "4.2.1"
  - Lines 1116-1166: `git_commit_and_push()` - added early check, improved error handling

---

## Upgrade Notes

**From v4.2.0:**
- Drop-in replacement
- No configuration changes needed
- Existing workflows work as before
- New capability: Can run `--push` multiple times without errors

---

## Summary

**v4.2.1 makes `--push` idempotent:**
- ✅ Works when files are already committed
- ✅ Works when there are new changes
- ✅ Always updates registry regardless
- ✅ No false failures

**Now you can run the pipeline as many times as you want!** 🎉

---

**Version:** 4.2.1  
**Release Date:** 2026-01-28  
**Type:** Hotfix  
**Author:** David (awesome-taskwarrior maintainer)  
**Status:** Production-ready
