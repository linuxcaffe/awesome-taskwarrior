# tw.py Change Log

## Version 2.1.0 (2026-01-24)

### Added
- Short flags for all major commands:
  - `-I` for `--install`
  - `-i` for `--info`
  - `-r` for `--remove`
  - `-u` for `--update`
  - `-l` for `--list`
  - `-s` for `--shell`
  - `-h` for `--help`
  - `-v` for `--version`
- `--debug` feature with 3 levels (1-3):
  - DebugLogger class with session-based logging
  - Logs to `~/.task/logs/debug/tw_debug_TIMESTAMP.log`
  - Auto-cleanup (keeps last 10 sessions)
  - Sets `TW_DEBUG` environment variable for child processes
  - Color-coded output to stderr
- `--tags` feature for tag management:
  - List all tags with `tw --tags`
  - TagFilter class supporting `+tag` (include) and `-tag` (exclude) syntax
  - Tag filtering applies to `--list` and `--info`
  - Tags stored in `.meta` files and displayed in listings
- Enhanced `--info` command:
  - `tw --info` shows full info of all available apps (installed or not)
  - `tw --info app1 app2` shows info for specific apps
  - `tw --info +python` shows apps matching tag filter
  - Tag filtering support integrated
- Interactive shell (`--shell`) enhancements:
  - Trailing arguments support: `tw --shell add +work`
  - `:help shell` for detailed documentation
  - Empty input runs default report
  - Context-sensitive help system

### Changed
- Updated help system with topic-based detailed help:
  - `tw --help <topic>` for feature-specific documentation
  - Topics: shell, install, remove, verify, list, info
- Improved debug output throughout codebase
- Better error messages and user feedback

### Fixed
- Registry path resolution issues
- Tag filter parsing and application
- Shell prompt formatting edge cases

## Version 2.0.0

Initial curl-based architecture:
- Removed git-based operations
- Direct file placement via curl
- Per-file manifest tracking
- Added docs_dir for README files
- Self-contained installers
