# tw.py GitHub Integration - Completion Guide

## Status: 90% Complete

### ✅ What's Already Done (in tw.py 2.1.0)

1. **GitHub Configuration** (lines ~13-17)
   - GITHUB_REPO, GITHUB_BRANCH, GITHUB_API_BASE, GITHUB_RAW_BASE constants added

2. **Imports** (lines ~1-14)
   - json, tempfile, urllib.request imports added

3. **DebugLogger** (lines ~26-92)
   - Complete with file logging and environment variables

4. **TagFilter** (lines ~94-159)
   - Complete tag filtering with +/- syntax

5. **PathManager Updated** (lines ~161-210)
   - `is_dev_mode` detection added
   - `local_registry` and `local_installers` paths added
   - Old `registry_dir` and `installers_dir` replaced

6. **RegistryManager Class** (lines ~212-321)
   - ✅ `list_apps()` - works for both local and GitHub
   - ✅ `_list_local_apps()` - lists from local registry.d/
   - ✅ `_list_github_apps()` - fetches from GitHub API
   - ✅ `get_meta()` - gets MetaFile from local or GitHub
   - ✅ `get_installer()` - downloads installer, returns temp file path

7. **Short Flags** (lines ~1192-1203)
   - All added: -I, -i, -r, -u, -l, -s, -h, -v

8. **--tags Feature** (lines ~1200+)
   - Argument parsing and tag filtering logic

9. **Interactive Shell** (lines ~754-1017)
   - Complete with :help shell support

### ⚠️ What Needs Fixing

All these methods in AppManager need to use `self.registry` instead of direct path access:

#### 1. `install()` method (line ~471)
**Current:**
```python
installer_path = self.paths.installers_dir / f"{app_name}.install"
```

**Should be:**
```python
installer_path = self.registry.get_installer(app_name)
is_temp_file = not self.paths.is_dev_mode
# ... at end of method:
if is_temp_file and installer_path:
    os.unlink(installer_path)
```

#### 2. `remove()` method (line ~534)
**Current:**
```python
installer_path = self.paths.installers_dir / f"{app_name}.install"
```

**Should be:**
```python
installer_path = self.registry.get_installer(app_name)
is_temp_file = not self.paths.is_dev_mode
# ... at end:
if is_temp_file and installer_path:
    os.unlink(installer_path)
```

#### 3. `list_installed()` method (line ~605, 623)
**Current:**
```python
meta_path = self.paths.registry_dir / f"{app}.meta"
if meta_path.exists():
    meta = MetaFile(meta_path)
```

**Should be:**
```python
meta = self.registry.get_meta(app)
if meta:
```

#### 4. `list_tags()` method (line ~642)
**Current:**
```python
for meta_path in self.paths.registry_dir.glob("*.meta"):
    app_name = meta_path.stem
    meta = MetaFile(meta_path)
```

**Should be:**
```python
apps = self.registry.list_apps()
for app_name in apps:
    meta = self.registry.get_meta(app_name)
    if not meta:
        continue
```

#### 5. `show_info_all()` method (lines ~677-707)
**Current:**
```python
debug(f"show_info_all called, registry_dir={self.paths.registry_dir}", 2)
meta_files = list(self.paths.registry_dir.glob("*.meta"))
for meta_path in meta_files:
    app_name = meta_path.stem
```

**Should be:**
```python
debug(f"show_info_all called, dev_mode={self.paths.is_dev_mode}", 2)
all_apps = self.registry.list_apps()
for app_name in all_apps:
    meta = self.registry.get_meta(app_name)
    if not meta:
        continue
```

#### 6. `show_info()` method (line ~726)
**Current:**
```python
meta_path = self.paths.registry_dir / f"{app_name}.meta"
if not meta_path.exists():
    print(f"[tw] ✗ Application not found: {app_name}")
    return False
meta = MetaFile(meta_path)
```

**Should be:**
```python
meta = self.registry.get_meta(app_name)
if not meta:
    print(f"[tw] ✗ Application not found: {app_name}")
    return False
```

#### 7. `verify()` method (line ~769)
**Current:**
```python
meta_path = self.paths.registry_dir / f"{app_name}.meta"
if not meta_path.exists():
    print(f"[tw] ⚠ Meta file not found: {meta_path}")
    return False
meta = MetaFile(meta_path)
```

**Should be:**
```python
meta = self.registry.get_meta(app_name)
if not meta:
    print(f"[tw] ⚠ Meta file not found for: {app_name}")
    return False
```

### 🔧 Quick Fix Script

Run this to make all the changes at once:

```bash
cd /path/to/tw.py/directory

# Backup first!
cp tw.py tw.py.backup

# Then apply changes (this is pseudocode, actual implementation would need careful sed/awk)
# Or just manually fix the 7 methods listed above
```

### ✨ New Features to Add

Once the above fixes are done, consider adding:

**1. `--available` command** (like --list but shows all apps from registry, not just installed)

Add to main():
```python
if args.available:
    all_apps = app_manager.registry.list_apps()
    print(f"[tw] Available applications ({len(all_apps)}):")
    for app_name in sorted(all_apps):
        meta = app_manager.registry.get_meta(app_name)
        if meta:
            installed = "✓" if app_manager.manifest.is_installed(app_name) else " "
            print(f"[tw] [{installed}] {app_name} - {meta.get('description', 'No description')}")
    return 0
```

**2. Mode indicator in output**

Already partially done - PathManager prints mode on init. Consider adding to --version:
```python
if args.version:
    mode = "DEV" if paths.is_dev_mode else "PRODUCTION"
    print(f"tw.py version {VERSION} ({mode} mode)")
    return 0
```

### 🧪 Testing Checklist

**Production Mode (no local registry):**
```bash
# Copy tw.py somewhere without registry.d/
cp tw.py /tmp/tw && chmod +x /tmp/tw
cd /tmp

# Should say "PRODUCTION mode"
./tw --debug --version

# Should fetch from GitHub
./tw --list  # Shows installed (from manifest)
./tw --info tw-recurrence  # Fetches .meta from GitHub
./tw --install tw-recurrence  # Downloads installer from GitHub

# Clean up
rm /tmp/tw
```

**Dev Mode (with local registry):**
### NOTE FROM DAVID ### Dev mode for tw is only activated when the folder registry.d is in the cwd, presumes to be in a clone of awsome-taskwarrior github. In dev mode, tw file related actions; list info tags etc, use local .install and .meta files, otherwise always from awesome github.
```bash
cd ~/dev/awesome-taskwarrior

# Should say "DEV mode"
./tw.py --debug --version

# Should use local files
./tw.py --list
./tw.py --info tw-recurrence
```

### 📝 Documentation Updates Needed

1. **README.md** - Update with new features:
   - Short flags
   - --debug with levels
   - --tags feature
   - --shell enhancements

2. **API.md** - Document:
   - RegistryManager class
   - Dev vs Production modes
   - GitHub fetching behavior

3. **CHANGES_tw.txt** - Already created, review and merge

### 🎯 Priority Order

1. **Critical** (breaks functionality): Fix the 7 AppManager methods above
2. **High** (usability): Add --available command ###NOTE### do the opposite of this. --available is deprecated, --list now shows installed and available, please clear out any references you see to --available
3. **Medium** (polish): Update documentation
4. **Low** (nice to have): Enhanced mode indicators

### 💡 Tips

- Test in production mode first (easier to see GitHub fetching work)
- Use --debug=2 to see what's happening
- temp files are automatically cleaned up (see RegistryManager.get_installer)
- The pattern is always: `self.registry.get_meta(app)` or `self.registry.get_installer(app)`

## Summary

You're 90% there! Just need to replace 7 method implementations to use RegistryManager instead of direct file access. The RegistryManager handles all the local vs GitHub logic automatically.
