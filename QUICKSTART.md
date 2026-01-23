# awesome-taskwarrior Quick Start

## Installation

One command:
```bash
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/install.sh | bash
```

Or manually:
```bash
mkdir -p ~/.task/scripts ~/.task/docs ~/.task/config
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/tw.py -o ~/.task/scripts/tw
chmod +x ~/.task/scripts/tw
echo 'export PATH="$HOME/.task/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Basic Commands

```bash
# See what's available
tw --list

# Install an extension
tw --install tw-recurrence

# See what you've installed
tw --list

# Get details about an extension
tw --info tw-recurrence

# Update an extension
tw --update tw-recurrence

# Remove an extension
tw --remove tw-recurrence

# Update tw.py itself
tw --update tw

# Check versions
tw --version
```

## Your First Extension: tw-recurrence

```bash
# Install it
tw --install tw-recurrence

# Test it with a periodic task
task add "Take vitamins" r:1d due:tomorrow ty:p

# Test it with a chained task
task add "Exercise" r:3d due:today ty:c

# View your recurring templates
task rtemplates

# Read the docs
less ~/.task/docs/recurrence_README.md
```

## File Locations

Everything is in `~/.task/`:

```
~/.task/
├── config/
│   ├── .tw_manifest        # What's installed
│   └── *.rc                # Extension configs
├── scripts/
│   └── tw                  # Package manager
├── hooks/
│   └── *.py                # Hook scripts
└── docs/
    └── *_README.md         # Documentation
```

## Updating

Update any extension:
```bash
tw --update tw-recurrence
```

Update tw.py itself:
```bash
tw --update tw
```

## Getting Help

```bash
tw --help              # tw.py help
tw help                # Taskwarrior help
tw --info <app>        # Extension details
less ~/.task/docs/*    # Read docs
```

## Uninstalling

Remove an extension:
```bash
tw --remove tw-recurrence
```

Remove tw.py entirely:
```bash
rm ~/.task/scripts/tw ~/.task/config/.tw_manifest
# Remove PATH addition from ~/.bashrc if desired
```

## Tips

- `tw --list` shows installed (✓) and available (○) extensions
- Each extension has docs in `~/.task/docs/`
- The manifest tracks what's installed
- `tw` passes through to `task` for normal taskwarrior commands
  - `tw add "Buy milk"` = `task add "Buy milk"`
  - `tw list` would list installed apps (use `task list` for tasks)

## Troubleshooting

**"tw: command not found"**
```bash
echo 'export PATH="$HOME/.task/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Colors not showing**
Your terminal might not support ANSI colors, but functionality works the same.

**Extension won't install**
Check if it's available:
```bash
tw --list
```

Try dry-run to see what would happen:
```bash
tw --dry-run --install app-name
```

**Start fresh**
```bash
rm -rf ~/.task/scripts/tw ~/.task/config/.tw_manifest
curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash
```

## Next Steps

- Browse extensions: `tw --list`
- Read extension docs in `~/.task/docs/`
- Check GitHub: https://github.com/linuxcaffe/awesome-taskwarrior
- Create your own extension and submit it!
