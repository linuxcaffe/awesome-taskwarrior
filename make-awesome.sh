#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# make-awesome.sh
# Multi-purpose project setup tool for awesome-taskwarrior extensions
# ============================================================================

SCRIPT_VERSION="2.0.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

msg() { echo -e "${BLUE}[make]${NC} $*"; }
success() { echo -e "${GREEN}[make] ✓${NC} $*"; }
error() { echo -e "${RED}[make] ✗${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[make] ⚠${NC} $*"; }

# ============================================================================
# Usage
# ============================================================================

show_usage() {
    cat << EOF
make-awesome.sh v${SCRIPT_VERSION}
Multi-purpose project setup tool for awesome-taskwarrior extensions

Usage: make-awesome.sh [OPTIONS]

Options:
  --install    Generate installer and metadata for awesome-taskwarrior registry
  --debug      Create debug versions of Python files with logging infrastructure
  --test       Create starter test suite (NOT YET IMPLEMENTED)
  --help       Show this help message

Examples:
  make-awesome.sh --install    # Generate .install and .meta files
  make-awesome.sh --debug      # Create debug.* versions of Python files
  
EOF
}

# ============================================================================
# --install Functions (from make-awesome-install.sh)
# ============================================================================

detect_project_info() {
    msg "Detecting project information..."
    
    # Try to get project name from directory name
    PROJECT_NAME=$(basename "$PWD")
    
    # Try to detect version from files
    PROJECT_VERSION="1.0.0"
    if [ -f "VERSION" ]; then
        PROJECT_VERSION=$(cat VERSION | tr -d '[:space:]')
    elif [ -f "version.txt" ]; then
        PROJECT_VERSION=$(cat version.txt | tr -d '[:space:]')
    elif grep -q "^VERSION=" *.sh 2>/dev/null; then
        PROJECT_VERSION=$(grep "^VERSION=" *.sh | head -1 | cut -d'"' -f2)
    elif grep -q "^version=" *.py 2>/dev/null; then
        PROJECT_VERSION=$(grep "^version=" *.py | head -1 | cut -d'"' -f2 | cut -d"'" -f2)
    fi
    
    # Try to get GitHub repo
    if git remote -v &>/dev/null; then
        GITHUB_REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]\(.*\)\.git/\1/' | sed 's/.*github.com[:/]\(.*\)/\1/')
    else
        GITHUB_REPO=""
    fi
    
    success "Project: $PROJECT_NAME"
    success "Version: $PROJECT_VERSION"
    [ -n "$GITHUB_REPO" ] && success "GitHub: https://github.com/$GITHUB_REPO"
}

detect_files() {
    msg "Detecting project files..."
    
    HOOKS=()
    SCRIPTS=()
    CONFIGS=()
    DOCS=()
    
    # Detect hooks (on-add, on-exit, on-modify)
    for hook in on-add on-exit on-modify; do
        for ext in py sh; do
            for file in ${hook}*.${ext}; do
                # Skip debug.* and *.orig files
                [[ "$file" == debug.* ]] && continue
                [[ "$file" == *.orig ]] && continue
                [ -f "$file" ] && HOOKS+=("$file:hook")
            done
        done
    done
    
    # Detect scripts (executable files not hooks)
    for ext in sh py; do
        for file in *.${ext}; do
            # Skip debug.* and *.orig files
            [[ "$file" == debug.* ]] && continue
            [[ "$file" == *.orig ]] && continue
            
            if [ -f "$file" ] && [ -x "$file" ]; then
                # Skip if it's a hook
                if [[ ! "$file" =~ ^on-(add|exit|modify) ]]; then
                    SCRIPTS+=("$file:script")
                fi
            fi
        done
    done
    
    # Also detect executable Python files without extensions
    for file in *; do
        # Skip if not a regular file or not executable
        [ -f "$file" ] || continue
        [ -x "$file" ] || continue
        
        # Skip if has an extension (already handled)
        [[ "$file" == *.* ]] && continue
        
        # Skip debug.* and make-awesome.sh
        [[ "$file" == debug.* ]] && continue
        [[ "$file" == "make-awesome.sh" ]] && continue
        
        # Skip if it's a hook
        [[ "$file" =~ ^on-(add|exit|modify) ]] && continue
        
        # Check if it has a Python shebang
        if head -1 "$file" 2>/dev/null | grep -q "python"; then
            SCRIPTS+=("$file:script")
        fi
    done
    
    # Detect configs
    for ext in rc conf; do
        for file in *.${ext}; do
            [ -f "$file" ] && CONFIGS+=("$file:config")
        done
    done
    
    # Detect docs
    for file in README.md USAGE.md INSTALL.md; do
        [ -f "$file" ] && DOCS+=("$file:doc")
    done
    
    # Report
    [ ${#HOOKS[@]} -gt 0 ] && success "Hooks: ${HOOKS[*]}"
    [ ${#SCRIPTS[@]} -gt 0 ] && success "Scripts: ${SCRIPTS[*]}"
    [ ${#CONFIGS[@]} -gt 0 ] && success "Configs: ${CONFIGS[*]}"
    [ ${#DOCS[@]} -gt 0 ] && success "Docs: ${DOCS[*]}"
    
    ALL_FILES=("${HOOKS[@]}" "${SCRIPTS[@]}" "${CONFIGS[@]}" "${DOCS[@]}")
    
    if [ ${#ALL_FILES[@]} -eq 0 ]; then
        error "No files detected! Make sure you have hooks, scripts, configs, or docs."
        exit 1
    fi
}

prompt_for_info() {
    msg "Gathering metadata..."
    echo ""
    
    # App name
    read -p "App name [$PROJECT_NAME]: " input
    APP_NAME=${input:-$PROJECT_NAME}
    
    # Version
    read -p "Version [$PROJECT_VERSION]: " input
    VERSION=${input:-$PROJECT_VERSION}
    
    # Type
    echo "Type: (1) hook, (2) script, (3) config, (4) theme"
    read -p "Select [1]: " input
    case ${input:-1} in
        1) TYPE="hook" ;;
        2) TYPE="script" ;;
        3) TYPE="config" ;;
        4) TYPE="theme" ;;
        *) TYPE="hook" ;;
    esac
    
    # Description
    read -p "Short description: " DESCRIPTION
    
    # GitHub repo
    if [ -n "$GITHUB_REPO" ]; then
        read -p "GitHub repo [$GITHUB_REPO]: " input
        REPO=${input:-$GITHUB_REPO}
    else
        read -p "GitHub repo (user/repo): " REPO
    fi
    
    # Author
    GIT_AUTHOR=$(git config user.name 2>/dev/null || echo "")
    read -p "Author [$GIT_AUTHOR]: " input
    AUTHOR=${input:-$GIT_AUTHOR}
    
    # License
    read -p "License [MIT]: " input
    LICENSE=${input:-MIT}
    
    # Requirements
    read -p "Requires Taskwarrior version [2.6.0]: " input
    REQ_TW=${input:-2.6.0}
    
    read -p "Requires Python version (leave blank if N/A): " REQ_PY
    
    # Tags
    echo ""
    msg "Tags help users find your extension"
    echo "Examples: hook, script, priority, recurrence, gtd, python, bash, stable, beta"
    echo "Suggested tags for your extension:"
    
    # Auto-suggest tags based on detected files
    SUGGESTED_TAGS=()
    [ ${#HOOKS[@]} -gt 0 ] && SUGGESTED_TAGS+=("hook")
    [ ${#SCRIPTS[@]} -gt 0 ] && SUGGESTED_TAGS+=("script")
    
    # Detect language
    if ls *.py 2>/dev/null | grep -q .; then
        SUGGESTED_TAGS+=("python")
    fi
    if ls *.sh 2>/dev/null | grep -q .; then
        SUGGESTED_TAGS+=("bash")
    fi
    
    # Show suggestions
    if [ ${#SUGGESTED_TAGS[@]} -gt 0 ]; then
        echo "  - ${SUGGESTED_TAGS[*]}"
    fi
    
    echo ""
    read -p "Tags (comma-separated): " TAGS_INPUT
    
    # Convert to comma-separated, lowercase, no spaces
    TAGS=$(echo "$TAGS_INPUT" | tr '[:upper:]' '[:lower:]' | tr -s ',' | tr -d ' ')
    
    echo ""
}

calculate_checksums() {
    msg "Calculating SHA256 checksums..."
    
    CHECKSUMS=()
    for item in "${ALL_FILES[@]}"; do
        file=$(echo "$item" | cut -d':' -f1)
        if [ -f "$file" ]; then
            checksum=$(sha256sum "$file" | cut -d' ' -f1)
            CHECKSUMS+=("$checksum")
            success "$file: $checksum"
        fi
    done
}

generate_meta_file() {
    msg "Generating ${APP_NAME}.meta..."
    
    # Build files list
    FILES_LIST=""
    for item in "${ALL_FILES[@]}"; do
        [ -n "$FILES_LIST" ] && FILES_LIST+=","
        FILES_LIST+="$item"
    done
    
    # Build checksums list
    CHECKSUMS_LIST=""
    for checksum in "${CHECKSUMS[@]}"; do
        [ -n "$CHECKSUMS_LIST" ] && CHECKSUMS_LIST+=","
        CHECKSUMS_LIST+="$checksum"
    done
    
    # Generate base_url
    BASE_URL="https://raw.githubusercontent.com/${REPO}/main/"
    REPO_URL="https://github.com/${REPO}"
    
    # Create meta file
    cat > "${APP_NAME}.meta" <<EOF
# ${APP_NAME}.meta
# ${DESCRIPTION}
# Version: ${VERSION}

name=${APP_NAME}
version=${VERSION}
type=${TYPE}
description=${DESCRIPTION}
repo=${REPO_URL}
base_url=${BASE_URL}
files=${FILES_LIST}
tags=${TAGS}

# Checksums (SHA256)
checksums=${CHECKSUMS_LIST}

# Additional metadata
author=${AUTHOR}
license=${LICENSE}
requires_taskwarrior=${REQ_TW}
EOF

    # Add Python requirement if specified
    if [ -n "$REQ_PY" ]; then
        echo "requires_python=${REQ_PY}" >> "${APP_NAME}.meta"
    fi
    
    success "Created ${APP_NAME}.meta"
}

generate_installer() {
    msg "Generating ${APP_NAME}.install..."
    
    # Start installer
    cat > "${APP_NAME}.install" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# [APP_NAME] - Installer Script
# Version: [VERSION]
# Generated by make-awesome.sh
# ============================================================================

VERSION="[VERSION]"
APPNAME="[APP_NAME]"
BASE_URL="[BASE_URL]"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

tw_msg() { echo -e "${BLUE}[tw]${NC} $*"; }
tw_success() { echo -e "${GREEN}[tw] ✓${NC} $*"; }
tw_error() { echo -e "${RED}[tw] ✗${NC} $*" >&2; }

# Debug support
DEBUG_LEVEL="${TW_DEBUG:-0}"
debug_msg() {
    local msg="$1"
    local level="${2:-1}"
    if [[ $DEBUG_LEVEL -ge $level ]]; then
        echo -e "${BLUE}[DEBUG-$level]${NC} $msg" >&2
    fi
}

debug_msg "Starting installer with DEBUG_LEVEL=$DEBUG_LEVEL" 1

# Directories
HOME="${HOME:-$(eval echo ~$USER)}"
TASKRC="${HOME}/.taskrc"
TASK_DIR="${HOME}/.task"
HOOKS_DIR="${TASK_DIR}/hooks"
SCRIPTS_DIR="${TASK_DIR}/scripts"
CONFIG_DIR="${TASK_DIR}/config"
DOCS_DIR="${TASK_DIR}/docs"

# ============================================================================
# Installation Function
# ============================================================================

install() {
    tw_msg "Installing [APP_NAME] v$VERSION..."
    debug_msg "Starting installation" 1
    
    # Create directories
    tw_msg "Creating directories..."
    mkdir -p "$HOOKS_DIR" "$SCRIPTS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
    debug_msg "Directories created" 2
    
    tw_msg "Downloading files..."
    debug_msg "Using BASE_URL: $BASE_URL" 2
    
EOF

    # Add hook downloads
    for item in "${HOOKS[@]}"; do
        file=$(echo "$item" | cut -d':' -f1)
        cat >> "${APP_NAME}.install" <<EOF
    debug_msg "Downloading hook: $file" 2
    curl -fsSL "\$BASE_URL/$file" -o "\$HOOKS_DIR/$file" || {
        tw_error "Failed to download $file"
        debug_msg "Download failed: $file" 1
        return 1
    }
    chmod +x "\$HOOKS_DIR/$file"
    debug_msg "Installed hook: \$HOOKS_DIR/$file" 2
EOF
    done
    
    # Add scripts downloads
    for item in "${SCRIPTS[@]}"; do
        file=$(echo "$item" | cut -d':' -f1)
        cat >> "${APP_NAME}.install" <<EOF
    debug_msg "Downloading script: $file" 2
    curl -fsSL "\$BASE_URL/$file" -o "\$SCRIPTS_DIR/$file" || {
        tw_error "Failed to download $file"
        debug_msg "Download failed: $file" 1
        return 1
    }
    chmod +x "\$SCRIPTS_DIR/$file"
    debug_msg "Installed script: \$SCRIPTS_DIR/$file" 2
EOF
    done
    
    # Add config downloads
    for item in "${CONFIGS[@]}"; do
        file=$(echo "$item" | cut -d':' -f1)
        cat >> "${APP_NAME}.install" <<EOF
    debug_msg "Downloading config: $file" 2
    curl -fsSL "\$BASE_URL/$file" -o "\$CONFIG_DIR/$file" || {
        tw_error "Failed to download $file"
        debug_msg "Download failed: $file" 1
        return 1
    }
    debug_msg "Installed config: \$CONFIG_DIR/$file" 2
EOF
    done
    
    # Add config to .taskrc if needed
    if [ ${#CONFIGS[@]} -gt 0 ]; then
        first_config=$(echo "${CONFIGS[0]}" | cut -d':' -f1)
        cat >> "${APP_NAME}.install" <<'EOF'
    
    # Add config to .taskrc
    tw_msg "Adding configuration to .taskrc..."
    local config_line="include $CONFIG_DIR/[FIRST_CONFIG]"
    
    if ! grep -qF "$config_line" "$TASKRC" 2>/dev/null; then
        echo "$config_line" >> "$TASKRC"
        tw_msg "Added config include to .taskrc"
    else
        tw_msg "Config already in .taskrc"
    fi
EOF
        sed -i "s/\[FIRST_CONFIG\]/$first_config/" "${APP_NAME}.install"
    fi
    
    # Add docs downloads
    for item in "${DOCS[@]}"; do
        file=$(echo "$item" | cut -d':' -f1)
        docname="${APP_NAME}_${file}"
        cat >> "${APP_NAME}.install" <<EOF
    
    tw_msg "Downloading documentation..."
    curl -fsSL "\$BASE_URL/$file" -o "\$DOCS_DIR/$docname" 2>/dev/null || true
EOF
    done
    
    # Add manifest tracking
    cat >> "${APP_NAME}.install" <<'EOF'
    
    # Track in manifest
    debug_msg "Writing to manifest" 2
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    mkdir -p "$(dirname "$MANIFEST_FILE")"
    
EOF

    # Add manifest entries for each file
    for item in "${ALL_FILES[@]}"; do
        file=$(echo "$item" | cut -d':' -f1)
        type=$(echo "$item" | cut -d':' -f2)
        
        case $type in
            hook)   dir="\$HOOKS_DIR" ;;
            script) dir="\$SCRIPTS_DIR" ;;
            config) dir="\$CONFIG_DIR" ;;
            doc)    dir="\$DOCS_DIR"; file="${APP_NAME}_${file}" ;;
        esac
        
        echo "    echo \"\$APPNAME|\$VERSION|$dir/$file||\$TIMESTAMP\" >> \"\$MANIFEST_FILE\"" >> "${APP_NAME}.install"
        echo "    debug_msg \"Manifest entry: $dir/$file\" 3" >> "${APP_NAME}.install"
    done
    
    # Finish install function
    cat >> "${APP_NAME}.install" <<'EOF'
    
    debug_msg "Installation complete" 1
    tw_success "Installed [APP_NAME] v$VERSION"
    echo ""
    tw_msg "Documentation: $DOCS_DIR/[APP_NAME]_README.md"
    echo ""
    
    return 0
}

# ============================================================================
# Removal Function
# ============================================================================

remove() {
    tw_msg "Removing [APP_NAME]..."
    debug_msg "Starting removal" 1
    
    tw_msg "Removing files..."
    debug_msg "Removing installed files" 2
EOF

    # Add file removal commands
    for item in "${ALL_FILES[@]}"; do
        file=$(echo "$item" | cut -d':' -f1)
        type=$(echo "$item" | cut -d':' -f2)
        
        case $type in
            hook)   dir="\$HOOKS_DIR" ;;
            script) dir="\$SCRIPTS_DIR" ;;
            config) dir="\$CONFIG_DIR" ;;
            doc)    dir="\$DOCS_DIR"; file="${APP_NAME}_${file}" ;;
        esac
        
        echo "    rm -f \"$dir/$file\"" >> "${APP_NAME}.install"
        echo "    debug_msg \"Removed: $dir/$file\" 2" >> "${APP_NAME}.install"
    done
    
    # Remove config from .taskrc if needed
    if [ ${#CONFIGS[@]} -gt 0 ]; then
        first_config=$(echo "${CONFIGS[0]}" | cut -d':' -f1)
        cat >> "${APP_NAME}.install" <<'EOF'
    
    # Remove config line from .taskrc
    tw_msg "Removing configuration from .taskrc..."
    if [[ -f "$TASKRC" ]]; then
        local config_line="include $CONFIG_DIR/[FIRST_CONFIG]"
        grep -vF "$config_line" "$TASKRC" > "$TASKRC.tmp" 2>/dev/null || true
        mv "$TASKRC.tmp" "$TASKRC"
    fi
EOF
        sed -i "s/\[FIRST_CONFIG\]/$first_config/" "${APP_NAME}.install"
    fi
    
    # Finish remove function
    cat >> "${APP_NAME}.install" <<'EOF'
    
    # Remove from manifest
    debug_msg "Removing from manifest" 2
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    if [[ -f "$MANIFEST_FILE" ]]; then
        grep -v "^$APPNAME|" "$MANIFEST_FILE" > "$MANIFEST_FILE.tmp" 2>/dev/null || true
        mv "$MANIFEST_FILE.tmp" "$MANIFEST_FILE"
        debug_msg "Manifest updated" 2
    fi
    
    debug_msg "Removal complete" 1
    tw_success "Removed [APP_NAME]"
    echo ""
    
    return 0
}

# ============================================================================
# Main Entry Point
# ============================================================================

case "${1:-}" in
    install)
        install
        ;;
    remove)
        remove
        ;;
    *)
        cat << 'EOFHELP'
[APP_NAME] - Installer
Usage: ./[APP_NAME].install {install|remove}

This installer is self-contained and can run standalone.
It also integrates with awesome-taskwarrior (tw.py) if available.

For more information:
  [REPO_URL]
EOFHELP
        exit 1
        ;;
esac
EOF

    # Replace placeholders
    sed -i "s/\[APP_NAME\]/$APP_NAME/g" "${APP_NAME}.install"
    sed -i "s/\[VERSION\]/$VERSION/g" "${APP_NAME}.install"
    sed -i "s|\[BASE_URL\]|$BASE_URL|g" "${APP_NAME}.install"
    sed -i "s|\[REPO_URL\]|$REPO_URL|g" "${APP_NAME}.install"
    
    chmod +x "${APP_NAME}.install"
    
    success "Created ${APP_NAME}.install"
}

show_install_summary() {
    echo ""
    echo "============================================================================"
    success "Package created successfully!"
    echo "============================================================================"
    echo ""
    msg "Generated files:"
    echo "  • ${APP_NAME}.meta"
    echo "  • ${APP_NAME}.install"
    echo ""
    msg "Next steps:"
    echo "  1. Test the installer:"
    echo "     ./${APP_NAME}.install install"
    echo ""
    echo "  2. Fork awesome-taskwarrior:"
    echo "     https://github.com/linuxcaffe/awesome-taskwarrior/fork"
    echo ""
    echo "  3. Clone your fork and add files:"
    echo "     git clone https://github.com/YOUR_USERNAME/awesome-taskwarrior.git"
    echo "     cd awesome-taskwarrior"
    echo "     cp /path/to/${APP_NAME}.meta registry.d/"
    echo "     cp /path/to/${APP_NAME}.install installers/"
    echo ""
    echo "  4. Commit and create PR:"
    echo "     git add registry.d/${APP_NAME}.meta installers/${APP_NAME}.install"
    echo "     git commit -m \"Add ${APP_NAME} v${VERSION}\""
    echo "     git push origin main"
    echo "     # Then create PR on GitHub"
    echo ""
    msg "Files to include in PR:"
    echo "  • registry.d/${APP_NAME}.meta"
    echo "  • installers/${APP_NAME}.install"
    echo ""
}

run_install_mode() {
    echo "============================================================================"
    echo "make-awesome.sh v${SCRIPT_VERSION} --install"
    echo "Generate installer and metadata for awesome-taskwarrior"
    echo "============================================================================"
    echo ""
    
    # Check if in a git repo (recommended but not required)
    if ! git status &>/dev/null; then
        warn "Not in a git repository. Some auto-detection may not work."
        warn "Consider initializing: git init"
        echo ""
    fi
    
    detect_project_info
    detect_files
    prompt_for_info
    calculate_checksums
    generate_meta_file
    generate_installer
    show_install_summary
    
    success "Done! Happy contributing to awesome-taskwarrior!"
}

# ============================================================================
# --debug Functions
# ============================================================================

generate_debug_boilerplate() {
    local original_file="$1"
    local debug_file="$2"
    
    msg "Creating debug version: $debug_file"
    
    # Use Python to properly parse the file and generate debug version
    python3 - "$original_file" "$debug_file" << 'EOFPYTHON'
import sys
import os

original_file = sys.argv[1]
debug_file = sys.argv[2]
script_name = os.path.basename(original_file)

# Read original file
with open(original_file, 'r') as f:
    lines = f.readlines()

# Parse components
shebang = ""
docstring_lines = []
import_lines = []
rest_lines = []

in_docstring = False
docstring_delimiter = None
after_shebang = False
in_imports = False
docstring_found = False  # Track if we've already found the module docstring

for i, line in enumerate(lines):
    # Handle shebang
    if line.startswith('#!') and not after_shebang:
        shebang = line
        after_shebang = True
        continue
    
    # Handle module-level docstring (only the FIRST one, right after shebang/comments)
    if not docstring_found and not in_docstring and (line.strip().startswith('"""') or line.strip().startswith("'''")):
        # Check if this looks like a function docstring (indented or follows 'def')
        if i > 0 and ('def ' in lines[i-1] or 'class ' in lines[i-1]):
            # This is a function/class docstring, treat as rest
            rest_lines.append(line)
            continue
        
        # This is the module docstring
        in_docstring = True
        docstring_delimiter = '"""' if '"""' in line else "'''"
        docstring_lines.append(line)
        # Check if docstring ends on same line
        if line.strip().count(docstring_delimiter) >= 2:
            in_docstring = False
            docstring_found = True
        continue
    
    if in_docstring:
        docstring_lines.append(line)
        if docstring_delimiter in line:
            in_docstring = False
            docstring_found = True
        continue
    
    # After module docstring, collect imports
    if line.startswith('import ') or line.startswith('from '):
        import_lines.append(line)
        in_imports = True
        continue
    
    # Blank lines and comments after shebang/docstring but before imports
    if not docstring_found and (line.strip() == '' or line.strip().startswith('#')):
        continue
    
    # Blank lines after imports still count as import section
    if in_imports and line.strip() == '':
        continue
    
    # Everything else is rest
    if in_imports and not (line.startswith('import ') or line.startswith('from ') or line.strip() == ''):
        in_imports = False
    
    if not in_imports:
        rest_lines.append(line)

# Generate debug file
with open(debug_file, 'w') as f:
    # Write shebang
    if shebang:
        f.write(shebang)
        if not shebang.endswith('\n'):
            f.write('\n')
    
    # Write docstring
    if docstring_lines:
        for line in docstring_lines:
            f.write(line)
    
    # Write debug header
    f.write(f"""
# ============================================================================
# DEBUG VERSION - Auto-generated by make-awesome.sh --debug
# ============================================================================

import os
import sys
from pathlib import Path
from datetime import datetime

# Debug configuration
DEBUG_MODE = 0  # Set to 1 to enable debug output

# Check if running under tw --debug
tw_debug_level = os.environ.get('TW_DEBUG', '0')
try:
    tw_debug_level = int(tw_debug_level)
except ValueError:
    tw_debug_level = 0

debug_active = DEBUG_MODE == 1 or tw_debug_level > 0

# Determine log directory based on context
def get_log_dir():
    \"\"\"Auto-detect dev vs production mode\"\"\"
    cwd = Path.cwd()
    
    # Dev mode: running from project directory (has .git)
    if (cwd / '.git').exists():
        log_dir = cwd / 'logs' / 'debug'
    else:
        # Production mode: installed and triggered by tw --debug
        log_dir = Path.home() / '.task' / 'logs' / 'debug'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

# Initialize debug logger
if debug_active:
    DEBUG_LOG_DIR = get_log_dir()
    DEBUG_SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
    DEBUG_LOG_FILE = DEBUG_LOG_DIR / f"{script_name}_debug_{{DEBUG_SESSION_ID}}.log"
    
    def debug_log(message, level=1):
        \"\"\"Write debug message to log file and stderr\"\"\"
        if debug_active and (DEBUG_MODE == 1 or tw_debug_level >= level):
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            prefix = f"[DEBUG-{{level}}]"
            log_line = f"{{timestamp}} {{prefix}} {{message}}\\n"
            
            # Write to file
            with open(DEBUG_LOG_FILE, 'a') as f:
                f.write(log_line)
            
            # Write to stderr with color
            print(f"\\033[34m{{prefix}}\\033[0m {{message}}", file=sys.stderr)
    
    # Initialize log file
    with open(DEBUG_LOG_FILE, 'w') as f:
        f.write("=" * 70 + "\\n")
        f.write(f"Debug Session - {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}\\n")
        f.write(f"Script: {script_name}\\n")
        f.write(f"Debug Mode: {{DEBUG_MODE}}\\n")
        f.write(f"TW_DEBUG Level: {{tw_debug_level}}\\n")
        f.write(f"Session ID: {{DEBUG_SESSION_ID}}\\n")
        f.write("=" * 70 + "\\n\\n")
    
    debug_log(f"Debug logging initialized: {{DEBUG_LOG_FILE}}", 1)
else:
    def debug_log(message, level=1):
        \"\"\"No-op when debug is disabled\"\"\"
        pass

""")
    
    # Write original imports (excluding duplicates of what we added)
    skip_imports = {'os', 'sys', 'pathlib', 'datetime'}
    for line in import_lines:
        # Check if this is a duplicate import
        is_duplicate = False
        for skip in skip_imports:
            if f'import {skip}' in line or f'from {skip} ' in line:
                is_duplicate = True
                break
        if not is_duplicate:
            f.write(line)
    
    # Write separator and rest of code
    f.write("""
# ============================================================================
# Original Code Below
# ============================================================================

""")
    
    for line in rest_lines:
        f.write(line)

print(f"DEBUG: Parsed {len(lines)} lines", file=sys.stderr)
print(f"DEBUG: Shebang: {'yes' if shebang else 'no'}", file=sys.stderr)
print(f"DEBUG: Docstring: {len(docstring_lines)} lines", file=sys.stderr)
print(f"DEBUG: Imports: {len(import_lines)} lines", file=sys.stderr)
print(f"DEBUG: Rest: {len(rest_lines)} lines", file=sys.stderr)

EOFPYTHON
    
    # Make executable
    chmod +x "$debug_file"
    
    success "Created: $debug_file"
}

check_tw_envar_compatibility() {
    local file="$1"
    
    # Check if file contains TW_DEBUG environment variable check
    if grep -q "TW_DEBUG" "$file" 2>/dev/null; then
        return 0  # Compatible
    else
        return 1  # Not compatible
    fi
}

run_debug_mode() {
    echo "============================================================================"
    echo "make-awesome.sh v${SCRIPT_VERSION} --debug"
    echo "Create debug versions of Python files"
    echo "============================================================================"
    echo ""
    
    # Set up logging for this debug generation session
    local log_dir="./logs/debug"
    mkdir -p "$log_dir"
    local session_id=$(date +"%Y%m%d_%H%M%S")
    local log_file="${log_dir}/make-awesome_debug_${session_id}.log"
    
    # Write session header to log
    {
        echo "========================================================================"
        echo "make-awesome.sh v${SCRIPT_VERSION} --debug Session - $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Session ID: ${session_id}"
        echo "========================================================================"
        echo ""
    } > "$log_file"
    
    msg "Scanning for Python files in current directory..."
    echo "[$(date '+%H:%M:%S')] [v${SCRIPT_VERSION}] Scanning for Python files in current directory..." >> "$log_file"
    
    local python_files=()
    
    # Find .py files
    for file in *.py; do
        if [ -f "$file" ]; then
            python_files+=("$file")
        fi
    done
    
    # Find executable files without extension that have Python shebangs
    for file in *; do
        # Skip if not a regular file or not executable
        [ -f "$file" ] || continue
        [ -x "$file" ] || continue
        
        # Skip if has .py extension (already handled)
        [[ "$file" == *.py ]] && continue
        
        # Skip if has other common extensions
        [[ "$file" == *.sh ]] && continue
        [[ "$file" == *.install ]] && continue
        [[ "$file" == *.md ]] && continue
        [[ "$file" == *.txt ]] && continue
        [[ "$file" == *.rc ]] && continue
        [[ "$file" == *.conf ]] && continue
        
        # Skip make-awesome.sh itself
        [[ "$file" == "make-awesome.sh" ]] && continue
        
        # Check if it has a Python shebang
        if head -1 "$file" 2>/dev/null | grep -q "python"; then
            python_files+=("$file")
        fi
    done
    
    if [ ${#python_files[@]} -eq 0 ]; then
        warn "No Python files found in current directory"
        echo "[$(date '+%H:%M:%S')] No Python files found" >> "$log_file"
        exit 0
    fi
    
    success "Found ${#python_files[@]} Python file(s)"
    echo "[$(date '+%H:%M:%S')] [v${SCRIPT_VERSION}] Found ${#python_files[@]} Python file(s): ${python_files[*]}" >> "$log_file"
    echo ""
    
    for pyfile in "${python_files[@]}"; do
        debug_name="debug.${pyfile}"
        
        echo "[$(date '+%H:%M:%S')] [v${SCRIPT_VERSION}] Processing: $pyfile" >> "$log_file"
        
        # Check if original file already has debug infrastructure (avoid duplication)
        if grep -q "# DEBUG VERSION - Auto-generated by make-awesome.sh --debug" "$pyfile" 2>/dev/null; then
            warn "File already has debug infrastructure, skipping: $pyfile"
            echo "[$(date '+%H:%M:%S')] [v${SCRIPT_VERSION}]   File already has debug infrastructure, skipping: $pyfile" >> "$log_file"
            continue
        fi
        
        # Generate debug version (capture stderr to log file, strip color codes)
        echo "[$(date '+%H:%M:%S')] [v${SCRIPT_VERSION}]   Generating debug version..." >> "$log_file"
        generate_debug_boilerplate "$pyfile" "$debug_name" 2>&1 | tee >(sed 's/\x1b\[[0-9;]*m//g' >> "$log_file") | grep -v "^DEBUG:" || true
        
        # Backup original to .orig and promote debug version
        if [ -f "$debug_name" ]; then
            backup_name="${pyfile}.orig"
            
            # Check if backup already exists
            if [ -f "$backup_name" ]; then
                msg "Backup exists, keeping: $backup_name"
                echo "[$(date '+%H:%M:%S')] [v${SCRIPT_VERSION}]   Backup already exists: $backup_name" >> "$log_file"
            else
                msg "Backing up: $pyfile -> $backup_name"
                echo "[$(date '+%H:%M:%S')] [v${SCRIPT_VERSION}]   Backing up: $pyfile -> $backup_name" >> "$log_file"
                cp "$pyfile" "$backup_name"
                success "Backed up: $backup_name"
            fi
            
            # Promote debug version to original name
            msg "Promoting: $debug_name -> $pyfile"
            echo "[$(date '+%H:%M:%S')] [v${SCRIPT_VERSION}]   Promoting: $debug_name -> $pyfile" >> "$log_file"
            mv "$debug_name" "$pyfile"
            success "Promoted: $pyfile (debug-enhanced)"
        fi
    done
    
    echo ""
    echo "============================================================================"
    success "Debug versions created!"
    echo "============================================================================"
    echo ""
    msg "Debug files created in current directory with 'debug.' prefix"
    msg "To use:"
    echo "  1. Set DEBUG_MODE=1 in the debug file, or"
    echo "  2. Run with: tw --debug [command]"
    echo ""
    msg "Logs will be written to:"
    echo "  • Dev mode (in project):    ./logs/debug/"
    echo "  • Production mode:          ~/.task/logs/debug/"
    echo ""
    msg "Debug generation log: $log_file"
    echo ""
    
    # Write session footer to log
    {
        echo ""
        echo "========================================================================"
        echo "Session completed: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================================================"
    } >> "$log_file"
}

# ============================================================================
# --test Functions
# ============================================================================

run_test_mode() {
    echo "============================================================================"
    echo "make-awesome.sh v${SCRIPT_VERSION} --test"
    echo "Create starter test suite"
    echo "============================================================================"
    echo ""
    
    error "NOT YET IMPLEMENTED"
    error "The --test mode will be available once the test architecture is finalized"
    echo ""
    exit 1
}

# ============================================================================
# Main Entry Point
# ============================================================================

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

case "${1:-}" in
    --install)
        run_install_mode
        ;;
    --debug)
        run_debug_mode
        ;;
    --test)
        run_test_mode
        ;;
    --help|-h)
        show_usage
        exit 0
        ;;
    *)
        error "Unknown option: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
