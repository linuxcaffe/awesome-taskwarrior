# awesome-taskwarrior

A curated collection of Taskwarrior extensions with a unified installation and management system.

## Overview

**awesome-taskwarrior** brings together the best Taskwarrior-related projects with `tw.py`, a universal wrapper that serves as both a transparent pass-through to Taskwarrior and a comprehensive package manager for extensions.

### Features

- 🎯 **One-Command Installation** - Install hooks, wrappers, and utilities with `tw --install <app>`
- 🔄 **Smart Wrapper System** - Stack multiple wrappers for enhanced Taskwarrior functionality
- 📦 **Dependency Management** - Automatic dependency checking and helpful error messages
- 🔍 **Version Tracking** - Keep extensions up-to-date with `tw --update`
- 🧪 **Built-in Testing** - Verify installations with `tw --check`
- 📚 **Comprehensive Documentation** - Templates and guides for developers

## Quick Start

### Install tw.py

```bash
# Clone repository
git clone https://github.com/linuxcaffe/awesome-taskwarrior.git
cd awesome-taskwarrior

# Add tw.py to your PATH
ln -s $(pwd)/tw.py ~/bin/tw
chmod +x tw.py

# Verify installation
tw --version
```

### Install Taskwarrior (if needed)

```bash
tw --install-taskwarrior
```

### Browse Available Extensions

```bash
tw --list
```

### Install an Extension

```bash
# Install advanced recurrence system
tw --install tw-recurrence

# Install priority management
tw --install tw-priority

# Install date parsing wrapper
tw --install nicedates
```

## Available Extensions

### Hooks

**Hooks** extend Taskwarrior by intercepting task events (add, modify, exit).

- **tw-recurrence** - Advanced recurrence beyond Taskwarrior's built-in system
  - Chained recurrence (completion-based spawning)
  - Periodic recurrence (time-based spawning)
  - Instance pile-up control
  
- **tw-priority** - Automatic priority management based on Maslow's hierarchy of needs
  - Context switching
  - Interactive review mode
  - Priority pyramid visualization

### Wrappers

**Wrappers** enhance task commands with additional syntax and features.

- **nicedates** - Human-readable date parsing
  - Natural language: "tomorrow", "next week", "in 3 days"
  - Improved date formatting in output

### Utilities

More extensions coming soon!

## Usage

### Normal Taskwarrior Commands

`tw.py` acts as a transparent pass-through:

```bash
tw next
tw add "Buy milk" due:tomorrow
tw list project:work
```

### Package Management

```bash
# List available extensions
tw --list
tw --list-installed

# Get detailed information
tw --info tw-recurrence

# Install/update/remove
tw --install tw-recurrence
tw --update tw-recurrence
tw --remove tw-recurrence

# Check for updates
tw --check
tw --update-all
```

### Wrapper Bridge

For wrappers that need special argument handling:

```bash
# Direct wrapper execution
nicedates add "Meeting" due:tomorrow

# Via tw.py
tw --exec nicedates add "Meeting" due:tomorrow

# Set default wrapper
tw --wrap nicedates
```

## Configuration

Create `~/.task/tw.config` to customize behavior:

```ini
[wrappers]
# Stack wrappers (applied in order)
stack=nicedates

[settings]
verbose=yes
auto_update=no
```

See `tw.config.example` for all available options.

## For Developers

### Adding Your Extension

1. Create `.meta` file in `registry.d/` (see `dev/models/` for templates)
2. Create `.install` script in `installers/`
3. Test thoroughly
4. Submit pull request

See [DEVELOPERS.md](DEVELOPERS.md) for comprehensive documentation.

### Templates and Examples

The `dev/models/` directory contains:
- **Templates** - Starting points for new extensions
  - `hook-template.meta` / `.install`
  - `wrapper-template.meta` / `.install`
  
- **Examples** - Real-world implementations
  - `tw-recurrence` (complex hook)
  - `tw-priority` (hook with utilities)
  - `nicedates` (wrapper)

### API Reference

See [dev/API.md](dev/API.md) for complete function reference for:
- `lib/tw-common.sh` - Bash library for installers
- `lib/tw-wrapper.py` - Python library for wrappers

## Design Philosophy

- **Unix Philosophy** - One tool does one thing well
- **Composability** - Extensions work together seamlessly
- **Independence** - Sub-projects maintain their own versioning
- **Transparency** - Minimal overhead, maximum clarity
- **Safety** - Always confirm before destructive operations

## Target Platform

- **Taskwarrior 2.6.2** and 2.x branch
- NOT compatible with Taskwarrior 3.x
- Well-made PRs for 3.x compatibility considered

## Project Structure

```
awesome-taskwarrior/
├── tw.py                      # Main wrapper/manager
├── tw.config.example          # Configuration template
├── registry.d/                # Extension metadata
├── installers/                # Installation scripts
├── lib/                       # Shared libraries
├── bin/                       # Optional pre-compiled binaries
├── installed/                 # Installation tracking
└── dev/                       # Development resources
    ├── models/               # Templates and examples
    ├── API.md                # Function reference
    └── DEVELOPERS.md         # Architecture guide
```

## Versioning

- **tw.py** - Semantic versioning (MAJOR.MINOR.PATCH)
- **Extensions** - Independent versioning schemes
- **Registry** - Git commits are canonical

## Contributing

Contributions welcome! Please:

1. Follow existing patterns and conventions
2. Test with Taskwarrior 2.6.2
3. Include comprehensive documentation
4. Provide working examples
5. Ensure clean uninstallation

See [DEVELOPERS.md](DEVELOPERS.md) for detailed guidelines.

## License

MIT License - see LICENSE file for details.

Individual extensions may have different licenses - check their repositories.

## Support

- **Issues** - Open an issue on GitHub
- **Questions** - Start a discussion
- **Documentation** - See DEVELOPERS.md and dev/API.md

## Acknowledgments

Built for the Taskwarrior community, standing on the shoulders of:
- Taskwarrior team for the excellent task management system
- All extension authors for their innovative work
- Contributors and testers who make this possible

## Related Projects

- [Taskwarrior](https://taskwarrior.org/) - The task management system
- [Timewarrior](https://timewarrior.net/) - Time tracking companion
- [Bugwarrior](https://github.com/ralphbean/bugwarrior) - Issue tracker integration

---

**awesome-taskwarrior** - Making Taskwarrior even more awesome, one extension at a time.
