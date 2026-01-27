#!/bin/bash
#
# verify-dev-mode.sh - Test if dev mode indicator is working
#
# Run this from your awesome-taskwarrior directory
#

echo "=== Dev Mode Indicator Verification ==="
echo

# Check if we're in the right directory
if [ ! -f "tw.py" ]; then
    echo "[ERROR] tw.py not found in current directory"
    echo "Please run this from your awesome-taskwarrior directory"
    exit 1
fi

# Check version
VERSION=$(grep "^VERSION = " tw.py | head -1 | cut -d'"' -f2)
echo "[check] tw.py version: $VERSION"

if [ "$VERSION" != "2.1.2" ]; then
    echo "[WARNING] Expected version 2.1.2, found $VERSION"
    echo "[WARNING] You may need to install the updated tw.py"
fi

# Check for dev mode function
if grep -q "show_dev_mode_if_needed" tw.py; then
    echo "[check] ✓ Dev mode function found in tw.py"
else
    echo "[check] ✗ Dev mode function NOT found in tw.py"
    echo "[ERROR] This version does not have dev mode indicator"
    exit 1
fi

# Check for registry.d and installers directories
if [ -d "registry.d" ] && [ -d "installers" ]; then
    echo "[check] ✓ Dev mode directories found (registry.d, installers)"
    echo "[check] → Dev mode SHOULD be active"
else
    echo "[check] ✗ Dev mode directories not found"
    echo "[check] → Dev mode will NOT activate"
fi

echo
echo "=== Testing Dev Mode ==="
echo

# Test with --version first
echo "$ ./tw.py --version"
./tw.py --version
echo

# Test with --list
echo "$ ./tw.py --list"
./tw.py --list
echo

echo "=== Expected Output ==="
echo "If dev mode is working, you should see:"
echo "  [tw] DEV MODE - using local registry: $(pwd)/registry.d"
echo "  [tw] Installed applications:"
echo "  ..."
