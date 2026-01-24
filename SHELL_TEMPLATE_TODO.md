# TODO: Implement Template System for tw --shell

## Summary
Add user-configurable templates for the interactive shell, stored in `~/.task/tw-templates.rc`

## Design Decisions (from session 2026-01-24)

**File Location:** `~/.task/tw-templates.rc`

**Format:**
```ini
# tw-shell Templates
# Format: template.name=modifiers
template.meeting=proj:meetings +work pri:M
template.bug=proj:bugs +work pri:H
template.urgent=+urgent pri:H due:tomorrow
```

## Implementation Tasks

### 1. Add template loading to TaskShell class

**In TaskShell.__init__():**
```python
self.templates = self._load_templates()  # Replace hardcoded dict
```

**Add new method:**
```python
def _load_templates(self):
    """Load templates from ~/.task/tw-templates.rc"""
    templates = {}
    template_file = Path.home() / ".task" / "tw-templates.rc"
    
    if template_file.exists():
        with open(template_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.startswith('template.'):
                        name = key[9:]  # Remove 'template.' prefix
                        templates[name] = shlex.split(value.strip())
    
    return templates
```

### 2. Create default template file if missing

**Add function:**
```python
def ensure_template_file():
    """Create template file with examples if it doesn't exist"""
    template_file = Path.home() / ".task" / "tw-templates.rc"
    
    if not template_file.exists():
        template_file.parent.mkdir(parents=True, exist_ok=True)
        default_content = """# tw-shell Templates
# Format: template.name=modifiers
# Usage: In tw --shell, type :tpl <name>

# Example templates:
template.meeting=proj:meetings +work pri:M
template.bug=proj:bugs +work pri:H
template.urgent=+urgent pri:H due:tomorrow
template.quick=+quick scheduled:now

# Add your own templates below:
"""
        template_file.write_text(default_content)
        return True
    return False
```

**Call in TaskShell.__init__():**
```python
def __init__(self, ...):
    # ...
    if ensure_template_file():
        print("Created template file: ~/.task/tw-templates.rc")
    self.templates = self._load_templates()
```

### 3. Enhance :tpl command in _handle_meta_command()

**Replace existing :tpl handling with:**
```python
elif cmd[0] == "tpl":
    if len(cmd) == 1 or (len(cmd) > 1 and cmd[1] == "list"):
        # :tpl or :tpl list - show available templates
        if self.templates:
            print("Available templates:")
            for name, mods in sorted(self.templates.items()):
                print(f"  {name}: {' '.join(mods)}")
        else:
            print("No templates defined.")
            print("Create/edit: ~/.task/tw-templates.rc")
    
    elif cmd[1] == "edit":
        # Open template file in editor
        editor = os.environ.get('EDITOR', 'vi')
        template_file = Path.home() / ".task" / "tw-templates.rc"
        ensure_template_file()  # Create if doesn't exist
        subprocess.run([editor, str(template_file)])
        self.templates = self._load_templates()  # Reload after edit
        print("Templates reloaded")
    
    elif cmd[1] == "reload":
        # Reload templates from file
        self.templates = self._load_templates()
        print(f"Reloaded {len(self.templates)} template(s)")
    
    else:
        # Apply template by name
        template_name = cmd[1]
        template = self.templates.get(template_name)
        if template:
            self.prefix_stack.extend(template)
        else:
            print(f"Unknown template: {template_name}")
            if self.templates:
                print(f"Available: {', '.join(sorted(self.templates.keys()))}")
            else:
                print("No templates defined. Use :tpl edit to create some.")
```

### 4. Update :help shell documentation

**Add template section to detailed help:**
```python
Templates:
  Built-in and custom templates provide quick modifier sets.
  Stored in: ~/.task/tw-templates.rc
  
  :tpl                  List available templates
  :tpl <name>           Apply template modifiers
  :tpl edit             Open template file in $EDITOR
  :tpl reload           Reload templates from file
  
  Example template file:
    template.meeting=proj:meetings +work pri:M
    template.urgent=+urgent pri:H due:tomorrow
```

### 5. Update help text in tw --help shell

**Add to the help output:**
```python
Templates:
  Create custom modifier sets in ~/.task/tw-templates.rc
  Format: template.name=modifiers
  Use: :tpl <name> in shell
```

## Testing Checklist

- [ ] Test with no template file (creates default)
- [ ] Test :tpl (shows list)
- [ ] Test :tpl <name> (applies template)
- [ ] Test :tpl edit (opens editor)
- [ ] Test :tpl reload (reloads without restart)
- [ ] Test invalid template names (shows error + available)
- [ ] Test with complex modifiers (quotes, special chars)
- [ ] Test :help shell shows template info

## Documentation Updates

1. **README.md** - Add template section
2. **QUICKSTART.md** - Add template example
3. **CHANGES_tw.txt** - Add to version notes

## Nice-to-Have Enhancements (Future)

- [ ] :tpl add <name> <modifiers> - Create template interactively
- [ ] :tpl del <name> - Delete template
- [ ] :tpl show <name> - Show what a template contains
- [ ] Template metadata (descriptions, categories)
- [ ] Share templates between users
- [ ] Import templates from URL

## Notes

- Uses shlex.split() to handle quoted values properly
- Reloads templates on :tpl edit for immediate feedback
- Follows taskwarrior .rc file conventions
- File location in ~/.task/ keeps everything in one place
- Simple format makes it easy to version control and share

## Related Files to Update

- tw.py (TaskShell class)
- CHANGES_tw.txt (add feature to changelog)
- README.md (document template feature)
- QUICKSTART.md (add template usage example)
