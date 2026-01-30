# make-awesome.py v4.1.0 - Bug Fixes

## Release Date: 2026-01-28

## Summary
Critical bug fixes for script detection, git status parsing, and push workflow improvements.

---

## Issues Fixed

### 1. Script Detection - Executables Without Extensions ✅ FIXED

**Problem:** Scripts without file extensions (like `nn`, `rr`, etc.) were not being detected by `detect_files()`.

**Root Cause:** The function only looked for `*.py` and `*.sh` files:
```python
# OLD - BROKEN:
for ext in ['py', 'sh']:
    for f in Path('.').glob(f'*.{ext}'):
```

**Fix:** Now checks ALL files in root directory for executables:
```python
# NEW - FIXED:
for f in Path('.').iterdir():
    if os.access(f, os.X_OK):
        # Check for shebang or script extension
```

**Detection Logic:**
1. Iterate through all files in project root
2. Skip excluded patterns (debug.*, .orig, hooks, make-awesome.py, etc.)
3. Check if file is executable (`os.access(f, os.X_OK)`)
4. Verify it's a script by checking for:
   - Shebang (`#!` at start of file), OR
   - Script extension (`.py`, `.sh`, `.bash`, `.pl`, `.rb`)

**Result:** Now detects executables like `nn`, `rr`, `agenda`, etc. ✅

---

### 2. Git Status Parsing - Format Mismatch ✅ FIXED

**Problem:** Git status check failed because it was checking if entire line ended with `.install` or `.meta`, but git status format includes status markers.

**Git Status Format:**
```
 M need-priority.meta     # Modified
?? need-priority.install  # Untracked
```

**Old Code - BROKEN:**
```python
only_registry_files = all(
    line.strip().endswith('.install') or line.strip().endswith('.meta')
    for line in lines if line.strip()
)
```
This checked if `" M need-priority.meta"` ends with `.meta` → FALSE!

**New Code - FIXED:**
```python
# Parse git status format: "XY filename"
changed_files = []
for line in lines:
    # First 2 chars are status, rest is filename
    filename = line[3:].strip() if len(line) > 3 else ""
    if filename:
        changed_files.append(filename)

only_registry_files = all(
    fname.endswith('.install') or fname.endswith('.meta')
    for fname in changed_files
)
```

**Result:** Correctly identifies .install/.meta files as expected changes ✅

---

### 3. Push Workflow - User Confirmation ✅ IMPROVED

**Problem:** `--push` stage would blindly run `git add .` without showing what's being added or asking for confirmation.

**Enhancement:** Now shows git status and asks before adding:

```bash
[make] Files to be committed:
 M need-priority.meta
?? need-priority.install
Run 'git add .'? [Y/n]: 
```

**Options:**
- Press Enter or `y` → Runs `git add .`
- Press `n` → Skips `git add`, uses only staged files

**Benefits:**
1. User sees what's changed before committing
2. User can choose to manually stage specific files
3. Prevents accidental commits of unwanted files
4. Makes pipeline flow more transparent

---

## Testing Checklist

### Test 1: Script Detection
```bash
cd ~/dev/tw-need_priority-hook
make-awesome.py --install

# Should detect:
# ✓ Hook: on-add-need-priority.py
# ✓ Hook: on-modify-need-priority.py
# ✓ Hook: on-exit-need-priority.py
# ✓ Script: nn                         # ← THIS IS THE FIX!
# ✓ Config: need.rc
# ✓ Doc: README.md
```

### Test 2: Git Status Parsing
```bash
# After --install creates .meta and .install files
make-awesome.py --push "test"

# Should show:
# [make] Found new .install and .meta files (expected from --install stage)
# [make] Files to be committed:
#  M need-priority.meta
# ?? need-priority.install
# Run 'git add .'? [Y/n]: 
```

### Test 3: Full Pipeline
```bash
make-awesome.py "Release v1.0"

# Stage 1: Debug → Success
# Stage 2: Test → Success (stub)
# Stage 3: Install → Detects all files including nn
# Stage 4: Push → Shows status, asks for confirmation
```

---

## Upgrade Notes

**From v4.0.0 to v4.1.0:**
- No breaking changes
- Existing projects will now detect more scripts
- Push workflow requires user interaction (confirmation)
- Git status logic is more robust

**Recommended Actions:**
1. Re-run `--install` on existing projects to pick up missing scripts
2. Update generated .meta files with newly detected executables
3. Test push workflow with new confirmation prompts

---

## Known Limitations

1. **Test stage still stub** - Full test infrastructure coming in future version
2. **Script detection heuristic** - Relies on shebang or extension; may miss edge cases
3. **GitHub URL validation** - Does not verify URLs actually work (returns 200)

---

## Files Changed

- `make-awesome.py` (main file)
  - Version bumped: 4.0.0 → 4.1.0
  - Function modified: `detect_files()` (lines 567-630)
  - Function modified: `check_git_status()` (lines 1023-1055)
  - Function modified: `git_commit_and_push()` (lines 1058-1080)

---

## Summary of Improvements

| Issue | Status | Impact |
|-------|--------|--------|
| Script detection without extensions | ✅ Fixed | Critical - nn, rr, etc. now detected |
| Git status parsing | ✅ Fixed | Critical - push workflow now works |
| Push confirmation | ✅ Added | Enhancement - better UX |
| Metadata defaults | ✅ Already working | N/A - no changes needed |

---

**Version:** 4.1.0  
**Release Date:** 2026-01-28  
**Author:** David (awesome-taskwarrior maintainer)  
**Status:** Production-ready
