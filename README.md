# Development Models and Templates

This directory contains templates and reference implementations for awesome-taskwarrior components.

## Purpose

These files serve two purposes:
1. **Templates**: Starting points for creating new apps
2. **Reference**: Examples of proper implementation

## File Index

### Special Case: Taskwarrior Installation
- `taskwarrior.install` - Built-in Taskwarrior 2.6.2 installer

### Generic Templates
- `hook-template.meta` - Template for hook-based extensions
- `hook-template.install` - Template installer for hooks
- `wrapper-template.meta` - Template for wrapper applications
- `wrapper-template.install` - Template installer for wrappers

### Real-World Examples
- `tw-recurrence.meta` / `.install` - Complex hook example
- `tw-priority.meta` / `.install` - Hook with external dependencies
- `nicedates.meta` / `.install` - Wrapper example

### Configuration
- `tw.config.example` - Annotated configuration file

## Usage

### Creating a New Hook

1. Copy `hook-template.meta` to `registry.d/yourapp.meta`
2. Copy `hook-template.install` to `installers/yourapp.install`
3. Fill in the template sections
4. Test thoroughly
5. Submit to registry

### Creating a New Wrapper

1. Copy `wrapper-template.meta` to `registry.d/yourapp.meta`
2. Copy `wrapper-template.install` to `installers/yourapp.install`
3. Implement wrapper pass-through logic
4. Test with wrapper stack
5. Submit to registry

## Template Conventions

All templates use the following markers:

- `<PLACEHOLDER>` - Required field, replace with actual value
- `[OPTIONAL]` - Optional field, remove if not needed
- `# TODO:` - Action items for implementer
- `# NOTE:` - Important information
- `# EXAMPLE:` - Usage example

## Best Practices

1. **Read the template comments** - They contain important guidance
2. **Test installation and uninstallation** - Both must work cleanly
3. **Follow existing patterns** - Look at real examples for guidance
4. **Document dependencies** - Make them explicit in .meta files
5. **Handle errors gracefully** - Provide helpful error messages

## Reference Documentation

See `DEVELOPERS.md` for comprehensive architecture documentation.
See `API.md` for library function reference.
