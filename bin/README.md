# Taskwarrior Binaries

This directory contains pre-compiled Taskwarrior 2.6.2 binaries for various platforms.

## Purpose

The `tw --install-taskwarrior` command can install Taskwarrior from pre-compiled binaries stored here, providing the easiest installation method.

## Supported Platforms

Currently supported platforms (binaries to be added):

- Linux x86_64 (Ubuntu/Debian based)
- Linux ARM64
- macOS x86_64
- macOS ARM64 (Apple Silicon)

## Binary Naming Convention

Binaries should be named: `task-2.6.2-<platform>-<arch>`

Examples:
- `task-2.6.2-linux-x86_64`
- `task-2.6.2-linux-aarch64`
- `task-2.6.2-darwin-x86_64`
- `task-2.6.2-darwin-arm64`

## Building Binaries

To build Taskwarrior 2.6.2 for your platform:

```bash
# Download source
wget https://taskwarrior.org/download/task-2.6.2.tar.gz
tar xzf task-2.6.2.tar.gz
cd task-2.6.2

# Build
cmake -DCMAKE_BUILD_TYPE=Release .
make

# Binary is in: src/task
# Copy to this directory with appropriate name
```

## Verification

All binaries should include SHA256 checksums in `CHECKSUMS.txt`.

## Alternative Installation Methods

If no pre-compiled binary is available for your platform:

1. **System package manager**: `sudo apt install taskwarrior`
2. **Build from source**: See taskwarrior.install for automated build
3. **Download from taskwarrior.org**: https://taskwarrior.org/download/

## Note

These binaries are optional. The `tw --install-taskwarrior` command will:
1. First try to use pre-compiled binaries from this directory
2. Fall back to system package manager if version matches
3. Build from source as last resort

For most users, installing via system package manager is recommended if Taskwarrior 2.6.2 is available.
