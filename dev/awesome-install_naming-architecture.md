# awesome-taskwarrior Naming & Installation Architecture

## Core Principle: NO NAME CHANGES EVER
**Files keep their exact names from project → installation → user's system**
This prevents foot-guns where manual installation breaks because users don't know about name transformations.

## Suffix System (Two Independent Markers)

### 1. Path Marker Suffixes
Used when files DON'T go to their "standard" location:
- `_hook.*` = File goes to hooks/ but isn't a hook itself (utility/library)
- `_script.*` = File goes to scripts/ but isn't a script
- `_config.*` = File goes to config/
- `_doc.*` = File goes to docs/

**Standard paths need NO marker:**
- `on-add_recurrence.py` → hooks/ (standard hook location) → chmod +x
- `my-utility.sh` → scripts/ (standard script location) → chmod +x

**Non-standard paths need marker:**
- `recurrence_common_hook.py` → hooks/ (library, not a hook) → needs `-x` marker too
- `README_doc.md` → docs/ (documentation)

### 2. Non-Executable Marker
Used to prevent chmod +x:
- `-x.*` suffix = Do NOT make executable

**Examples:**
- `recurrence_common_hook-x.py` → hooks/ directory, NOT executable (library)
- `utils_hook.sh` → hooks/ directory, IS executable (utility script)
- `on-add_recurrence.py` → hooks/ directory, IS executable (standard hook)

### 3. Combined Usage
Markers can be used together:
- `recurrence_common_hook-x.py` = Path marker (_hook) + Non-exec marker (-x)
  - Goes to: ~/.task/hooks/
  - Filename: recurrence_common_hook-x.py (unchanged!)
  - Permissions: NOT executable (library module)

## make-awesome.py --install Logic

### Current (WRONG) Implementation
❌ Strips suffixes during installation
❌ Changes filenames
❌ Creates foot-gun for manual installation

### Correct Implementation Needed
✓ NO filename changes at any point
✓ Check for `-x.*` suffix → skip chmod +x
✓ Path markers (_hook, _script, etc.) only determine destination directory
✓ Files keep exact same name in project and in user's ~/.task/

### Install Logic Flow
```python
for filename in files:
    # Determine destination based on type or _suffix
    if filename contains '_hook':
        dest_dir = hooks/
    elif filename contains '_script':
        dest_dir = scripts/
    # ... etc
    
    # Copy with SAME NAME
    copy(filename, f"{dest_dir}/{filename}")  # NO CHANGES!
    
    # Apply chmod only if NOT -x suffix
    if not filename.endswith('-x.py') and not filename.endswith('-x.sh'):
        chmod +x f"{dest_dir}/{filename}"
```

## Python Import Compatibility
Python can't import modules with dots in middle of name, so:
- ✓ `recurrence_common_hook.py` (underscores OK)
- ✓ `recurrence_common_hook-x.py` (dash before extension OK)
- ✗ `recurrence_common.hook.py` (dot before extension BREAKS imports)

Import statement: `from recurrence_common_hook import ...`
(Python strips the `-x` and extension automatically: `recurrence_common_hook-x.py` → `recurrence_common_hook`)

## Migration Notes
- Old system used `.hook.py`, `.script.sh` which broke Python imports
- New system uses `_hook.py` for path markers (import-friendly)
- Old system stripped markers during install (foot-gun)
- New system keeps ALL names unchanged (safe for manual install)

## Example File Naming

### Standard Hooks (no markers needed)
```
on-add_recurrence.py        → ~/.task/hooks/on-add_recurrence.py (chmod +x)
on-exit_recurrence.py       → ~/.task/hooks/on-exit_recurrence.py (chmod +x)
```

### Library in Hooks Dir (needs both markers)
```
recurrence_common_hook-x.py → ~/.task/hooks/recurrence_common_hook-x.py (no chmod)
```

### Utility Script in Hooks Dir (needs path marker only)
```
tw-debug_hook.sh            → ~/.task/hooks/tw-debug_hook.sh (chmod +x)
```

## Version History
- v4.2.3: Old system with `.hook.py` and suffix stripping
- v4.3.0: New system with `_hook` and `-x` markers, NO name changes (INCOMPLETE)
- v4.4.0: (Needed) Complete removal of name-changing logic

## TODO for v4.4.0
1. Remove ALL filename transformation logic
2. Keep files with exact same names throughout
3. Use `-x` suffix check for chmod logic only
4. Use `_hook/_script/_config/_doc` suffixes for directory routing only
5. Update tests to verify no name changes occur
