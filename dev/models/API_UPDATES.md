# API.md Update Instructions

## Changes Needed for v1.3.0

### 1. Environment Variables Section (Line ~32-36)

**UPDATE** the environment variables list:

```bash
**Available Environment Variables:**
- `$INSTALL_DIR` - Base installation directory (default: `~/.task`)
- `$HOOKS_DIR` - Hook installation directory (default: `~/.task/hooks`)
- `$SCRIPTS_DIR` - Scripts/wrappers directory (default: `~/.task/scripts`)  # NEW
- `$CONFIG_DIR` - Configuration files directory (default: `~/.task/config`)  # NEW
- `$LOGS_DIR` - Logs directory (default: `~/.task/logs`)  # NEW
- `$TASKRC` - Path to .taskrc file (default: `~/.taskrc`)
- `$TW_DEBUG` - Debug flag (`0` or `1`)
```

### 2. ADD New Section: "Project Directory Management"

**INSERT** before "### Repository Management" section:

```markdown
### Project Directory Management

#### tw_get_install_dir
Get the correct installation directory based on app type.

**Syntax:**
```bash
tw_get_install_dir TYPE SHORT_NAME
```

**Parameters:**
- `TYPE` - App type: `hook`, `wrapper`, `utility`, or `config`
- `SHORT_NAME` - Short name for the app (e.g., `recurrence`)

**Returns:**
- Echoes the full path to installation directory
- Returns 1 on invalid type

**Example:**
```bash
install_dir=$(tw_get_install_dir hook recurrence)
# Returns: ~/.task/hooks/recurrence
```

#### tw_clone_to_project
Clone repository to the appropriate location based on app type.

**Syntax:**
```bash
tw_clone_to_project TYPE SHORT_NAME REPO_URL [BRANCH]
```

**Example:**
```bash
tw_clone_to_project hook recurrence "https://github.com/user/tw-recurrence_overhaul-hook"
# Clones to: ~/.task/hooks/recurrence/
```
```

### 3. UPDATE Hook Management Section

**REPLACE** tw_symlink_hook documentation:

```markdown
#### tw_symlink_hook
Create symlink for a hook in the hooks directory root.

**Syntax (v1.1.0+):**
```bash
tw_symlink_hook PROJECT_DIR HOOK_FILE
```

**Parameters:**
- `PROJECT_DIR` - Full path to project directory (e.g., `${HOOKS_DIR}/recurrence`)
- `HOOK_FILE` - Hook filename (e.g., `on-add_recurrence.py`)

**Example:**
```bash
local project_dir="${HOOKS_DIR}/recurrence"
tw_symlink_hook "$project_dir" "on-add_recurrence.py"

# Creates: ~/.task/hooks/on-add_recurrence.py -> ~/.task/hooks/recurrence/on-add_recurrence.py
```

**Migration from v1.0.0:**
```bash
# OLD:
tw_symlink_hook "${HOOKS_DIR}/${APPNAME}/on-add-test.py"

# NEW:
tw_symlink_hook "${HOOKS_DIR}/${SHORT_NAME}" "on-add-test.py"
```
```

### 4. ADD New Section: "Wrapper Management"

**INSERT** after Hook Management section:

```markdown
### Wrapper Management

#### tw_symlink_wrapper
Create symlink for a wrapper/utility script.

**Syntax:**
```bash
tw_symlink_wrapper PROJECT_DIR SCRIPT_FILE [LINK_NAME]
```

**Example:**
```bash
local project_dir="${SCRIPTS_DIR}/nicedates"
tw_symlink_wrapper "$project_dir" "nicedates.py" "nicedates"

# Creates: ~/.task/scripts/nicedates -> ~/.task/scripts/nicedates/nicedates.py
```

#### tw_remove_wrapper
Remove wrapper symlink from scripts directory.

**Syntax:**
```bash
tw_remove_wrapper LINK_NAME
```

**Example:**
```bash
tw_remove_wrapper "nicedates"
```
```

## Summary of Changes

- ✅ Added 3 new environment variables
- ✅ Added 2 new functions for project directory management
- ✅ Updated tw_symlink_hook signature (now takes 2 params)
- ✅ Added 2 new functions for wrapper management
- ✅ Added migration guide from v1.0.0 to v1.1.0+

Total new functions: 4
Updated functions: 1
