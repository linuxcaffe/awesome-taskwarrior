# tw Tab Completion - Quick Start

**One command to enable tab completion!**

## Installation

Choose your shell and run ONE command:

```bash
# Bash users
tw --install-completion bash

# Zsh users
tw --install-completion zsh

# Fish users
tw --install-completion fish
```

That's it! tw will:
- ✓ Create the necessary directories
- ✓ Install the completion script
- ✓ Tell you what to add to your config file
- ✓ Show you how to activate it now

## What You'll See

### Bash Example

```bash
$ tw --install-completion bash
[tw] Wrote completion script to: ~/.bash_completion.d/tw.sh
[tw] Add this line to ~/.bashrc:
[tw]   source ~/.bash_completion.d/tw.sh
[tw] To activate now: source ~/.bash_completion.d/tw.sh
```

### Zsh Example

```bash
$ tw --install-completion zsh
[tw] Wrote completion script to: ~/.zsh/completion/_tw
[tw] Add these lines to ~/.zshrc:
[tw]   fpath=(~/.zsh/completion $fpath)
[tw]   autoload -Uz compinit && compinit
[tw] To activate now: exec zsh
```

### Fish Example

```bash
$ tw --install-completion fish
[tw] Wrote completion script to: ~/.config/fish/completions/tw.fish
[tw] Fish will auto-load completions on next shell start
[tw] To activate now: exec fish
```

## Follow the Instructions

After running the install command:

1. **Copy the line(s)** tw tells you to add to your config file
2. **Paste them** into your ~/.bashrc, ~/.zshrc, or leave them alone (fish)
3. **Activate** completions with the command tw shows you

## Try It Out

Once activated, try these:

```bash
tw --i<TAB>           # Completes to --install or --info
tw --install <TAB>    # Shows available apps
tw --remove <TAB>     # Shows installed apps
tw add +<TAB>         # Shows task tags (passes through to task)
```

## Troubleshooting

### Bash: "Command not found: tw"

Make sure ~/.task/scripts is in your PATH:

```bash
export PATH="$HOME/.task/scripts:$PATH"
# Add this to ~/.bashrc to make it permanent
```

### Completions not working after activation

1. Make sure you added the line(s) to your config file
2. Make sure you sourced the config or restarted your shell
3. Try: `complete -p tw` (bash) or `which _tw` (zsh) to verify

### Want to reinstall?

Just run the install command again:

```bash
tw --install-completion bash
```

It will overwrite the old completion script with the new one.

## Manual Installation

If you need more control (e.g., system-wide installation), use the manual approach:

```bash
tw --generate-completion bash > /usr/share/bash-completion/completions/tw
tw --generate-completion zsh > /usr/local/share/zsh/site-functions/_tw
tw --generate-completion fish > /usr/share/fish/vendor_completions.d/tw.fish
```

## More Information

For detailed documentation, see COMPLETION_README.md

For changes and technical details, see CHANGES_v2.2.0.txt

## Questions?

- **What gets completed?** tw flags, app names, help topics, and all task commands
- **Does it work with task completion?** Yes! Seamlessly passes through to task
- **Can I use both --install and --generate?** Yes! Use --install for easy setup, --generate for custom paths
- **Will it break my existing task completion?** No! It works alongside task's completion

## Enjoy!

Tab completion makes tw even faster and easier to use. Happy tasking!
