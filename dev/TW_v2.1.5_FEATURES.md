# tw v2.1.5 - Three New Features!

## Summary
Added three powerful features to tw: automatic paging, file attachment via ranger, and shell command execution in interactive mode.

---

## Feature 1: -p / --pager (Automatic Paging)

### Overview
Automatically page long task output through `less` when it exceeds terminal height.

### Usage
```bash
tw -p <task command>
tw --pager <task command>
```

### Examples
```bash
# Page through all tasks
tw -p list

# Page through next actions
tw --pager next

# Page complex reports
tw -p status:pending list

# With other flags
tw --debug=2 -p list
```

### How It Works
1. Captures terminal dimensions
2. Runs task command and captures output
3. Counts output lines
4. If output exceeds screen height, invokes `less` with flags:
   - `-r` : Raw control characters (preserves colors)
   - `-X` : Don't clear screen on exit
   - `-F` : Auto-exit if content fits on one screen

### Smart Behavior
- **Short output**: Just prints directly (no pager invoked)
- **Long output**: Automatically opens in less
- **No pager**: Falls back to direct print if less/more not found

### Configuration (Future)
Could add to ~/.taskrc:
```
# Always use pager (future feature)
tw.pager=auto
```

---

## Feature 2: -A / --attach (File Attachment via Ranger)

### Overview
Attach files to tasks using the ranger file browser, creating annotations with file paths.

### Requirements
- **ranger** must be installed
- Check with: `which ranger`
- Install: 
  - Debian/Ubuntu: `sudo apt install ranger`
  - Arch: `sudo pacman -S ranger`
  - macOS: `brew install ranger`

### Usage
```bash
tw -A <taskid>
tw --attach <taskid>
```

### Interactive Flow
```bash
$ tw -A 42
[tw] Attaching to task 42: 'Fix bug in login system'
[tw] Type a label (or press Enter for none): Screenshot
[tw] Launching ranger... (press 'q' to cancel)

# Ranger opens, you navigate and select a file
# Press Enter to select, q to quit

[tw] ✓ Attached: Screenshot: /home/user/Pictures/bug-screenshot.png
```

### How It Works
1. Verifies ranger is installed
2. Gets task description for confirmation
3. Prompts for optional label
4. Launches ranger in file selection mode
5. Creates annotation: `label: /path/to/file` or just `/path/to/file`
6. Adds annotation to task

### Examples
```bash
# Attach with label
tw -A 42
# You select: /docs/spec.pdf
# Result: "Spec: /docs/spec.pdf"

# Attach without label (just press Enter at prompt)
tw -A 42
# You select: /home/user/todo.txt
# Result: "/home/user/todo.txt"

# View attachments
tw 42 info
# Shows all annotations including file paths
```

### Integration with taskopen
If you have taskopen installed, attached file paths work as links:
```bash
# Open all annotations for task 42
taskopen 42
```

### Error Handling
```bash
# Ranger not installed
$ tw -A 42
[tw] Error: ranger is not installed
[tw] Install ranger to use file attachment feature
...

# Invalid task ID
$ tw -A 999
[tw] Error: Could not find task 999

# Cancel during ranger
# Press 'q' in ranger or Ctrl+C
[tw] No file selected, attachment cancelled
```

---

## Feature 3: Shell exec/! Commands (Interactive Shell Enhancement)

### Overview
Execute any shell command directly from the tw interactive shell without exiting.

### Syntax
```bash
exec <command>     # Execute shell command
!<command>         # Same as exec
!!                 # Repeat last shell command
```

### Usage Examples

**Basic execution:**
```bash
tw> exec ls -la
total 48
drwxr-xr-x  4 user user  4096 Jan 29 12:00 .
...

tw> !pwd
/home/user/projects

tw> !cat notes.txt
TODO: Fix bug #42
TODO: Write documentation
```

**Repeat last command:**
```bash
tw> !date
Wed Jan 29 12:34:56 EST 2026

tw> !!
Wed Jan 29 12:34:58 EST 2026
```

**Complex commands:**
```bash
tw> exec grep -r "TODO" . | wc -l
23

tw> !find . -name "*.py" -type f
./tw
./make-awesome.py
./hooks/on-add.py
```

**Mix with task commands:**
```bash
tw> list +work
[task output showing work tasks]

tw> !grep "meeting" ~/.task/notes.txt
Budget meeting next Tuesday

tw> add Schedule budget meeting +work due:tuesday
Created task 45.

tw> !!
Budget meeting next Tuesday
```

### How It Works
1. Shell detects `exec ` or `!` prefix
2. Extracts command after prefix
3. Executes via `subprocess.run(shell=True)`
4. Returns to shell prompt after execution
5. `!!` retrieves last command from readline history

### Integration with Shell State
Shell commands are independent of task state:
```bash
tw> :push +work proj:foo
tw +work proj:foo> !ls
# Lists files (NOT affected by +work proj:foo)

tw +work proj:foo> list
# Lists tasks (IS affected by +work proj:foo)
```

### History
- Shell commands are saved to `~/.tw_shell_history`
- Use arrow keys to navigate
- `!!` uses readline history (not a separate shell history)

### Safety
- Shell commands run with your normal user permissions
- No commands are blocked (you have full shell access)
- Use with same caution as normal shell

---

## Combined Usage Examples

### Example 1: Attach and Review
```bash
# Attach a document
tw -A 42
# Select: /docs/proposal.pdf
# Label: Proposal

# View task with attachment
tw -p 42 info
# Pages through task info including the attachment

# Open in interactive shell
tw --shell
tw> 42 info
tw> exec evince /docs/proposal.pdf &
tw> 42 done
```

### Example 2: Research Workflow
```bash
tw --shell
tw> :push +research proj:thesis

# Search for papers
tw +research proj:thesis> !find ~/Papers -name "*.pdf" | grep quantum
~/Papers/quantum-computing-2025.pdf
~/Papers/quantum-algorithms.pdf

# Add tasks for papers
tw +research proj:thesis> add Read quantum computing paper due:friday
Created task 50.

# Attach the paper
tw +research proj:thesis> :q
$ tw -A 50
# Select: ~/Papers/quantum-computing-2025.pdf
# Label: Paper
```

### Example 3: Debug Session with Paging
```bash
# Long list needs paging
tw -p list status:pending

# In pager (less):
# - Use / to search
# - Use n for next match
# - Press q to exit

# Found interesting tasks, now work on them interactively
tw --shell
tw> :push status:pending +bug

# Check system logs while in shell
tw status:pending +bug> !tail -20 /var/log/syslog
[log output]

# Continue with tasks
tw status:pending +bug> 23 start
```

---

## Installation

```bash
# Copy new version
cp tw ~/.task/scripts/tw
chmod +x ~/.task/scripts/tw

# Verify version
tw --version
# Should show: tw v2.1.5

# Check features
tw --help | grep -A2 "Pager and Attach"
```

---

## Configuration Options (Future Ideas)

```taskrc
# Auto-enable pager for certain commands
tw.pager.auto=list,next,all

# Default ranger starting directory
tw.attach.start_dir=~/Documents

# Alternative file browser
tw.attach.browser=nnn

# Shell command history size
tw.shell.history_size=1000
```

---

## Feature Comparison

| Feature | tasksh | tw v2.1.5 |
|---------|--------|-----------|
| Interactive shell | ✅ | ✅ |
| Persistent modifiers | ✅ | ✅ |
| Shell commands (exec/!) | ✅ | ✅ NEW |
| Command history | ✅ | ✅ |
| Auto-paging | ❌ | ✅ NEW |
| File attachment UI | ❌ | ✅ NEW |
| HEAD/PREFIX state | ❌ | ✅ |
| Templates | ❌ | ✅ |

---

## Testing Guide

### Test Pager
```bash
# Should NOT page (short output)
tw -p version

# Should page (long output)
tw -p list all

# Test with colors
tw -p list status:pending

# Test without pager available (won't error)
PATH=/bin:/usr/bin tw -p list
```

### Test Attach
```bash
# Verify ranger
which ranger || echo "Need to install ranger"

# Test basic attach
tw add Test attachment task
tw -A <taskid>  # Use the created task ID

# Test with label
tw -A <taskid>
# Enter label: "Reference"

# Test cancel
tw -A <taskid>
# Press 'q' in ranger

# Verify annotation
tw <taskid> info | grep -A5 Annotations
```

### Test Shell Commands
```bash
tw --shell

# Test exec
tw> exec echo "Hello"

# Test !
tw> !date

# Test !!
tw> !ls
tw> !!

# Test with task commands
tw> list
tw> !pwd
tw> :q
```

---

## Known Issues

### Pager
- Terminal resize while in pager not handled
- Color support depends on terminal
- Less flags are fixed (not configurable yet)

### Attach
- Requires ranger (no fallback browser yet)
- No file type validation
- Large binary file paths work but may be unwieldy

### Shell Commands
- No shell command history separate from tw commands
- `!!` might conflict if last command was a task command
- Shell commands don't respect HEAD/PREFIX state

---

## Roadmap

**v2.1.6** (Potential features):
- Configuration file support for pager/attach options
- Alternative file browsers (nnn, lf, etc.)
- Pager command customization
- Shell command history isolation
- File type detection and icons

---

**tw v2.1.5** - Three powerful new features! 🎯
