# make-awesome.py v4.2.3 - Bug Fixes

## Summary
Fixed two critical bugs in v4.2.2:
1. **Branch mismatch** causing 404 errors during installation
2. **Missing .orig backup** regression in debug enhancement

---

## Bug #1: Branch Mismatch in Installer 🔴 CRITICAL

### Problem
The `.install` file was hardcoded to use `main` branch, while the `.meta` file correctly used the detected/specified branch. This caused 404 errors when trying to download files from GitHub.

### Example of Bug
```bash
# .meta file (correct):
base_url=https://raw.githubusercontent.com/linuxcaffe/tw-agenda-hook/master/

# .install file (wrong):
BASE_URL="https://raw.githubusercontent.com/linuxcaffe/tw-agenda-hook/main/"

# Result when running installer:
curl: (22) The requested URL returned error: 404
```

### Root Cause
**File**: `make-awesome.py`  
**Line**: 841  
**Code**:
```python
f.write(f'BASE_URL="https://raw.githubusercontent.com/{info.repo}/main/"\n\n')
```

### Fix Applied
**Line**: 841  
**Changed to**:
```python
f.write(f'BASE_URL="https://raw.githubusercontent.com/{info.repo}/{info.branch}/"\n\n')
```

Now the installer uses the same branch as specified in the `.meta` file.

### Testing
```bash
cd ~/dev/tw-agenda-hook

# Re-generate installer with correct branch
make-awesome.py --install
# When prompted for branch, enter: master

# Test installation
tw -I agenda-edate
# Should now successfully download all files!
```

---

## Bug #2: Missing .orig Backup 🔴 REGRESSION

### Problem
The `--debug` enhancement was creating new files named `debug.{filename}` instead of the expected behavior of:
1. Backing up original to `{filename}.orig`
2. Writing enhanced version to original `{filename}`

This was a regression from earlier versions where the .orig backup pattern was standard.

### Example of Bug
```bash
# Before running --debug:
on-add-mybook.py

# After running --debug (WRONG):
on-add-mybook.py          # original unchanged
debug.on-add-mybook.py    # new enhanced version

# Expected behavior:
on-add-mybook.py          # enhanced version
on-add-mybook.py.orig     # original backup
```

### Root Cause
**File**: `make-awesome.py`  
**Lines**: 430-438  
**Code**:
```python
output_path = Path(filepath).parent / f"debug.{Path(filepath).name}"

with open(output_path, 'w') as f:
    f.writelines(enhanced_lines)

if os.access(filepath, os.X_OK):
    os.chmod(output_path, os.stat(filepath).st_mode)

success(f"Created: {output_path}")
```

### Fix Applied
**Lines**: 430-440  
**Changed to**:
```python
# Backup original to .orig
orig_path = Path(filepath).with_suffix(Path(filepath).suffix + '.orig')
msg(f"Backing up to: {orig_path}")

# Rename original to .orig
Path(filepath).rename(orig_path)

# Write enhanced version to original filename
with open(filepath, 'w') as f:
    f.writelines(enhanced_lines)

# Copy executable permissions from .orig
if os.access(orig_path, os.X_OK):
    os.chmod(filepath, os.stat(orig_path).st_mode)

success(f"Enhanced: {filepath} (original saved as {orig_path.name})")
```

### Testing
```bash
cd ~/dev/my-hook-project

# Run debug enhancement
make-awesome.py --debug

# Should see:
[make] Processing: on-add-myhook.py
[make] Backing up to: on-add-myhook.py.orig
[make] ✓ Enhanced: on-add-myhook.py (original saved as on-add-myhook.py.orig)

# Verify:
ls -la on-add-myhook.py*
# Should show:
# -rwxr-xr-x on-add-myhook.py      (enhanced)
# -rwxr-xr-x on-add-myhook.py.orig (original backup)
```

---

## Version History

### v4.2.3 (Current)
- ✅ Fixed: Branch mismatch in installer generation
- ✅ Fixed: Restored .orig backup behavior in debug enhancement

### v4.2.2 (Previous)
- Full pipeline working end-to-end
- Known issues: branch mismatch, missing .orig backup

### v4.2.0-4.2.1
- Enhanced git status parsing
- Improved metadata defaults
- Script detection improvements

### v4.0.0
- Initial full pipeline release
- Debug → Test → Install → Push

---

## Upgrade Instructions

If you're using v4.2.2 or earlier:

```bash
cd ~/dev/awesome-taskwarrior

# Backup current version
cp make-awesome.py make-awesome.py.bak

# Download v4.2.3
curl -o make-awesome.py [URL to v4.2.3]
chmod +x make-awesome.py

# Verify version
./make-awesome.py --version
# Should show: 4.2.3
```

---

## Testing Recommendations

### Test 1: Branch Detection
```bash
cd ~/dev/your-project

# Check your actual branch
git branch --show-current

# Run installer generation
make-awesome.py --install

# When prompted for branch, verify the default matches your git branch
# If you use 'master', make sure installer shows master, not main

# Verify generated files match:
grep base_url your-project.meta
# Should show: base_url=https://raw.githubusercontent.com/user/repo/BRANCH/

grep BASE_URL your-project.install
# Should show: BASE_URL="https://raw.githubusercontent.com/user/repo/BRANCH/"
# Both should have the SAME branch!
```

### Test 2: Debug Enhancement with .orig Backup
```bash
cd ~/dev/your-hook-project

# Before enhancement:
ls -la on-add*.py
# Should show only: on-add-myhook.py

# Run debug enhancement:
make-awesome.py --debug

# After enhancement:
ls -la on-add*.py*
# Should show:
# on-add-myhook.py       (enhanced version)
# on-add-myhook.py.orig  (original backup)

# Verify no debug.* files:
ls -la debug.*
# Should show: No such file or directory
```

### Test 3: Full Pipeline
```bash
cd ~/dev/your-project

# Run complete pipeline:
make-awesome.py "Release v1.0.0"

# Should complete all stages:
# ✓ Debug enhancement (with .orig backups)
# ✓ Test (stub)
# ✓ Install generation (correct branch in both .meta and .install)
# ✓ Git push + registry update

# Verify installer works:
tw -I your-project
# Should successfully download all files with correct branch!
```

---

## Impact Assessment

### Critical (Requires Immediate Update)
- If you use a branch other than 'main' (e.g., 'master')
- If you distribute installers to users
- If you rely on .orig backups for safety

### Low Impact (Can Update at Convenience)
- If all your repos use 'main' branch
- If you don't use --debug enhancement
- If you manually test installers before distribution

---

## Known Remaining Issues
None at this time. v4.2.3 is considered stable for production use.

---

## Support
For issues or questions:
- Review previous chat: https://claude.ai/chat/9c273870-f7ce-4054-b6cd-2cfe680b2c15
- Check project documentation
- Test in isolated environment first

---

**make-awesome.py v4.2.3** - Smart coding over quick fixes! 🎯
