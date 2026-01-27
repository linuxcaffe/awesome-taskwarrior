#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# fix-directory-paths.sh
# Update old ~/.task/hooks/priority/ references to new standard paths
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

msg() { echo -e "${BLUE}[fix-paths]${NC} $*"; }
success() { echo -e "${GREEN}[fix-paths] ✓${NC} $*"; }
error() { echo -e "${RED}[fix-paths] ✗${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[fix-paths] ⚠${NC} $*"; }

echo "============================================================================"
echo "fix-directory-paths.sh"
echo "Update directory paths to awesome-taskwarrior standard structure"
echo "============================================================================"
echo ""

msg "Scanning for files with old directory references..."

# Find Python files (excluding .orig backups and debug versions)
files_to_fix=()
for file in *.py nn; do
    if [ -f "$file" ] && [[ ! "$file" =~ \.orig$ ]] && [[ ! "$file" =~ ^debug\. ]]; then
        if grep -q "\.task/hooks/priority" "$file" 2>/dev/null; then
            files_to_fix+=("$file")
        fi
    fi
done

# Also check other Python executables without .py extension
for file in *; do
    # Skip if not a file
    [ -f "$file" ] || continue
    # Skip if has extension or is a backup/debug file
    [[ "$file" == *.* ]] && continue
    [[ "$file" =~ ^debug\. ]] && continue
    [[ "$file" =~ \.orig$ ]] && continue
    # Check if it's a Python file with old paths
    if head -1 "$file" 2>/dev/null | grep -q "python"; then
        if grep -q "\.task/hooks/priority" "$file" 2>/dev/null; then
            files_to_fix+=("$file")
        fi
    fi
done

if [ ${#files_to_fix[@]} -eq 0 ]; then
    success "No files found with old directory references"
    exit 0
fi

msg "Found ${#files_to_fix[@]} file(s) to fix:"
for file in "${files_to_fix[@]}"; do
    echo "  • $file"
done
echo ""

read -p "Proceed with fixes? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    msg "Aborted"
    exit 0
fi

echo ""
fixed=0

for file in "${files_to_fix[@]}"; do
    msg "Processing: $file"
    
    # Create backup
    cp "$file" "${file}.bak"
    
    # Fix HOOK_DIR variable definition
    if grep -q "HOOK_DIR = os.path.expanduser(\"~/.task/hooks/priority\")" "$file"; then
        sed -i 's|HOOK_DIR = os.path.expanduser("~/.task/hooks/priority")|TASK_DIR = os.path.expanduser("~/.task")|g' "$file"
        success "  Fixed HOOK_DIR → TASK_DIR"
    fi
    
    # Fix CONFIG_FILE path
    if grep -q "CONFIG_FILE = os.path.join(HOOK_DIR, \"need.rc\")" "$file"; then
        sed -i 's|CONFIG_FILE = os.path.join(HOOK_DIR, "need.rc")|CONFIG_FILE = os.path.join(TASK_DIR, "config", "need.rc")|g' "$file"
        success "  Fixed CONFIG_FILE path"
    fi
    
    # Fix LOG_DIR path
    if grep -q "LOG_DIR = os.path.join(HOOK_DIR, \"logs\")" "$file"; then
        sed -i 's|LOG_DIR = os.path.join(HOOK_DIR, "logs")|LOG_DIR = os.path.join(TASK_DIR, "logs", "need-priority")|g' "$file"
        success "  Fixed LOG_DIR path"
    fi
    
    # Fix LOG_FILE path (if it exists)
    if grep -q "LOG_FILE = os.path.join(LOG_DIR," "$file"; then
        # LOG_FILE is already relative to LOG_DIR, so it should be fine
        success "  LOG_FILE uses LOG_DIR (OK)"
    fi
    
    # Fix documentation in nn file
    if [ "$file" = "nn" ]; then
        # Fix the usage documentation
        if grep -q "~/.task/hooks/priority/nn.py" "$file"; then
            sed -i 's|~/.task/hooks/priority/nn.py|~/.task/scripts/nn|g' "$file"
            success "  Fixed documentation paths"
        fi
        
        # Update the NOTE section
        if grep -q "NOTE: Due to taskwarrior alias limitations" "$file"; then
            # This is more complex, so we'll provide guidance
            warn "  Manual update recommended for NOTE section"
            warn "  Suggest updating to describe ~/.task/scripts/nn location"
        fi
    fi
    
    ((fixed++))
    echo ""
done

echo "============================================================================"
success "Path fixes complete!"
echo "============================================================================"
echo ""
msg "Summary:"
echo "  • Fixed: $fixed files"
echo "  • Backups: *.bak"
echo ""

msg "Changes made:"
echo "  OLD: HOOK_DIR = os.path.expanduser(\"~/.task/hooks/priority\")"
echo "  NEW: TASK_DIR = os.path.expanduser(\"~/.task\")"
echo ""
echo "  OLD: CONFIG_FILE = os.path.join(HOOK_DIR, \"need.rc\")"
echo "  NEW: CONFIG_FILE = os.path.join(TASK_DIR, \"config\", \"need.rc\")"
echo ""
echo "  OLD: LOG_DIR = os.path.join(HOOK_DIR, \"logs\")"
echo "  NEW: LOG_DIR = os.path.join(TASK_DIR, \"logs\", \"need-priority\")"
echo ""

msg "Next steps:"
echo "  1. Review changes: diff nn nn.bak"
echo "  2. Test your hooks: tw add test +testpri"
echo "  3. If satisfied, remove backups: rm *.bak"
echo "  4. Run: make-awesome.sh --install"
echo "  5. Update and test installation"
echo ""

warn "NOTE: You may need to manually update the docstring in 'nn'"
warn "to reflect the new ~/.task/scripts/nn installation path"
echo ""
