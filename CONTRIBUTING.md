# Contributing to awesome-taskwarrior

Thank you for your interest in contributing! This guide helps you work effectively with the awesome-taskwarrior ecosystem, whether you're adding new extensions or improving existing ones.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Adding a New Extension](#adding-a-new-extension)
- [Working with Claude (AI Assistant)](#working-with-claude-ai-assistant)
- [Testing Your Extension](#testing-your-extension)
- [Submission Guidelines](#submission-guidelines)

## Getting Started

### Prerequisites

- Taskwarrior 2.6.2 (NOT 3.x)
- Python 3.6+ (for Python-based extensions)
- Git
- Bash

### Essential Reading

Before contributing, familiarize yourself with:

1. **[DEVELOPERS.md](DEVELOPERS.md)** - Complete architecture guide
2. **[dev/API.md](dev/API.md)** - Function reference for libraries
3. **[dev/models/](dev/models/)** - Templates and examples
4. **[README.md](README.md)** - User-facing documentation

## Project Structure

```
awesome-taskwarrior/
├── registry.d/          # Extension metadata (.meta files)
├── installers/          # Installation scripts (.install files)
├── lib/                 # Shared libraries
│   ├── tw-common.sh    # Bash functions for installers
│   └── tw-wrapper.py   # Python base class for wrappers
├── dev/
│   ├── models/         # Templates and examples
│   ├── API.md          # Function reference
│   └── DEVELOPERS.md   # Architecture guide
└── tw.py               # Main wrapper/package manager
```

## Adding a New Extension

### Step 1: Choose Your Template

Based on your extension type:

- **Hook** → Use `dev/models/hook-template.meta` and `.install`
- **Wrapper** → Use `dev/models/wrapper-template.meta` and `.install`

### Step 2: Create Metadata File

Create `registry.d/yourapp.meta`:

```ini
name=yourapp
short_desc=One-line description (max 80 chars)
version=1.0.0
repo=https://github.com/username/yourapp
type=hook
install_script=yourapp.install
author=your-username
wrapper=no

long_desc=Detailed description of functionality.
  Continuation lines must be indented with spaces.

requires=python3>=3.6,taskwarrior>=2.6.2

provides=on-add-yourapp.py,on-modify-yourapp.py

tags=hook,automation,productivity
```

**Required fields:**
- name, short_desc, version, repo, type, install_script

**Important:**
- Use lowercase with hyphens for names
- Tags should match existing taxonomy (see `tw --list tags`)
- Multi-line values must have indented continuations

### Step 3: Create Installer Script

Create `installers/yourapp.install`:

```bash
#!/bin/bash

APPNAME="yourapp"
REPO_URL="https://github.com/username/yourapp"

# Source common library
source "$(dirname "$0")/../lib/tw-common.sh"

install() {
    echo "Installing ${APPNAME}..."
    
    # Check dependencies
    tw_check_python_version 3.6 || return 1
    tw_check_taskwarrior_version 2.6.2 || return 1
    
    # Clone repository
    local target_dir="${HOOKS_DIR}/${APPNAME}"
    tw_clone_or_update "$REPO_URL" "$target_dir" || return 1
    
    # Install hooks
    tw_symlink_hook "${target_dir}/on-add-yourapp.py" || return 1
    
    # Add configuration
    tw_add_config "uda.yourapp.type=string"
    
    echo "✓ Installed ${APPNAME}"
    return 0
}

uninstall() {
    echo "Uninstalling ${APPNAME}..."
    
    tw_remove_hook "on-add-yourapp.py"
    tw_remove_config "uda.yourapp"
    rm -rf "${HOOKS_DIR}/${APPNAME}"
    
    echo "✓ Uninstalled ${APPNAME}"
    return 0
}

# Optional: test function
test() {
    echo "Testing ${APPNAME}..."
    tw_test_hook "on-add-yourapp.py" || return 1
    echo "✓ All tests passed"
    return 0
}

# Main entry point
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    : ${INSTALL_DIR:=~/.task}
    : ${HOOKS_DIR:=~/.task/hooks}
    : ${TASKRC:=~/.taskrc}
    : ${TW_DEBUG:=0}
    
    case "${1:-install}" in
        install) install ;;
        uninstall) uninstall ;;
        test) test ;;
        *)
            echo "Usage: $0 {install|uninstall|test}" >&2
            exit 1
            ;;
    esac
fi
```

**Required functions:**
- `install()` - Must return 0 on success
- `uninstall()` - Must clean up completely

**Best practices:**
- Use `tw-common.sh` library functions (see [dev/API.md](dev/API.md))
- Check dependencies before making changes
- Provide clear error messages
- Include `test()` function when possible
- Make script standalone executable for testing

### Step 4: Test Locally

```bash
# Test without installing
tw --dry-run --install yourapp

# Test in isolation
TW_TEST_ENV=1 bash installers/yourapp.install install

# Test with tw.py
tw --debug --install yourapp
tw --check yourapp  # If test() function exists
tw --remove yourapp
```

## Working with Claude (AI Assistant)

If you're using Claude (Anthropic's AI assistant) to help develop your extension, this project has been designed to work well with AI assistance.

### The Claude Project Knowledge Base

This repository includes a project knowledge base that Claude can reference. When working with Claude, mention:

```
This project has comprehensive documentation in the knowledge base including:
- DEVELOPERS.md (architecture and conventions)
- dev/API.md (function reference)
- dev/models/ (templates and examples)

Please reference these for awesome-taskwarrior conventions.
```

### Effective Prompting

#### Creating a New Extension

```
I'm adding [APP_NAME] to awesome-taskwarrior.

Project Context:
- Target: Taskwarrior 2.6.2 (NOT 3.x)
- Type: [hook/wrapper/utility]
- Current repo: [YOUR_REPO_URL]

Please create:
1. registry.d/[app-name].meta
2. installers/[app-name].install

Following the templates in dev/models/ and using tw-common.sh functions 
from dev/API.md.

Confirm you've reviewed the templates before generating.
```

#### Updating an Existing Installer

```
The [app-name] installer needs to [describe change].

Current installer is attached. Please update it following:
- The template in dev/models/hook-template.install
- Using tw-common.sh library functions (see dev/API.md)
- Maintaining the existing install/uninstall/test structure

Show only the changes needed, don't rewrite the whole file.
```

#### Debugging Installation Issues

```
tw --install [app-name] is failing with: [error message]

Debug output from: tw --debug --install [app-name]
[paste output]

The installer should use tw-common.sh functions. What's wrong and how do I fix it?
```

### Claude Best Practices

**DO:**
- ✅ Reference specific documentation files (DEVELOPERS.md, API.md)
- ✅ Mention which template applies (hook-template, wrapper-template)
- ✅ Request incremental changes for existing code
- ✅ Ask Claude to confirm understanding before generating
- ✅ Include relevant context (repo URL, app type, requirements)

**DON'T:**
- ❌ Assume Claude knows awesome-taskwarrior conventions without prompting
- ❌ Ask for Taskwarrior 3.x compatibility
- ❌ Request complete rewrites when small changes suffice
- ❌ Skip mentioning the project knowledge base

### Prompt Template Library

#### For Creating .meta Files

```
Create registry.d/[app-name].meta for my [hook/wrapper].

Repository: [URL]
Description: [brief description]
Dependencies: [list]
Type: [hook/wrapper/utility]

Follow the format in dev/models/[hook/wrapper]-template.meta.
All required fields must be present.
Use appropriate tags from: tw --list tags
```

#### For Creating Installers

```
Create installers/[app-name].install for my [type] extension.

Repository: [URL]
Provides: [list of files]
Dependencies: [list]

Requirements:
- Follow dev/models/[hook/wrapper]-template.install
- Use tw-common.sh functions (see dev/API.md)
- Include install(), uninstall(), and test() functions
- Handle [specific requirements]

The [hooks/wrapper] are located at: [path in repo]
```

#### For Adding Features

```
Add [feature] to [app-name].

Current code: [attach file]

Please:
- Maintain existing structure
- Use appropriate tw-common.sh functions
- Add error handling
- Update test() function if needed
- Follow awesome-taskwarrior conventions

Explain your approach before showing code changes.
```

### Working Session Tips

1. **Start with context**: Always mention you're working on awesome-taskwarrior
2. **Reference docs first**: Point Claude to DEVELOPERS.md and API.md
3. **Use templates**: Specify which template applies
4. **Test incrementally**: Ask for testable changes
5. **Request explanations**: Understand the approach before implementation

## Testing Your Extension

### Manual Testing

```bash
# Preview installation
tw --dry-run --install yourapp

# Install in test mode
TW_TEST_ENV=1 tw --install yourapp

# Run tests (if test() function exists)
tw --check yourapp

# Verify installation
tw --list-installed
ls -la ~/.task/hooks/

# Test functionality
task add "test task"  # Should trigger your hook

# Clean up
tw --remove yourapp
```

### Automated Testing

If your installer includes a `test()` function:

```bash
# Run installer's test suite
bash installers/yourapp.install test

# Or via tw.py
tw --check yourapp
```

### Test Checklist

- [ ] Installation succeeds without errors
- [ ] All hooks/files are created in correct locations
- [ ] Configuration is added to .taskrc correctly
- [ ] Dependencies are checked properly
- [ ] Uninstallation removes all traces
- [ ] Test function (if present) passes
- [ ] Works with Taskwarrior 2.6.2
- [ ] Dry-run shows accurate preview

## Submission Guidelines

### Before Submitting

1. **Test thoroughly**
   ```bash
   tw --dry-run --install yourapp
   tw --install yourapp
   tw --check yourapp
   tw --remove yourapp
   ```

2. **Verify files**
   - [ ] `registry.d/yourapp.meta` - All required fields present
   - [ ] `installers/yourapp.install` - Executable and tested
   - [ ] Both follow templates in `dev/models/`

3. **Check conventions**
   - [ ] Name uses lowercase with hyphens
   - [ ] Installer uses `tw-common.sh` functions
   - [ ] Error messages are helpful
   - [ ] Uninstall is clean and complete
   - [ ] Tags match existing taxonomy

4. **Documentation**
   - [ ] Repository has README with usage examples
   - [ ] Dependencies are documented
   - [ ] Installation requirements are clear

### Pull Request

Create a pull request with:

**Title:** `Add [app-name] - [one-line description]`

**Description:**
```markdown
## Extension Details
- Name: yourapp
- Type: hook/wrapper/utility
- Repository: [URL]

## What it does
[Brief description]

## Testing
- [ ] Tested installation with `tw --install yourapp`
- [ ] Tested uninstallation with `tw --remove yourapp`
- [ ] Tested with Taskwarrior 2.6.2
- [ ] Test function passes (if applicable)

## Files Added/Modified
- registry.d/yourapp.meta
- installers/yourapp.install

## Dependencies
[List any external dependencies]
```

### Review Process

Maintainers will check:
1. Follows awesome-taskwarrior conventions
2. Uses library functions appropriately
3. Installs and uninstalls cleanly
4. Works with Taskwarrior 2.6.2
5. Documentation is clear

## Code Style

### Bash Scripts

- Use `tw-common.sh` library functions
- Check return codes: `command || return 1`
- Quote variables: `"$VARIABLE"`
- Use `local` for function variables
- Provide debug output: `tw_debug "message"`

### Python Code

For wrappers, extend the base class:

```python
from tw_wrapper import TaskWrapper, main

class YourWrapper(TaskWrapper):
    def process_args(self, args):
        # Your logic here
        return modified_args

if __name__ == '__main__':
    main(YourWrapper)
```

### Metadata Files

- Use consistent formatting
- Indent continuation lines with spaces
- Keep short descriptions under 80 characters
- Use existing tags when possible

## Getting Help

- **Documentation:** See [DEVELOPERS.md](DEVELOPERS.md) and [dev/API.md](dev/API.md)
- **Examples:** Check [dev/models/](dev/models/) for working examples
- **Templates:** Use templates as starting points, not from scratch
- **Issues:** Open an issue for questions or clarifications
- **Discussions:** Use GitHub Discussions for design questions

## Version Control

### Commit Messages

Use clear, descriptive commit messages:

```
Add tw-yourapp to registry

- Create registry.d/tw-yourapp.meta
- Create installers/tw-yourapp.install
- Tested with Taskwarrior 2.6.2
```

### Branch Naming

- Feature: `feature/add-yourapp`
- Fix: `fix/yourapp-installation`
- Docs: `docs/improve-contributing`

## Compatibility

### Taskwarrior Version

- **Target:** 2.6.2 and 2.x branch
- **NOT compatible:** Taskwarrior 3.x
- **PRs for 3.x:** Considered but not guaranteed

### Python Version

- **Minimum:** Python 3.6
- **Recommended:** Python 3.8+

## Questions?

If you're unsure about anything:

1. Check [DEVELOPERS.md](DEVELOPERS.md) for architecture details
2. Look at [dev/models/](dev/models/) for examples
3. Review [dev/API.md](dev/API.md) for function reference
4. Open an issue for clarification
5. Start a discussion for design questions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to awesome-taskwarrior!** 🎉

Your extensions help make Taskwarrior even more powerful for the community.
