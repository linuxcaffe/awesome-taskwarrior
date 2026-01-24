#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# make-awesome-install.sh
# Generate installer and metadata for awesome-taskwarrior registry
# ============================================================================

SCRIPT_VERSION="1.0.0"

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
# Functions
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
                [ -f "$file" ] && HOOKS+=("$file:hook")
            done
        done
    done
    
    # Detect scripts (executable files not hooks)
    for ext in sh py; do
        for file in *.${ext}; do
            if [ -f "$file" ] && [ -x "$file" ]; then
                # Skip if it's a hook
                if [[ ! "$file" =~ ^on-(add|exit|modify) ]]; then
                    SCRIPTS+=("$file:script")
                fi
            fi
        done
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
# Compatible with awesome-taskwarrior v2.0.0
# ============================================================================

APPNAME="[APP_NAME]"
VERSION="[VERSION]"
BASE_URL="[BASE_URL]"

# Environment detection with defaults (works standalone or with tw.py)
: "${HOOKS_DIR:=$HOME/.task/hooks}"
: "${SCRIPTS_DIR:=$HOME/.task/scripts}"
: "${CONFIG_DIR:=$HOME/.task/config}"
: "${DOCS_DIR:=$HOME/.task/docs}"
: "${TASKRC:=$HOME/.taskrc}"

# Optional tw-common.sh sourcing (provides helpers but not required)
if [[ -f "${TW_COMMON:-}" ]]; then
    source "$TW_COMMON"
else
    # Fallback functions for standalone use
    tw_msg() { echo "[tw] $*"; }
    tw_success() { echo "[tw] ✓ $*"; }
    tw_error() { echo "[tw] ✗ $*" >&2; }
    tw_warn() { echo "[tw] ⚠ $*" >&2; }
fi

# Debug support - check for TW_DEBUG environment variable
if [[ "${TW_DEBUG:-0}" -gt 0 ]] || [[ "${DEBUG_HOOKS:-0}" == "1" ]]; then
    DEBUG_ENABLED=1
    DEBUG_LEVEL="${TW_DEBUG_LEVEL:-${TW_DEBUG:-1}}"
    DEBUG_LOG_DIR="${TW_DEBUG_LOG:-$HOME/.task/logs/debug}"
    DEBUG_LOG="${DEBUG_LOG_DIR}/[APP_NAME]_debug_$(date +%Y%m%d_%H%M%S).log"
    
    mkdir -p "$DEBUG_LOG_DIR"
    
    # Debug logging function
    debug_msg() {
        local level="${2:-1}"
        if [[ "$DEBUG_LEVEL" -ge "$level" ]]; then
            local timestamp=$(date +"%H:%M:%S.%N" | cut -c1-12)
            local msg="[debug] $timestamp | [APP_NAME] | $1"
            echo -e "\033[34m$msg\033[0m" >&2
            echo "$msg" >> "$DEBUG_LOG"
        fi
    }
    
    debug_msg "Debug enabled (level $DEBUG_LEVEL)" 1
    debug_msg "Log file: $DEBUG_LOG" 2
else
    DEBUG_ENABLED=0
    debug_msg() { :; }  # No-op when debug disabled
fi

# ============================================================================
# Installation Function
# ============================================================================

install() {
    tw_msg "Installing [APP_NAME] v$VERSION..."
    debug_msg "Starting installation" 1
    debug_msg "BASE_URL: $BASE_URL" 2
    debug_msg "HOOKS_DIR: $HOOKS_DIR" 2
    debug_msg "CONFIG_DIR: $CONFIG_DIR" 2
    
    # Create directories
    mkdir -p "$HOOKS_DIR" "$SCRIPTS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
    
EOF

    # Add download commands for each file type
    if [ ${#HOOKS[@]} -gt 0 ] || [ ${#SCRIPTS[@]} -gt 0 ]; then
        echo '    tw_msg "Downloading files..."' >> "${APP_NAME}.install"
        echo '    debug_msg "Downloading hooks and scripts" 2' >> "${APP_NAME}.install"
    fi
    
    # Add hooks downloads
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

show_summary() {
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

# ============================================================================
# Main
# ============================================================================

echo "============================================================================"
echo "make-awesome-install.sh v${SCRIPT_VERSION}"
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
show_summary

success "Done! Happy contributing to awesome-taskwarrior!"
