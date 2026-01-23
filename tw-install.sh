#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# awesome-taskwarrior Bootstrap Installer
# ============================================================================

GITHUB_REPO="linuxcaffe/awesome-taskwarrior"
GITHUB_BRANCH="main"
RAW_BASE="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}"

echo "============================================================================"
echo "awesome-taskwarrior Bootstrap Installer"
echo "============================================================================"
echo ""

# Check if task is installed
if ! command -v task &> /dev/null; then
    echo "⚠ Warning: 'task' (Taskwarrior) not found in PATH"
    echo "  Please install Taskwarrior first: https://taskwarrior.org"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create directories
echo "Creating directories..."
mkdir -p ~/.task/scripts
mkdir -p ~/.task/docs
mkdir -p ~/.task/config

# Download tw.py
echo "Downloading tw.py..."
if curl -fsSL "${RAW_BASE}/tw.py" -o ~/.task/scripts/tw; then
    chmod +x ~/.task/scripts/tw
    echo "✓ Installed: ~/.task/scripts/tw"
else
    echo "✗ Failed to download tw.py"
    exit 1
fi

# Download README
echo "Downloading documentation..."
if curl -fsSL "${RAW_BASE}/README.md" -o ~/.task/docs/tw_README.md 2>/dev/null; then
    echo "✓ Documentation: ~/.task/docs/tw_README.md"
else
    echo "⚠ Could not download README (not critical)"
fi

# Check if ~/.task/scripts is in PATH
echo ""
if [[ ":$PATH:" == *":$HOME/.task/scripts:"* ]]; then
    echo "✓ ~/.task/scripts is already in your PATH"
else
    echo "⚠ ~/.task/scripts is NOT in your PATH"
    echo ""
    echo "Add it by running:"
    echo '  echo '\''export PATH="$HOME/.task/scripts:$PATH"'\'' >> ~/.bashrc'
    echo "  source ~/.bashrc"
    echo ""
    
    read -p "Add to ~/.bashrc now? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # Detect shell config file
        SHELL_CONFIG=""
        if [ -f ~/.bashrc ]; then
            SHELL_CONFIG=~/.bashrc
        elif [ -f ~/.zshrc ]; then
            SHELL_CONFIG=~/.zshrc
        elif [ -f ~/.profile ]; then
            SHELL_CONFIG=~/.profile
        fi
        
        if [ -n "$SHELL_CONFIG" ]; then
            echo '' >> "$SHELL_CONFIG"
            echo '# awesome-taskwarrior' >> "$SHELL_CONFIG"
            echo 'export PATH="$HOME/.task/scripts:$PATH"' >> "$SHELL_CONFIG"
            echo "✓ Added to $SHELL_CONFIG"
            echo ""
            echo "Run this to activate now:"
            echo "  source $SHELL_CONFIG"
        fi
    fi
fi

echo ""
echo "============================================================================"
echo "Installation complete!"
echo "============================================================================"
echo ""
echo "Getting started:"
echo "  1. Ensure ~/.task/scripts is in your PATH (see above)"
echo "  2. Run: tw --version"
echo "  3. Run: tw --list (to see available extensions)"
echo "  4. Run: tw --install <app-name> (to install extensions)"
echo ""
echo "Documentation:"
echo "  less ~/.task/docs/tw_README.md"
echo ""
echo "Self-update tw.py anytime with:"
echo "  tw --update tw"
echo ""
