#!/usr/bin/env python3
"""
make-awesome.py - Complete development-to-deployment pipeline for awesome-taskwarrior

This tool provides a full workflow from development through deployment:
- --debug:    Enhance with debug infrastructure (tw --debug=2 compatible)
- --testing:  Run test suite [STUB]
- --timing:   Inject TW_TIMING timing block (tw --timing compatible)
- --stdhelp:  Standardise help output [STUB]
- --meta:     Generate .meta registry entry only
- --install:  Generate .install (and .meta if run standalone)
- --push:     Git commit/push + registry update

Pipeline order: debug → testing → timing → stdhelp → meta → install → push

Single command: make-awesome.py "commit message"  — runs full pipeline
Flag combo:     make-awesome.py --meta --push "msg"  — runs selected stages in order

Version: 4.9.0
"""

import sys
import os
import re
import argparse
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional

VERSION = "4.10.2"

# Mode detection
# Fleet mode  — running from the awesome-taskwarrior dir (where awesome.rc lives)
# Project mode — running from any other project directory
SCRIPT_DIR     = Path(__file__).resolve().parent
IS_FLEET_MODE  = Path.cwd() == SCRIPT_DIR

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def msg(text):
    print(f"{Colors.BLUE}[make]{Colors.NC} {text}")

def success(text):
    print(f"{Colors.GREEN}[make] [OK]{Colors.NC} {text}")

def error(text):
    print(f"{Colors.RED}[make] [FAIL]{Colors.NC} {text}", file=sys.stderr)

def warn(text):
    print(f"{Colors.YELLOW}[make] [WARN]{Colors.NC} {text}")


# ============================================================================
# DEBUG Enhancement (Smart pattern-aware enhancement from v3.0.0)
# ============================================================================

class DebugPattern:
    """Represents detected debug patterns in existing code"""
    def __init__(self):
        self.has_debug_var = False
        self.debug_var_name = None
        self.debug_var_value = None
        self.has_debug_function = False
        self.debug_function_name = None
        self.has_tw_debug_check = False
        self.path_constants = []


class PythonFileAnalyzer:
    """Analyzes Python files to detect existing patterns"""
    
    @staticmethod
    def analyze(filepath: str) -> DebugPattern:
        """Analyze a Python file for existing debug patterns"""
        pattern = DebugPattern()
        
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Detect debug variables
        debug_var_patterns = [
            r'^\s*DEBUG\s*=\s*(\d+)',
            r'^\s*DEBUG_MODE\s*=\s*(\d+)',
            r'^\s*debug\s*=\s*(\d+)',
        ]
        
        for line in lines:
            for pattern_str in debug_var_patterns:
                match = re.match(pattern_str, line)
                if match:
                    pattern.has_debug_var = True
                    var_match = re.match(r'^\s*(\w+)\s*=', line)
                    if var_match:
                        pattern.debug_var_name = var_match.group(1)
                        pattern.debug_var_value = match.group(1)
                    break
        
        # Detect debug functions
        debug_func_patterns = [
            r'^\s*def\s+(debug_print|debug_log|log_debug|print_debug)\s*\(',
        ]
        
        for line in lines:
            for pattern_str in debug_func_patterns:
                match = re.match(pattern_str, line)
                if match:
                    pattern.has_debug_function = True
                    pattern.debug_function_name = match.group(1)
                    break
        
        # Detect TW_DEBUG
        if 'TW_DEBUG' in content:
            pattern.has_tw_debug_check = True
        
        # Detect path constants
        path_patterns = [
            r'^\s*([A-Z_]+(?:DIR|PATH|FILE))\s*=\s*(.+)$',
        ]
        
        for line in lines:
            for pattern_str in path_patterns:
                match = re.match(pattern_str, line)
                if match:
                    const_name = match.group(1)
                    const_value = match.group(2).strip()
                    pattern.path_constants.append((const_name, const_value))
        
        return pattern


class PythonFileParser:
    """Parses Python file structure"""
    
    @staticmethod
    def parse(filepath: str) -> Dict[str, any]:
        """Parse Python file into structural components"""
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        result = {
            'shebang': None,
            'docstring': [],
            'imports': [],
            'rest': [],
            'all_lines': lines,
        }
        
        idx = 0
        
        # Extract shebang
        if lines and lines[0].startswith('#!'):
            result['shebang'] = lines[0]
            idx = 1
        
        # Skip blank lines
        while idx < len(lines) and lines[idx].strip() == '':
            idx += 1
        
        # Extract docstring
        if idx < len(lines) and lines[idx].strip().startswith('"""'):
            result['docstring'].append(lines[idx])
            idx += 1
            
            # Multi-line docstring
            if not lines[idx - 1].strip().endswith('"""') or lines[idx - 1].strip().count('"""') == 1:
                while idx < len(lines):
                    result['docstring'].append(lines[idx])
                    if '"""' in lines[idx]:
                        idx += 1
                        break
                    idx += 1
        
        # Skip blank lines
        while idx < len(lines) and lines[idx].strip() == '':
            idx += 1
        
        # Extract imports
        while idx < len(lines):
            line = lines[idx].strip()
            
            if line and not line.startswith('import ') and not line.startswith('from ') and not line.startswith('#'):
                break
            
            if line.startswith('import ') or line.startswith('from ') or line == '' or line.startswith('#'):
                result['imports'].append(lines[idx])
                idx += 1
            else:
                break
        
        # Rest
        result['rest'] = lines[idx:]
        
        return result


class DebugEnhancer:
    """Enhances Python files with debug infrastructure"""
    
    @staticmethod
    def enhance_existing_debug(pattern: DebugPattern, parsed: Dict) -> List[str]:
        """Enhance existing debug code"""
        enhanced = []
        
        # Shebang and docstring
        if parsed['shebang']:
            enhanced.append(parsed['shebang'])
        
        for line in parsed['docstring']:
            enhanced.append(line)
        
        enhanced.append('\n')
        enhanced.append('# ============================================================================\n')
        enhanced.append('# DEBUG ENHANCED VERSION - Auto-generated by make-awesome.py\n')
        enhanced.append('# ============================================================================\n')
        enhanced.append('\n')
        
        # Add imports together
        enhanced.append('import os\n')
        enhanced.append('import sys\n')
        enhanced.append('from pathlib import Path\n')
        enhanced.append('from datetime import datetime\n')
        
        # Add original imports (skip duplicates)
        skip_imports = {'os', 'sys', 'pathlib', 'datetime'}
        for line in parsed['imports']:
            is_duplicate = False
            for skip in skip_imports:
                stripped = line.strip()
                if (stripped == f'import {skip}'
                        or stripped.startswith(f'from {skip} ')
                        or stripped.startswith(f'from {skip}.')):
                    is_duplicate = True
                    break
            if not is_duplicate and line.strip():
                enhanced.append(line)
        
        enhanced.append('\n')
        
        # Add TW_DEBUG support
        enhanced.append('# ============================================================================\n')
        enhanced.append('# Enhanced Debug Infrastructure\n')
        enhanced.append('# ============================================================================\n')
        enhanced.append('\n')
        
        if not pattern.has_tw_debug_check:
            enhanced.append('# Check if running under tw --debug\n')
            enhanced.append("tw_debug_level = os.environ.get('TW_DEBUG', '0')\n")
            enhanced.append('try:\n')
            enhanced.append('    tw_debug_level = int(tw_debug_level)\n')
            enhanced.append('except ValueError:\n')
            enhanced.append('    tw_debug_level = 0\n')
            enhanced.append('\n')
        
        # Add log directory detection
        enhanced.append('# Determine log directory\n')
        enhanced.append('def get_log_dir():\n')
        enhanced.append('    """Log dir respects TW_TASK_DIR for dev/test isolation."""\n')
        enhanced.append("    import os as _os\n")
        enhanced.append("    task_dir = Path(_os.environ.get('TW_TASK_DIR', str(Path.home() / '.task')))\n")
        enhanced.append("    log_dir = task_dir / 'logs' / 'debug'\n")
        enhanced.append('    log_dir.mkdir(parents=True, exist_ok=True)\n')
        enhanced.append('    return log_dir\n')
        enhanced.append('\n')
        
        # Original code
        enhanced.append('# ============================================================================\n')
        enhanced.append('# Original Code with Debug Enhancements\n')
        enhanced.append('# ============================================================================\n')
        enhanced.append('\n')
        
        for line in parsed['rest']:
            enhanced.append(line)
        
        # Add wrapper
        if pattern.has_debug_function:
            enhanced.append('\n')
            enhanced.append('# ============================================================================\n')
            enhanced.append('# Enhanced Debug Logging Wrapper\n')
            enhanced.append('# ============================================================================\n')
            enhanced.append('\n')
            enhanced.append(f'_original_{pattern.debug_function_name} = {pattern.debug_function_name}\n')
            enhanced.append('\n')
            enhanced.append(f'if {pattern.debug_var_name} or tw_debug_level >= 2:\n')
            enhanced.append('    DEBUG_LOG_DIR = get_log_dir()\n')
            enhanced.append('    DEBUG_SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")\n')
            enhanced.append('    try:\n')
            enhanced.append('        script_name = Path(__file__).stem\n')
            enhanced.append('    except:\n')
            enhanced.append('        script_name = Path(sys.argv[0]).stem if sys.argv else "script"\n')
            enhanced.append('    DEBUG_LOG_FILE = DEBUG_LOG_DIR / f"{script_name}_debug_{DEBUG_SESSION_ID}.log"\n')
            enhanced.append('    \n')
            enhanced.append(f'    def {pattern.debug_function_name}(msg):\n')
            enhanced.append('        """Enhanced debug with file logging"""\n')
            enhanced.append(f'        if {pattern.debug_var_name} or tw_debug_level >= 2:\n')
            enhanced.append('            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]\n')
            enhanced.append('            log_line = f"{timestamp} [DEBUG] {msg}\\n"\n')
            enhanced.append('            with open(DEBUG_LOG_FILE, "a") as f:\n')
            enhanced.append('                f.write(log_line)\n')
            enhanced.append(f'            _original_{pattern.debug_function_name}(msg)\n')
            enhanced.append('    \n')
            enhanced.append('    with open(DEBUG_LOG_FILE, "w") as f:\n')
            enhanced.append('        f.write("=" * 70 + "\\n")\n')
            enhanced.append('        f.write(f"Debug Session - {datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}\\n")\n')
            enhanced.append('        f.write(f"Script: {script_name}\\n")\n')
            enhanced.append(f'        f.write(f"{pattern.debug_var_name}: {{{pattern.debug_var_name}}}\\n")\n')
            enhanced.append('        f.write(f"TW_DEBUG Level: {tw_debug_level}\\n")\n')
            enhanced.append('        f.write(f"Session ID: {DEBUG_SESSION_ID}\\n")\n')
            enhanced.append('        f.write("=" * 70 + "\\n\\n")\n')
            enhanced.append('    \n')
            enhanced.append(f'    {pattern.debug_function_name}("Debug logging initialized")\n')
        
        return enhanced
    
    @staticmethod
    def add_new_debug(parsed: Dict) -> List[str]:
        """Add new debug infrastructure"""
        enhanced = []
        
        if parsed['shebang']:
            enhanced.append(parsed['shebang'])
        
        for line in parsed['docstring']:
            enhanced.append(line)
        
        enhanced.append('\n')
        enhanced.append('# ============================================================================\n')
        enhanced.append('# DEBUG VERSION - Auto-generated by make-awesome.py\n')
        enhanced.append('# ============================================================================\n')
        enhanced.append('\n')
        
        # Imports
        enhanced.append('import os\n')
        enhanced.append('import sys\n')
        enhanced.append('from pathlib import Path\n')
        enhanced.append('from datetime import datetime\n')
        
        skip_imports = {'os', 'sys', 'pathlib', 'datetime'}
        for line in parsed['imports']:
            is_duplicate = False
            for skip in skip_imports:
                stripped = line.strip()
                if (stripped == f'import {skip}'
                        or stripped.startswith(f'from {skip} ')
                        or stripped.startswith(f'from {skip}.')):
                    is_duplicate = True
                    break
            if not is_duplicate and line.strip():
                enhanced.append(line)
        
        enhanced.append('\n')
        enhanced.append('# Debug configuration (default 0, triggered by tw --debug=2)\n')
        enhanced.append('DEBUG_MODE = 0\n')
        enhanced.append('\n')
        enhanced.append("tw_debug_level = os.environ.get('TW_DEBUG', '0')\n")
        enhanced.append('try:\n')
        enhanced.append('    tw_debug_level = int(tw_debug_level)\n')
        enhanced.append('except ValueError:\n')
        enhanced.append('    tw_debug_level = 0\n')
        enhanced.append('\n')
        enhanced.append('debug_active = DEBUG_MODE == 1 or tw_debug_level >= 2\n')
        enhanced.append('\n')
        enhanced.append('def get_log_dir():\n')
        enhanced.append('    """Log dir respects TW_TASK_DIR for dev/test isolation."""\n')
        enhanced.append("    import os as _os\n")
        enhanced.append("    task_dir = Path(_os.environ.get('TW_TASK_DIR', str(Path.home() / '.task')))\n")
        enhanced.append("    log_dir = task_dir / 'logs' / 'debug'\n")
        enhanced.append('    log_dir.mkdir(parents=True, exist_ok=True)\n')
        enhanced.append('    return log_dir\n')
        enhanced.append('\n')
        enhanced.append('if debug_active:\n')
        enhanced.append('    DEBUG_LOG_DIR = get_log_dir()\n')
        enhanced.append('    DEBUG_SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")\n')
        enhanced.append('    try:\n')
        enhanced.append('        script_name = Path(__file__).stem\n')
        enhanced.append('    except:\n')
        enhanced.append('        script_name = Path(sys.argv[0]).stem if sys.argv else "script"\n')
        enhanced.append('    DEBUG_LOG_FILE = DEBUG_LOG_DIR / f"{script_name}_debug_{DEBUG_SESSION_ID}.log"\n')
        enhanced.append('    \n')
        enhanced.append('    def debug_log(message, level=1):\n')
        enhanced.append('        if debug_active and tw_debug_level >= level:\n')
        enhanced.append('            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]\n')
        enhanced.append('            log_line = f"{timestamp} [DEBUG-{level}] {message}\\n"\n')
        enhanced.append('            with open(DEBUG_LOG_FILE, "a") as f:\n')
        enhanced.append('                f.write(log_line)\n')
        enhanced.append('            print(f"\\033[34m[DEBUG-{level}]\\033[0m {message}", file=sys.stderr)\n')
        enhanced.append('    \n')
        enhanced.append('    with open(DEBUG_LOG_FILE, "w") as f:\n')
        enhanced.append('        f.write("=" * 70 + "\\n")\n')
        enhanced.append('        f.write(f"Debug Session - {datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}\\n")\n')
        enhanced.append('        f.write(f"Script: {script_name}\\n")\n')
        enhanced.append('        f.write(f"TW_DEBUG Level: {tw_debug_level}\\n")\n')
        enhanced.append('        f.write("=" * 70 + "\\n\\n")\n')
        enhanced.append('    debug_log(f"Debug logging initialized: {DEBUG_LOG_FILE}", 1)\n')
        enhanced.append('else:\n')
        enhanced.append('    def debug_log(message, level=1):\n')
        enhanced.append('        pass\n')
        enhanced.append('\n')
        enhanced.append('# ============================================================================\n')
        enhanced.append('# Original Code\n')
        enhanced.append('# ============================================================================\n')
        enhanced.append('\n')
        
        for line in parsed['rest']:
            enhanced.append(line)
        
        return enhanced


def process_python_file(filepath: str, dry_run: bool = False) -> bool:
    """Process a single Python file"""
    msg(f"Processing: {filepath}")

    if dry_run:
        msg(f"[dry-run] Would enhance: {filepath}")
        return True

    pattern = PythonFileAnalyzer.analyze(filepath)

    if pattern.has_debug_var:
        msg(f"  - Found: {pattern.debug_var_name} = {pattern.debug_var_value}")
    if pattern.has_debug_function:
        msg(f"  - Found: {pattern.debug_function_name}()")
    if pattern.path_constants:
        msg(f"  - Found {len(pattern.path_constants)} path constants (preserving)")

    parsed = PythonFileParser.parse(filepath)

    if pattern.has_debug_var or pattern.has_debug_function:
        msg("Enhancing existing debug...")
        enhanced_lines = DebugEnhancer.enhance_existing_debug(pattern, parsed)
    else:
        msg("Adding new debug...")
        enhanced_lines = DebugEnhancer.add_new_debug(parsed)
    
    # Backup original to .orig
    orig_path = Path(filepath).with_suffix(Path(filepath).suffix + '.orig')
    msg(f"Backing up to: {orig_path}")
    
    # Rename original to .orig
    Path(filepath).rename(orig_path)
    
    # Write enhanced version to original filename
    with open(filepath, 'w') as f:
        f.writelines(enhanced_lines)
    
    # Copy executable permissions from .orig
    if os.access(orig_path, os.X_OK):
        os.chmod(filepath, os.stat(orig_path).st_mode)
    
    success(f"Enhanced: {filepath} (original saved as {orig_path.name})")
    return True


def find_python_files() -> List[str]:
    """Find Python files"""
    files = []
    
    for f in Path('.').glob('*.py'):
        if f.is_file() and f.name != 'make-awesome.py':
            files.append(str(f))
    
    for f in Path('.').iterdir():
        if not f.is_file() or f.suffix or f.name == 'make-awesome.py':
            continue
        if not os.access(f, os.X_OK):
            continue
        
        try:
            with open(f, 'r') as file:
                if 'python' in file.readline():
                    files.append(str(f))
        except:
            continue
    
    return files


def cmd_debug(args) -> int:
    """Debug enhancement"""
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --debug")
    msg("=" * 70)
    print()

    force    = args and hasattr(args, 'force')    and args.force
    dry_run  = args and hasattr(args, 'dry_run') and args.dry_run

    if dry_run:
        msg("[dry-run] No files will be modified")
        print()

    files = find_python_files()

    if not files:
        warn("No Python files found")
        return 0

    success(f"Found {len(files)} file(s)")
    if force:
        msg("--force enabled: will re-enhance all files")
    print()

    processed = 0
    skipped = 0
    for f in files:
        with open(f, 'r') as file:
            already_enhanced = 'Auto-generated by make-awesome' in file.read()
        if not force and already_enhanced:
            if dry_run:
                warn(f"[dry-run] Would skip (already enhanced): {f}")
            else:
                warn(f"Already enhanced: {f}")
            skipped += 1
            continue

        try:
            if process_python_file(f, dry_run=dry_run):
                processed += 1
            print()
        except Exception as e:
            error(f"Failed: {f}: {e}")
    
    if processed > 0:
        success(f"Processed {processed} file(s)")
    elif skipped > 0:
        success(f"All files already enhanced ({skipped} file(s))")
    
    msg("Triggered by: tw --debug=2")
    print()
    
    # Success if we processed files OR all files were already enhanced
    return 0 if (processed > 0 or skipped > 0) else 1


# ============================================================================
# TIMING Enhancement
# ============================================================================

# The timing block injected into each hook.
# Placed immediately after the shebang so _t0 is set before any imports,
# capturing full Python interpreter startup cost.
# Uses atexit so the report fires at natural script exit regardless of
# how the hook terminates.  All names are prefixed with _ to avoid
# colliding with any hook's own namespace.
_TIMING_BLOCK = '''\
import os as _os_timing, time as _time_module
if _os_timing.environ.get('TW_TIMING'):
    import atexit as _atexit
    _t0 = _time_module.perf_counter()

    def _report_timing(_f=__file__):
        elapsed = (_time_module.perf_counter() - _t0) * 1000
        import os.path as _osp
        print(f"[timing] {_osp.basename(_f)}: {elapsed:.1f}ms", file=__import__('sys').stderr)

    _atexit.register(_report_timing)

'''


def _find_shebang_line(lines: list) -> int:
    """Return index of the line immediately after the shebang.

    If no shebang is present, returns 0 (insert at very top).
    The timing block must be the first real code after #!/usr/bin/env python3
    so that _t0 is set before any other imports run.
    """
    if lines and lines[0].startswith('#!'):
        return 1
    return 0


def inject_timing_block(filepath: str, force: bool = False, dry_run: bool = False) -> bool:
    """Inject the TW_TIMING block into a Python hook file.

    Inserts immediately after the shebang line so _t0 is set before any
    other imports, capturing full Python interpreter startup cost.

    Idempotent: skips if TW_TIMING already present unless force=True.
    On --force, strips the existing block before re-injecting.
    """
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.splitlines(keepends=True)

    if dry_run:
        if 'TW_TIMING' in content:
            if not force:
                warn(f"[dry-run] Would skip (already timed): {filepath}")
                return False
            else:
                msg(f"[dry-run] Would re-inject timing block into: {filepath}")
        else:
            msg(f"[dry-run] Would inject timing block into: {filepath}")
        return True

    if 'TW_TIMING' in content:
        if not force:
            warn(f"Already timed: {filepath}")
            return False  # False = skipped, not an error
        else:
            msg(f"--force: re-injecting timing block into {filepath}")
            # Strip old block. The block starts at a known marker line and
            # ends at the first blank line that follows '_atexit.register'.
            # We can't stop on the first blank because the block itself
            # contains internal blank lines.
            strip_markers = (
                'import os as _os_timing',        # new-style block start
                '# Timing support',                # old-style banner
                "if os.environ.get('TW_TIMING')",  # old-style (no banner)
            )
            new_lines = []
            skip = False
            seen_register = False
            for line in lines:
                if not skip and any(line.startswith(m) for m in strip_markers):
                    skip = True
                    seen_register = False
                    continue
                if skip:
                    if '_atexit.register' in line:
                        seen_register = True
                        continue
                    if seen_register and line.strip() == '':
                        # Trailing blank after register — done stripping
                        skip = False
                        seen_register = False
                    continue
                new_lines.append(line)
            lines = new_lines

    idx = _find_shebang_line(lines)

    lines = lines[:idx] + _TIMING_BLOCK.splitlines(keepends=True) + lines[idx:]

    # Backup original (only if no .orig already exists)
    orig_path = Path(filepath).with_suffix(Path(filepath).suffix + '.orig')
    if not orig_path.exists():
        msg(f"Backing up to: {orig_path.name}")
        Path(filepath).rename(orig_path)
    else:
        msg(f"Backup exists: {orig_path.name} (overwriting source only)")
        Path(filepath).unlink()

    with open(filepath, 'w') as f:
        f.writelines(lines)

    if orig_path.exists() and os.access(orig_path, os.X_OK):
        os.chmod(filepath, os.stat(orig_path).st_mode)

    success(f"Timing injected: {filepath}")
    return True


def cmd_timing(args) -> int:
    """Inject TW_TIMING timing block into all hook Python files."""
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --timing")
    msg("=" * 70)
    print()

    force    = args and hasattr(args, 'force')    and args.force
    dry_run  = args and hasattr(args, 'dry_run') and args.dry_run

    if dry_run:
        msg("[dry-run] No files will be modified")
        print()

    files = find_python_files()

    if not files:
        warn("No Python files found")
        return 0

    success(f"Found {len(files)} file(s)")
    if force:
        msg("--force enabled: will re-inject timing block in all files")
    print()

    injected = 0
    skipped  = 0
    for f in files:
        try:
            result = inject_timing_block(f, force=force, dry_run=dry_run)
            if result:
                injected += 1
            else:
                skipped += 1
            print()
        except Exception as e:
            error(f"Failed: {f}: {e}")

    if injected > 0:
        success(f"Timing block injected into {injected} file(s)")
    if skipped > 0:
        msg(f"Skipped {skipped} file(s) (already timed; use --force to re-inject)")

    msg("Triggered by: tw --timing")
    print()

    return 0 if (injected > 0 or skipped > 0) else 1


# ============================================================================
# StageReport — shared deviation/anomaly reporting for all pipeline stages
# ============================================================================

class StageReport:
    """Accumulates events during a pipeline stage and prints a summary.

    Each stage creates one StageReport, feeds it events, then calls
    print_summary() at the end.  Clean runs (no flags, no failures) stay
    silent so the normal stage output is not cluttered.

    Event types:
      changed  — file/item was successfully modified
      skipped  — already correct, nothing to do
      flagged  — unusual pattern found but NOT auto-fixed (needs human eye)
      failed   — hard error during processing
    """

    def __init__(self, stage_name: str):
        self.stage   = stage_name
        self.changed: list = []   # (item, detail)
        self.skipped: list = []
        self.flagged: list = []
        self.failed:  list = []

    def add_changed(self, item: str, detail: str = ''):
        self.changed.append((item, detail))

    def add_skipped(self, item: str, detail: str = ''):
        self.skipped.append((item, detail))

    def add_flagged(self, item: str, detail: str):
        self.flagged.append((item, detail))

    def add_failed(self, item: str, detail: str):
        self.failed.append((item, detail))

    @property
    def has_issues(self) -> bool:
        return bool(self.flagged or self.failed)

    @property
    def clean(self) -> bool:
        return not self.has_issues

    def print_summary(self):
        """Print report only when there is something worth noting."""
        if not self.has_issues:
            return
        print()
        msg(f"┌─ {self.stage} stage report ({'CLEAN' if self.clean else 'ATTENTION NEEDED'}) ─")
        if self.flagged:
            msg(f"│  {len(self.flagged)} flagged (unusual patterns — review manually):")
            for item, detail in self.flagged:
                warn(f"│    [FLAG] {item}")
                if detail:
                    warn(f"│           {detail}")
        if self.failed:
            msg(f"│  {len(self.failed)} failed:")
            for item, detail in self.failed:
                error(f"│    [FAIL] {item}")
                if detail:
                    error(f"│           {detail}")
        msg(f"└{'─' * 60}")
        print()


# ============================================================================
# EnvarEnhancer — patch hardcoded ~/.task paths to use TW_TASK_DIR
# ============================================================================

class EnvarEnhancer:
    """Scan and patch hardcoded environment-related paths in project files.

    Handles:
      TW_TASK_DIR  — replaces hardcoded ~/.task path constants
      TASKRC       — replaces hardcoded ~/.taskrc references
      TW_DEBUG     — flags non-standard debug implementations (no auto-fix)
      TW_TIMING    — flags non-standard timing blocks (no auto-fix)

    Safe patterns (auto-fixed):
      Python:
        TASK_DIR   = os.path.expanduser("~/.task")
        CONFIG_DIR = os.path.expanduser("~/.task/config")
        HOOK_DIR   = os.path.expanduser("~/.task/hooks")
        <VAR>      = os.path.expanduser("~/.task/config/<file>.rc")
        Path.home() / '.task'  (standalone, not chained)
        taskrc     = os.path.expanduser("~/.taskrc")
      Shell:
        TASK_DIR="${HOME}/.task"  or  TASK_DIR="$HOME/.task"
        TASKRC="${HOME}/.taskrc"  (only if not already using ${TASKRC:-...})

    Flagged (reported, not auto-fixed):
      - Inline ~/.task references inside strings/f-strings
      - ~/.task in comments (informational only)
      - TW_DEBUG / TW_TIMING patterns that differ from injector standard
      - Any remaining ~/.task reference after patching
    """

    import re as _re

    # ── Python patterns ───────────────────────────────────────────────────────

    # TASK_DIR = os.path.expanduser("~/.task")
    _PY_TASK_DIR = _re.compile(
        r'^(\s*TASK_DIR\s*=\s*)os\.path\.expanduser\(["\']~/.task["\']\)',
        _re.MULTILINE
    )
    _PY_TASK_DIR_REPL = r"\1os.environ.get('TW_TASK_DIR', os.path.expanduser('~/.task'))"

    # CONFIG_DIR = os.path.expanduser("~/.task/config")
    _PY_CONFIG_DIR = _re.compile(
        r'^(\s*CONFIG_DIR\s*=\s*)os\.path\.expanduser\(["\']~/.task/config["\']\)',
        _re.MULTILINE
    )
    _PY_CONFIG_DIR_REPL = r"\1os.path.join(TASK_DIR, 'config')"

    # HOOK_DIR = os.path.expanduser("~/.task/hooks")
    _PY_HOOK_DIR = _re.compile(
        r'^(\s*HOOK_DIR\s*=\s*)os\.path\.expanduser\(["\']~/.task/hooks["\']\)',
        _re.MULTILINE
    )
    _PY_HOOK_DIR_REPL = r"\1os.path.join(TASK_DIR, 'hooks')"

    # <VAR> = os.path.expanduser("~/.task/config/<file>")
    _PY_TASK_SUBPATH = _re.compile(
        r'^(\s*\w+\s*=\s*)os\.path\.expanduser\(["\']~/.task/([^"\']+)["\']\)',
        _re.MULTILINE
    )

    # Path.home() / '.task'  (NOT followed by / to avoid chained paths)
    _PY_PATH_HOME = _re.compile(
        r"Path\.home\(\)\s*/\s*'\.task'(?!\s*/)",
    )
    _PY_PATH_HOME_REPL = "Path(os.environ.get('TW_TASK_DIR', str(Path.home() / '.task')))"

    # taskrc = os.path.expanduser("~/.taskrc")  — any var name
    _PY_TASKRC = _re.compile(
        r'^(\s*\w*[Tt]ask[Rr][Cc]\w*\s*=\s*)os\.path\.expanduser\(["\']~/.taskrc["\']\)',
        _re.MULTILINE
    )
    _PY_TASKRC_REPL = r"\1os.environ.get('TASKRC', os.path.expanduser('~/.taskrc'))"

    # ── Shell patterns ────────────────────────────────────────────────────────

    # TASK_DIR="$HOME/.task" or TASK_DIR="${HOME}/.task"
    _SH_TASK_DIR = _re.compile(
        r'^(\s*TASK_DIR\s*=\s*)["\']?\$\{?HOME\}?/\.task["\']?',
        _re.MULTILINE
    )
    _SH_TASK_DIR_REPL = r'\1"${TW_TASK_DIR:-${HOME}/.task}"'

    # TASKRC="$HOME/.taskrc" — only when NOT already using ${TASKRC:-...}
    _SH_TASKRC = _re.compile(
        r'^(\s*TASKRC\s*=\s*)["\']?\$\{?HOME\}?/\.taskrc["\']?',
        _re.MULTILINE
    )
    _SH_TASKRC_REPL = r'\1"${TASKRC:-${HOME}/.taskrc}"'

    # ── Detection patterns (flag only) ────────────────────────────────────────

    # Remaining ~/.task references after patching
    _REMAINING_TASK = _re.compile(r'~/.task(?!/logs)')
    # Non-standard TW_DEBUG (not from injector)
    _CUSTOM_DEBUG   = _re.compile(r'TW_DEBUG', _re.MULTILINE)
    _INJECTOR_MARK  = 'Auto-generated by make-awesome'

    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def _is_python(cls, path: Path) -> bool:
        return path.suffix == '.py' or (
            path.suffix == '' and path.read_bytes()[:2] in (b'#!',) and
            b'python' in path.read_bytes()[:50]
        )

    @classmethod
    def _is_shell(cls, path: Path) -> bool:
        if path.suffix in ('.sh', '.bash'):
            return True
        if path.suffix == '':
            try:
                hdr = path.read_bytes()[:50]
                return b'#!/bin/bash' in hdr or b'#!/bin/sh' in hdr
            except Exception:
                return False
        return False

    @classmethod
    def scan_file(cls, path: Path, report: 'StageReport'):
        """Scan one file and add events to report without modifying anything."""
        try:
            text = path.read_text(errors='replace')
        except Exception as e:
            report.add_failed(path.name, str(e))
            return

        fname = path.name

        if cls._is_python(path) or cls._is_shell(path):
            # Check for already-done
            if 'TW_TASK_DIR' in text:
                report.add_skipped(fname, 'already uses TW_TASK_DIR')
                return

        if cls._is_python(path):
            found = []
            if cls._PY_TASK_DIR.search(text):
                found.append('TASK_DIR')
            if cls._PY_CONFIG_DIR.search(text):
                found.append('CONFIG_DIR')
            if cls._PY_HOOK_DIR.search(text):
                found.append('HOOK_DIR')
            if cls._PY_TASKRC.search(text):
                found.append('TASKRC')
            if cls._PY_PATH_HOME.search(text):
                found.append('Path.home()/.task')
            if found:
                report.add_changed(fname, f"will patch: {', '.join(found)}")

            # Sub-path patterns — auto-fixable, report them
            for m in cls._PY_TASK_SUBPATH.finditer(text):
                subpath = m.group(2)
                # Skip if it's already handled by specific patterns above
                if not subpath.startswith('config') and not subpath.startswith('hooks'):
                    report.add_changed(fname, f"will patch inline path: ~/.task/{subpath}")

            # TW_DEBUG: flag if present but NOT from injector
            if cls._CUSTOM_DEBUG.search(text) and cls._INJECTOR_MARK not in text:
                report.add_flagged(fname, 'custom TW_DEBUG implementation (not from injector) — review')

        elif cls._is_shell(path):
            found = []
            if cls._SH_TASK_DIR.search(text):
                found.append('TASK_DIR')
            if cls._SH_TASKRC.search(text) and '${TASKRC:-' not in text:
                found.append('TASKRC')
            if found:
                report.add_changed(fname, f"will patch: {', '.join(found)}")

    @classmethod
    def patch_file(cls, path: Path, report: 'StageReport', dry_run: bool = False) -> bool:
        """Patch one file. Returns True if file was changed (or would be in dry_run)."""
        import shutil
        try:
            original = path.read_text()
        except Exception as e:
            report.add_failed(path.name, str(e))
            return False

        # Skip if already done
        if 'TW_TASK_DIR' in original:
            report.add_skipped(path.name, 'already uses TW_TASK_DIR')
            return False

        patched = original
        changed_items = []

        if cls._is_python(path):
            # Ensure `import os` is present (needed for os.environ.get)
            has_import_os = bool(_re.search(r'^import os\b', patched, _re.MULTILINE))

            # Apply patches in dependency order
            if cls._PY_TASK_DIR.search(patched):
                patched = cls._PY_TASK_DIR.sub(cls._PY_TASK_DIR_REPL, patched)
                changed_items.append('TASK_DIR')
                if not has_import_os:
                    # Insert `import os` after shebang/docstring block
                    patched = cls._inject_import_os(patched)

            if cls._PY_CONFIG_DIR.search(patched):
                patched = cls._PY_CONFIG_DIR.sub(cls._PY_CONFIG_DIR_REPL, patched)
                changed_items.append('CONFIG_DIR')

            if cls._PY_HOOK_DIR.search(patched):
                patched = cls._PY_HOOK_DIR.sub(cls._PY_HOOK_DIR_REPL, patched)
                changed_items.append('HOOK_DIR')

            # Generic sub-path handler for remaining ~/.task/<path> patterns
            def _subpath_repl(m):
                prefix = m.group(1)
                subpath = m.group(2)
                parts = subpath.strip('/').split('/')
                parts_str = ', '.join(f"'{p}'" for p in parts)
                return f"{prefix}os.path.join(TASK_DIR, {parts_str})"

            if cls._PY_TASK_SUBPATH.search(patched):
                new = cls._PY_TASK_SUBPATH.sub(_subpath_repl, patched)
                if new != patched:
                    patched = new
                    changed_items.append('subpaths')

            if cls._PY_PATH_HOME.search(patched):
                patched = cls._PY_PATH_HOME.sub(cls._PY_PATH_HOME_REPL, patched)
                changed_items.append('Path.home()/.task')

            if cls._PY_TASKRC.search(patched):
                patched = cls._PY_TASKRC.sub(cls._PY_TASKRC_REPL, patched)
                changed_items.append('TASKRC')

            # If any replacement introduced os.path.join(TASK_DIR, ...) but
            # TASK_DIR is not defined, inject the constant before its first use.
            if ('os.path.join(TASK_DIR' in patched and
                    not _re.search(r'^\s*TASK_DIR\s*=', patched, _re.MULTILINE)):
                td_const = ("TASK_DIR = os.environ.get("
                            "'TW_TASK_DIR', os.path.expanduser('~/.task'))\n")
                # Insert just before the first line referencing TASK_DIR
                lines = patched.splitlines(keepends=True)
                insert_at = next(
                    (i for i, l in enumerate(lines) if 'TASK_DIR' in l),
                    len(lines)
                )
                lines.insert(insert_at, td_const)
                patched = ''.join(lines)
                if not has_import_os:
                    patched = cls._inject_import_os(patched)
                if 'TASK_DIR (injected)' not in changed_items:
                    changed_items.append('TASK_DIR (injected)')

            # Flag remaining ~/.task refs that look like actual path code
            # (skip comment lines and plain-text strings like install instructions)
            _path_ops = ('expanduser', 'os.path', 'Path(', 'join(', '= "~/', "= '~/")
            for line in patched.splitlines():
                stripped = line.lstrip()
                if stripped.startswith('#'):
                    continue
                if '~/.task' in line and 'TW_TASK_DIR' not in line:
                    if any(op in line for op in _path_ops):
                        report.add_flagged(path.name,
                            f"residual ~/.task in path code (not auto-fixed): {stripped[:80]}")

            # TW_DEBUG without injector mark
            if cls._CUSTOM_DEBUG.search(patched) and cls._INJECTOR_MARK not in patched:
                report.add_flagged(path.name,
                    'custom TW_DEBUG (not from injector) — run --debug stage first')

        elif cls._is_shell(path):
            if cls._SH_TASK_DIR.search(patched):
                patched = cls._SH_TASK_DIR.sub(cls._SH_TASK_DIR_REPL, patched)
                changed_items.append('TASK_DIR')

            if cls._SH_TASKRC.search(patched) and '${TASKRC:-' not in patched:
                patched = cls._SH_TASKRC.sub(cls._SH_TASKRC_REPL, patched)
                changed_items.append('TASKRC')

        if patched == original:
            report.add_skipped(path.name, 'no matching patterns found')
            return False

        if dry_run:
            report.add_changed(path.name, f"[dry-run] would patch: {', '.join(changed_items)}")
            return True

        # Backup
        orig_path = Path(str(path) + '.orig')
        if not orig_path.exists():
            shutil.copy2(path, orig_path)

        # Write patch
        path.write_text(patched)

        # Verify Python compiles
        # Clear PYTHONPYCACHEPREFIX — if set to /dev/null (a common dev setting)
        # py_compile will crash trying to create cache dirs inside /dev/null.
        if cls._is_python(path):
            import subprocess as _sp
            import os as _os2
            _compile_env = _os2.environ.copy()
            _compile_env.pop('PYTHONPYCACHEPREFIX', None)
            result = _sp.run(
                [sys.executable, '-m', 'py_compile', str(path)],
                capture_output=True,
                env=_compile_env
            )
            if result.returncode != 0:
                # Restore from backup
                shutil.copy2(orig_path, path)
                report.add_failed(path.name,
                    f"syntax error after patch — restored from .orig: "
                    f"{result.stderr.decode().strip()[:120]}")
                return False

        report.add_changed(path.name, f"patched: {', '.join(changed_items)}")
        return True

    @classmethod
    def _inject_import_os(cls, text: str) -> str:
        """Insert `import os` after the first existing import block."""
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_at = i
                break
        if insert_at:
            lines.insert(insert_at, 'import os\n')
        return ''.join(lines)

    @classmethod
    def update_awesome_rc(cls, app_name: str) -> bool:
        """Flip envar_ready = yes for app_name in awesome.rc."""
        rc_path = SCRIPT_DIR / 'awesome.rc'
        if not rc_path.exists():
            return False
        text = rc_path.read_text()
        # Find the section and update envar_ready within it
        import re as _re2
        # Match the section and the envar_ready line within it
        pattern = _re2.compile(
            r'(^\[' + _re2.escape(app_name) + r'\][^\[]*?)'
            r'(envar_ready\s*=\s*)\S+',
            _re2.MULTILINE | _re2.DOTALL
        )
        new_text, n = pattern.subn(r'\g<1>\g<2>yes', text)
        if n:
            rc_path.write_text(new_text)
            return True
        return False


# ─────────────────────────────────────────────────────────────────────────────

import re as _re


def cmd_envar(args) -> int:
    """Patch hardcoded env-related paths to use TW_TASK_DIR / TASKRC."""
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --envar")
    msg("=" * 70)
    print()

    dry_run = args and hasattr(args, 'dry_run') and args.dry_run
    force   = args and hasattr(args, 'force')   and args.force

    if dry_run:
        msg("[dry-run] No files will be modified")
        print()

    report = StageReport('Envar')

    # Collect candidate files: .py, shell scripts, executable files without extension
    candidates: list[Path] = []
    for pat in ['*.py', '*.sh']:
        candidates.extend(Path('.').glob(pat))
    for f in Path('.').iterdir():
        if f.is_file() and f.suffix == '' and os.access(f, os.X_OK):
            candidates.append(f)
    candidates = sorted(set(candidates))

    # Skip .orig and __pycache__
    candidates = [f for f in candidates
                  if not f.name.endswith('.orig') and '__pycache__' not in str(f)]

    if not candidates:
        warn("No patchable files found")
        return 0

    msg(f"Scanning {len(candidates)} file(s)...")
    print()

    changed = 0
    for f in candidates:
        if dry_run:
            scan_report = StageReport('scan')
            EnvarEnhancer.scan_file(f, scan_report)
            # Merge into main report
            for item, detail in scan_report.changed:
                report.add_changed(item, detail)
                msg(f"  [would patch] {item}: {detail}")
            for item, detail in scan_report.skipped:
                pass  # silent
            for item, detail in scan_report.flagged:
                report.add_flagged(item, detail)
                warn(f"  [flag] {item}: {detail}")
        else:
            if EnvarEnhancer.patch_file(f, report, dry_run=False):
                changed += 1

    print()

    if not dry_run:
        if changed > 0:
            success(f"Patched {changed} file(s)")
        else:
            msg("No files needed patching")

        # Update awesome.rc if no failures
        if not report.failed:
            app_name = _get_app_name_from_meta()
            if app_name:
                if EnvarEnhancer.update_awesome_rc(app_name):
                    success(f"awesome.rc: envar_ready = yes  [{app_name}]")
                else:
                    warn(f"Could not update awesome.rc for '{app_name}' "
                         f"(not in fleet or envar_ready field missing)")
            else:
                warn("No .meta found — awesome.rc not updated")
        else:
            warn("awesome.rc not updated (failures present — fix and re-run)")

    report.print_summary()

    msg("Triggered by: TW_TASK_DIR / TASKRC isolation (B+C)")
    print()
    return 0 if not report.failed else 1


def _get_app_name_from_meta() -> str:
    """Read app name from the first .meta file in cwd."""
    metas = list(Path('.').glob('*.meta'))
    if not metas:
        return ''
    for line in metas[0].read_text().splitlines():
        if line.startswith('name='):
            return line.split('=', 1)[1].strip()
    return ''


class ProjectInfo:
    def __init__(self):
        self.name = ""
        self.version = "1.0.0"
        self.type = "hook"
        self.description = ""
        self.repo = ""
        self.branch = "main"  # Default branch
        self.author = ""
        self.license = "MIT"
        self.requires_tw = "2.6.0"
        self.requires_py = ""
        self.tags = ""
        self.files = []
        self.checksums = []
        # Wrapper-specific fields
        self.wrapper_keyword = ""
        self.wrapper_script = ""
        self.wrapper_type = "command"  # 'command' or 'filter'


def detect_project_info() -> ProjectInfo:
    info = ProjectInfo()
    info.name = Path.cwd().name
    msg(f"Project: {info.name}")
    
    if Path("VERSION").exists():
        info.version = Path("VERSION").read_text().strip()
    elif Path("version.txt").exists():
        info.version = Path("version.txt").read_text().strip()
    
    msg(f"Version: {info.version}")
    
    # Detect GitHub repo
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                              capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        match = re.search(r'github\.com[:/](.+?)(\.git)?$', url)
        if match:
            info.repo = match.group(1)
            msg(f"GitHub: {info.repo}")
    except:
        pass
    
    # Detect default branch
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                              capture_output=True, text=True, check=True)
        info.branch = result.stdout.strip()
        msg(f"Branch: {info.branch}")
    except:
        # Fallback: try to get from remote
        try:
            result = subprocess.run(['git', 'remote', 'show', 'origin'],
                                  capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if 'HEAD branch:' in line:
                    info.branch = line.split(':')[1].strip()
                    msg(f"Branch: {info.branch}")
                    break
        except:
            info.branch = "main"  # Default fallback
    
    # Detect author from git
    try:
        result = subprocess.run(['git', 'config', 'user.name'],
                              capture_output=True, text=True, check=True)
        info.author = result.stdout.strip()
    except:
        info.author = os.environ.get('USER', 'Unknown')
    
    return info


def detect_files() -> List[Tuple[str, str]]:
    files = []
    msg("Detecting files...")
    
    # Helper function to detect path marker suffixes
    # Pattern: basename_TYPE.extension or basename_TYPE-x.extension
    # Examples: recurrence_common_hook-x.py, utils_script.sh, README_doc.md
    def get_path_marker_type(filename: str) -> Optional[str]:
        """Check if filename has path marker suffix like _hook, _script, _config, _doc"""
        # Match: basename_TYPE[-x].extension
        match = re.match(r'^.+_(hook|script|config|doc)(-x)?\.\w+$', filename)
        if match:
            return match.group(1)
        return None
    
    # Detect standard hooks (on-add*, on-exit*, on-modify*)
    for hook in ['on-add', 'on-exit', 'on-modify', 'on-launch']:
        for ext in ['py', 'sh']:
            for f in Path('.').glob(f'{hook}*.{ext}'):
                if not f.name.startswith('debug.') and not f.name.endswith('.orig'):
                    if f.is_file():
                        files.append((f.name, 'hook'))
                        msg(f"  Hook: {f.name}")
    
    # Detect files with path marker suffixes
    # These are files that go to non-standard locations (e.g., library in hooks dir)
    for pattern in ['*_hook*.py', '*_hook*.sh', '*_script*.py', '*_script*.sh', '*_config*.rc', '*_config*.conf', '*_doc*.md']:
        for f in Path('.').glob(pattern):
            if f.is_file() and not any(fname == f.name for fname, _ in files):
                path_marker_type = get_path_marker_type(f.name)
                if path_marker_type:
                    files.append((f.name, path_marker_type))
                    msg(f"  {path_marker_type.capitalize()} (path marker): {f.name}")
    
    # Detect scripts - check ALL files in root directory for executables
    exclude_patterns = [
        'debug.',           # debug.* files
        '.orig',            # backup files
        'on-add',           # hooks (handled above)
        'on-modify',        # hooks
        'on-exit',          # hooks
        'make-awesome.py',  # this script itself
        '.install',         # installer files (output, not input)
        '.meta',            # metadata files (output, not input)
        '.git',             # git files
        '__pycache__',      # python cache
    ]
    
    for f in Path('.').iterdir():
        # Skip directories
        if not f.is_file():
            continue
        
        # Skip excluded patterns
        if any(pattern in f.name for pattern in exclude_patterns):
            continue
        
        # Skip files already added as hooks
        if any(fname == f.name for fname, _ in files):
            continue
        
        # Check if executable
        if os.access(f, os.X_OK):
            # Is it a script? (has shebang or common script extension)
            try:
                with open(f, 'rb') as file:
                    first_bytes = file.read(2)
                    if first_bytes == b'#!':  # Has shebang
                        files.append((f.name, 'script'))
                        msg(f"  Script: {f.name}")
                        continue
            except:
                pass
            
            # Or has script extension
            if f.suffix in ['.py', '.sh', '.bash', '.pl', '.rb']:
                files.append((f.name, 'script'))
                msg(f"  Script: {f.name}")
    
    # Detect configs
    for ext in ['rc', 'conf']:
        for f in Path('.').glob(f'*.{ext}'):
            if f.is_file():
                files.append((f.name, 'config'))
                msg(f"  Config: {f.name}")
    
    # Detect docs
    for doc in ['README.md', 'USAGE.md', 'INSTALL.md']:
        if Path(doc).exists():
            files.append((doc, 'doc'))
            msg(f"  Doc: {doc}")
    
    return files


def load_files_from_meta(meta_file: Path) -> list:
    """Parse files= line from .meta. Returns list of 2-tuples (name, type) or
    3-tuples (name, type, dest) when a custom destination is specified."""
    try:
        with open(meta_file) as f:
            for line in f:
                if line.startswith('files='):
                    val = line.split('=', 1)[1].strip()
                    if not val:
                        return []
                    result = []
                    for entry in val.split(','):
                        parts = entry.strip().split(':')
                        if len(parts) >= 3:
                            result.append((parts[0], parts[1], ':'.join(parts[2:])))
                        elif len(parts) == 2:
                            result.append((parts[0], parts[1]))
                    return result
    except Exception:
        pass
    return []


def _load_or_detect_files() -> list:
    """Use files= from existing .meta if available, else detect from filesystem.
    Always supplements with any doc files (README.md etc.) present on disk but
    missing from files= — ensures they're not silently dropped on re-generation."""
    meta_files = list(Path('.').glob('*.meta'))
    if meta_files:
        files = load_files_from_meta(meta_files[0])
        if files:
            msg(f"  Using files= from {meta_files[0].name}")
            for t in files:
                dest = f" → {t[2]}" if len(t) > 2 else ""
                msg(f"    {t[0]}:{t[1]}{dest}")
            # Supplement with doc files present on disk but absent from files=
            existing_names = {t[0] for t in files}
            for doc in ['README.md', 'USAGE.md', 'INSTALL.md']:
                if doc not in existing_names and Path(doc).exists():
                    files.append((doc, 'doc'))
                    msg(f"  Doc (auto-added): {doc}")
            return files
    return detect_files()


def prompt_for_metadata(info: ProjectInfo) -> bool:
    msg("Gathering metadata...")
    print()
    
    # Check for existing .meta file to use as defaults
    # Look for ANY .meta file in current directory (not just matching dir name)
    meta_files = list(Path('.').glob('*.meta'))
    
    if meta_files:
        meta_file = meta_files[0]  # Use first .meta file found
        msg(f"Found existing .meta file: {meta_file.name}")
        try:
            with open(meta_file, 'r') as f:
                for line in f:
                    if line.startswith('name='):
                        info.name = line.split('=', 1)[1].strip()
                    elif line.startswith('version='):
                        info.version = line.split('=', 1)[1].strip()
                    elif line.startswith('description='):
                        info.description = line.split('=', 1)[1].strip()
                    elif line.startswith('author='):
                        info.author = line.split('=', 1)[1].strip()
                    elif line.startswith('tags='):
                        info.tags = line.split('=', 1)[1].strip()
                    elif line.startswith('license='):
                        info.license = line.split('=', 1)[1].strip()
                    elif line.startswith('type='):
                        info.type = line.split('=', 1)[1].strip()
                    elif line.startswith('wrapper.keyword='):
                        info.wrapper_keyword = line.split('=', 1)[1].strip()
                    elif line.startswith('wrapper.script='):
                        info.wrapper_script = line.split('=', 1)[1].strip()
                    elif line.startswith('wrapper.type='):
                        info.wrapper_type = line.split('=', 1)[1].strip()
                    elif line.startswith('base_url='):
                        # Extract branch from base_url
                        url = line.split('=', 1)[1].strip()
                        # URL format: https://raw.githubusercontent.com/user/repo/BRANCH/
                        parts = url.split('/')
                        if len(parts) >= 6:
                            info.branch = parts[5]
        except Exception as e:
            warn(f"Could not read .meta file: {e}")
    
    response = input(f"App name [{info.name}]: ").strip()
    if response:
        info.name = response
    
    response = input(f"Version [{info.version}]: ").strip()
    if response:
        info.version = response
    
    type_map = {'1': 'hook', '2': 'script', '3': 'config', '4': 'theme', '5': 'wrapper'}
    type_default = {v: k for k, v in type_map.items()}.get(info.type, '1')
    print("Type: (1) hook, (2) script, (3) config, (4) theme, (5) wrapper")
    response = input(f"Select [{type_default}]: ").strip()
    info.type = type_map.get(response, info.type)
    
    # Wrapper-specific prompts
    if info.type == 'wrapper':
        if info.wrapper_keyword:
            response = input(f"Wrapper keyword [{info.wrapper_keyword}]: ").strip()
            if response:
                info.wrapper_keyword = response
        else:
            info.wrapper_keyword = input("Wrapper keyword (e.g., ann): ").strip()
        
        if not info.wrapper_keyword:
            error("Wrapper keyword required")
            return False
        
        if info.wrapper_script:
            response = input(f"Wrapper script [{info.wrapper_script}]: ").strip()
            if response:
                info.wrapper_script = response
        else:
            info.wrapper_script = input("Wrapper script name (e.g., annn): ").strip()
        
        if not info.wrapper_script:
            error("Wrapper script name required")
            return False
        
        # Wrapper type: command (keyword dispatch) or filter (output filter)
        current_wtype = info.wrapper_type or 'command'
        print(f"Wrapper type: (1) command  — keyword in args triggers dispatch (e.g., annn)")
        print(f"              (2) filter   — pipes all report output through script (e.g., nicedates)")
        wtype_map = {'1': 'command', '2': 'filter', 'command': 'command', 'filter': 'filter'}
        response = input(f"Select [{current_wtype}]: ").strip().lower()
        info.wrapper_type = wtype_map.get(response, current_wtype)
    
    # Description with default if available
    if info.description:
        response = input(f"Description [{info.description}]: ").strip()
        if response:
            info.description = response
    else:
        info.description = input("Description: ").strip()
    
    if not info.description:
        error("Description required")
        return False
    
    if info.repo:
        response = input(f"GitHub repo [{info.repo}]: ").strip()
        if response:
            info.repo = response
    else:
        info.repo = input("GitHub repo (user/repo): ").strip()
    
    if not info.repo:
        error("GitHub repo required")
        return False
    
    # Branch prompt with detected default
    response = input(f"Branch [{info.branch}]: ").strip()
    if response:
        info.branch = response
    
    # Validate branch exists on GitHub by testing a known URL
    if info.repo:
        test_url = f"https://raw.githubusercontent.com/{info.repo}/{info.branch}/README.md"
        msg(f"Verifying branch '{info.branch}' on GitHub...")
        try:
            result = subprocess.run(
                ['curl', '-sI', '-o', '/dev/null', '-w', '%{http_code}', test_url],
                capture_output=True, text=True, timeout=10
            )
            http_code = result.stdout.strip()
            if http_code == '200':
                success(f"Branch '{info.branch}' verified")
            elif http_code in ('404', '000'):
                warn(f"Branch '{info.branch}' returned {http_code} - might not exist!")
                # Suggest alternatives
                alternatives = ['main', 'master'] if info.branch not in ('main', 'master') else ['master' if info.branch == 'main' else 'main']
                for alt in alternatives:
                    alt_url = f"https://raw.githubusercontent.com/{info.repo}/{alt}/README.md"
                    alt_result = subprocess.run(
                        ['curl', '-sI', '-o', '/dev/null', '-w', '%{http_code}', alt_url],
                        capture_output=True, text=True, timeout=10
                    )
                    if alt_result.stdout.strip() == '200':
                        response = input(f"  Branch '{alt}' exists. Use it instead? [Y/n]: ").strip().lower()
                        if response != 'n':
                            info.branch = alt
                            success(f"Switched to branch '{alt}'")
                        break
                else:
                    warn("Could not verify any branch. Continuing with current setting.")
                    response = input(f"  Continue with '{info.branch}'? [Y/n]: ").strip().lower()
                    if response == 'n':
                        info.branch = input("  Enter branch name: ").strip() or info.branch
            else:
                warn(f"Got HTTP {http_code} testing branch (might be fine for private repos)")
        except (subprocess.TimeoutExpired, Exception) as e:
            warn(f"Could not verify branch (network issue: {e}). Continuing.")
    
    # Author with default
    if info.author:
        response = input(f"Author [{info.author}]: ").strip()
        if response:
            info.author = response
    else:
        info.author = input("Author: ").strip()
    
    response = input(f"License [{info.license}]: ").strip()
    if response:
        info.license = response
    
    response = input(f"Requires TW [{info.requires_tw}]: ").strip()
    if response:
        info.requires_tw = response
    
    info.requires_py = input("Requires Python (blank if N/A): ").strip()
    
    print()
    msg("Tags (e.g., hook, script, python, bash, stable)")
    # Tags with default
    if info.tags:
        response = input(f"Tags [{info.tags}]: ").strip().lower()
        if response:
            info.tags = response
    else:
        info.tags = input("Tags: ").strip().lower()
    print()
    
    return True


def calculate_checksums(files: List[Tuple[str, str]]) -> List[str]:
    msg("Calculating checksums...")
    checksums = []
    
    for filename, *_ in files:
        try:
            with open(filename, 'rb') as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()
                checksums.append(sha256)
                msg(f"  {filename}: {sha256[:16]}...")
        except Exception as e:
            error(f"Failed: {filename}: {e}")
            return []
    
    return checksums


def generate_meta_file(info: ProjectInfo) -> bool:
    meta_file = f"{info.name}.meta"
    msg(f"Generating {meta_file}...")
    
    def _file_str(t):
        dest = t[2] if len(t) > 2 else None
        return f"{t[0]}:{t[1]}" + (f":{dest}" if dest else "")
    files_list = ','.join(_file_str(t) for t in info.files)
    checksums_list = ','.join(info.checksums)
    base_url = f"https://raw.githubusercontent.com/{info.repo}/{info.branch}"
    repo_url = f"https://github.com/{info.repo}"
    
    try:
        with open(meta_file, 'w') as f:
            f.write(f"# {info.name}.meta\n")
            f.write(f"# {info.description}\n\n")
            f.write(f"name={info.name}\n")
            f.write(f"version={info.version}\n")
            f.write(f"type={info.type}\n")
            f.write(f"description={info.description}\n")
            f.write(f"repo={repo_url}\n")
            f.write(f"base_url={base_url}\n")
            f.write(f"files={files_list}\n")
            f.write(f"tags={info.tags}\n\n")
            f.write(f"checksums={checksums_list}\n\n")
            f.write(f"author={info.author}\n")
            f.write(f"license={info.license}\n")
            f.write(f"requires_taskwarrior={info.requires_tw}\n")
            if info.requires_py:
                f.write(f"requires_python={info.requires_py}\n")
            if info.type == 'wrapper':
                f.write(f"\nwrapper.keyword={info.wrapper_keyword}\n")
                f.write(f"wrapper.script={info.wrapper_script}\n")
                f.write(f"wrapper.type={info.wrapper_type}\n")
        
        success(f"Created {meta_file}")
        return True
    except Exception as e:
        error(f"Failed: {e}")
        return False


def generate_installer(info: ProjectInfo) -> bool:
    """Generate full bash installer with install/remove functions"""
    install_file = f"{info.name}.install"
    msg(f"Generating {install_file}...")
    
    try:
        with open(install_file, 'w') as f:
            # Header and variables
            f.write('#!/usr/bin/env bash\n')
            f.write('set -euo pipefail\n\n')
            f.write('# ============================================================================\n')
            f.write(f'# {info.name} - Installer Script\n')
            f.write(f'# Version: {info.version}\n')
            f.write('# Generated by make-awesome.py\n')
            f.write('# ============================================================================\n\n')
            f.write(f'VERSION="{info.version}"\n')
            f.write(f'APPNAME="{info.name}"\n')
            f.write(f'BASE_URL="https://raw.githubusercontent.com/{info.repo}/{info.branch}"\n\n')
            
            # Colors and helper functions
            f.write("# Colors\n")
            f.write("RED='\\033[0;31m'\n")
            f.write("GREEN='\\033[0;32m'\n")
            f.write("BLUE='\\033[0;34m'\n")
            f.write("NC='\\033[0m'\n\n")
            f.write('tw_msg() { echo -e "${BLUE}[tw]${NC} $*"; }\n')
            f.write('tw_success() { echo -e "${GREEN}[tw] [OK]${NC} $*"; }\n')
            f.write('tw_error() { echo -e "${RED}[tw] [FAIL]${NC} $*" >&2; }\n\n')
            
            # Debug support
            f.write('# Debug support\n')
            f.write('DEBUG_LEVEL="${TW_DEBUG:-0}"\n')
            f.write('debug_msg() {\n')
            f.write('    local msg="$1"\n')
            f.write('    local level="${2:-1}"\n')
            f.write('    if [[ $DEBUG_LEVEL -ge $level ]]; then\n')
            f.write('        echo -e "${BLUE}[DEBUG-$level]${NC} $msg" >&2\n')
            f.write('    fi\n')
            f.write('}\n\n')
            f.write('debug_msg "Starting installer with DEBUG_LEVEL=$DEBUG_LEVEL" 1\n\n')
            
            # Directories
            f.write('# Directories\n')
            f.write('HOME="${HOME:-$(eval echo ~$USER)}"\n')
            f.write('TASKRC="${TASKRC:-${HOME}/.taskrc}"\n')
            f.write('TASK_DIR="${TW_TASK_DIR:-${HOME}/.task}"\n')
            f.write('HOOKS_DIR="${TASK_DIR}/hooks"\n')
            f.write('SCRIPTS_DIR="${TASK_DIR}/scripts"\n')
            f.write('CONFIG_DIR="${TASK_DIR}/config"\n')
            f.write('DOCS_DIR="${TASK_DIR}/docs"\n\n')
            
            # Install function
            f.write('# ============================================================================\n')
            f.write('# Installation Function\n')
            f.write('# ============================================================================\n\n')
            f.write('install() {\n')
            f.write(f'    tw_msg "Installing {info.name} v$VERSION..."\n')
            f.write('    debug_msg "Starting installation" 1\n\n')
            f.write('    # Create directories\n')
            f.write('    tw_msg "Creating directories..."\n')
            f.write('    mkdir -p "$HOOKS_DIR" "$SCRIPTS_DIR" "$CONFIG_DIR" "$DOCS_DIR"\n')
            f.write('    debug_msg "Directories created" 2\n\n')
            f.write('    tw_msg "Downloading files..."\n')
            f.write('    debug_msg "Using BASE_URL: $BASE_URL" 2\n\n')
            
            # Normalize to 3-tuples (name, ftype, dest_or_none)
            _nf = [(t[0], t[1], t[2] if len(t) > 2 else None) for t in info.files]
            hooks   = [(n, ft, d) for n, ft, d in _nf if ft == 'hook']
            scripts = [(n, ft, d) for n, ft, d in _nf if ft == 'script']
            configs = [(n, ft, d) for n, ft, d in _nf if ft == 'config']
            docs    = [(n, ft, d) for n, ft, d in _nf if ft == 'doc']

            def _dest_path(filename, dir_var, dest):
                """Return shell dest path: custom (~ expanded) or type-based dir."""
                if dest:
                    return dest.replace('~', '$HOME')
                return f'{dir_var}/{filename}'

            # Download hooks
            for filename, _, dest in hooks:
                is_executable = not (
                    filename.endswith('-x.py') or
                    filename.endswith('-x.sh') or
                    ('_hook' in filename and not filename.startswith('on-'))
                )
                dp = _dest_path(filename, '$HOOKS_DIR', dest)
                if dest:
                    f.write(f'    mkdir -p "$(dirname "{dp}")"\n')
                f.write(f'    debug_msg "Downloading hook: {filename}" 2\n')
                f.write(f'    curl -fsSL "$BASE_URL/{filename}" -o "{dp}" || {{\n')
                f.write(f'        tw_error "Failed to download {filename}"\n')
                f.write(f'        debug_msg "Download failed: {filename}" 1\n')
                f.write('        return 1\n')
                f.write('    }\n')
                if is_executable:
                    f.write(f'    chmod +x "{dp}"\n')
                f.write(f'    debug_msg "Installed hook: {dp}" 2\n\n')

            # Download scripts
            for filename, _, dest in scripts:
                is_executable = not (filename.endswith('-x.sh') or filename.endswith('-x.py'))
                dp = _dest_path(filename, '$SCRIPTS_DIR', dest)
                if dest:
                    f.write(f'    mkdir -p "$(dirname "{dp}")"\n')
                f.write(f'    debug_msg "Downloading script: {filename}" 2\n')
                f.write(f'    curl -fsSL "$BASE_URL/{filename}" -o "{dp}" || {{\n')
                f.write(f'        tw_error "Failed to download {filename}"\n')
                f.write(f'        debug_msg "Download failed: {filename}" 1\n')
                f.write('        return 1\n')
                f.write('    }\n')
                if is_executable:
                    f.write(f'    chmod +x "{dp}"\n')
                f.write(f'    debug_msg "Installed script: {dp}" 2\n\n')

            # Download configs
            for filename, _, dest in configs:
                dp = _dest_path(filename, '$CONFIG_DIR', dest)
                if dest:
                    f.write(f'    mkdir -p "$(dirname "{dp}")"\n')
                f.write(f'    debug_msg "Downloading config: {filename}" 2\n')
                f.write(f'    curl -fsSL "$BASE_URL/{filename}" -o "{dp}" || {{\n')
                f.write(f'        tw_error "Failed to download {filename}"\n')
                f.write(f'        debug_msg "Download failed: {filename}" 1\n')
                f.write('        return 1\n')
                f.write('    }\n')
                f.write(f'    debug_msg "Installed config: {dp}" 2\n\n')

            # Add config to .taskrc if needed (standard dest only)
            std_configs = [(n, ft, d) for n, ft, d in configs if not d]
            if std_configs:
                first_config = std_configs[0][0]
                f.write('    # Add config to .taskrc\n')
                f.write('    tw_msg "Checking .taskrc for existing config include..."\n')
                f.write(f'    if ! grep -q "{first_config}" "$TASKRC" 2>/dev/null; then\n')
                f.write(f'        echo "include ~/.task/config/{first_config}" >> "$TASKRC"\n')
                f.write(f'        tw_msg "Added config include to .taskrc"\n')
                f.write(f'        debug_msg "Added to .taskrc: include ~/.task/config/{first_config}" 2\n')
                f.write('    else\n')
                f.write('        tw_msg "Config already in .taskrc"\n')
                f.write(f'        debug_msg "Config already present in .taskrc: {first_config}" 2\n')
                f.write('    fi\n\n')

            # Download docs
            for filename, _, dest in docs:
                docname = f"{info.name}_{filename}"
                dp = _dest_path(docname, '$DOCS_DIR', dest)
                if dest:
                    f.write(f'    mkdir -p "$(dirname "{dp}")"\n')
                f.write('    tw_msg "Downloading documentation..."\n')
                f.write(f'    curl -fsSL "$BASE_URL/{filename}" -o "{dp}" 2>/dev/null || true\n')
                f.write(f'    debug_msg "Downloaded doc: {dp}" 2\n\n')

            # Manifest tracking
            f.write('    # Track in manifest\n')
            f.write('    debug_msg "Writing to manifest" 2\n')
            f.write('    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"\n')
            f.write('    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")\n')
            f.write('    mkdir -p "$(dirname "$MANIFEST_FILE")"\n\n')

            # Add manifest entries for each file
            for filename, ftype, dest in _nf:
                if dest:
                    manifest_path = dest.replace('~', '$HOME')
                elif ftype == 'hook':
                    manifest_path = f'$HOOKS_DIR/{filename}'
                elif ftype == 'script':
                    manifest_path = f'$SCRIPTS_DIR/{filename}'
                elif ftype == 'config':
                    manifest_path = f'$CONFIG_DIR/{filename}'
                elif ftype == 'doc':
                    manifest_path = f'$DOCS_DIR/{info.name}_{filename}'
                else:
                    manifest_path = f'$TASK_DIR/{filename}'

                f.write(f'    echo "$APPNAME|$VERSION|{manifest_path}||$TIMESTAMP" >> "$MANIFEST_FILE"\n')
                f.write(f'    debug_msg "Manifest entry: {manifest_path}" 3\n')
            
            # Finish install function
            f.write('\n')
            
            # Register wrapper if applicable
            if info.type == 'wrapper' and info.wrapper_keyword and info.wrapper_script:
                f.write('    # Register wrapper with tw\n')
                f.write('    WRAPPERS_FILE="${HOME}/.task/config/.tw_wrappers"\n')
                f.write('    mkdir -p "$(dirname "$WRAPPERS_FILE")"\n')
                f.write(f'    if ! grep -q "^{info.wrapper_keyword}|" "$WRAPPERS_FILE" 2>/dev/null; then\n')
                f.write(f'        echo "{info.wrapper_keyword}|{info.wrapper_script}|{info.description}|{info.wrapper_type}" >> "$WRAPPERS_FILE"\n')
                f.write(f'        tw_msg "Registered wrapper: {info.wrapper_keyword} -> {info.wrapper_script} ({info.wrapper_type})"\n')
                f.write(f'        debug_msg "Registered wrapper in .tw_wrappers" 2\n')
                f.write('    else\n')
                f.write(f'        tw_msg "Wrapper already registered: {info.wrapper_keyword}"\n')
                f.write('    fi\n\n')
            
            f.write('    debug_msg "Installation complete" 1\n')
            f.write(f'    tw_success "Installed {info.name} v$VERSION"\n')
            f.write('    echo ""\n')
            if docs:
                doc_name = f"{info.name}_{docs[0][0]}"
                f.write(f'    tw_msg "Documentation: $DOCS_DIR/{doc_name}"\n')
            f.write('    echo ""\n\n')
            f.write('    return 0\n')
            f.write('}\n\n')
            
            # Remove function
            f.write('# ============================================================================\n')
            f.write('# Removal Function\n')
            f.write('# ============================================================================\n\n')
            f.write('remove() {\n')
            f.write(f'    tw_msg "Removing {info.name}..."\n')
            f.write('    debug_msg "Starting removal" 1\n\n')
            f.write('    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"\n')
            f.write('    if [ ! -f "$MANIFEST_FILE" ]; then\n')
            f.write('        tw_error "Manifest file not found"\n')
            f.write('        return 1\n')
            f.write('    fi\n\n')
            f.write('    # Remove files based on manifest\n')
            f.write('    grep "^$APPNAME|" "$MANIFEST_FILE" | cut -d"|" -f3 | while read -r file; do\n')
            f.write('        if [ -f "$file" ]; then\n')
            f.write('            rm "$file"\n')
            f.write('            debug_msg "Removed: $file" 2\n')
            f.write('            tw_msg "Removed: $(basename $file)"\n')
            f.write('        fi\n')
            f.write('    done\n\n')
            
            # Remove from manifest
            f.write('    # Remove from manifest\n')
            f.write('    sed -i.bak "/^$APPNAME|/d" "$MANIFEST_FILE"\n')
            f.write('    debug_msg "Removed from manifest" 2\n\n')
            
            # Remove config from .taskrc if present
            if configs:
                first_config = configs[0][0]
                # NO NAME CHANGES! Use actual filename
                # Match by filename only (path-format-agnostic)
                f.write('    # Remove config from .taskrc\n')
                f.write(f'    if grep -q "{first_config}" "$TASKRC" 2>/dev/null; then\n')
                f.write(f'        sed -i.bak "/{first_config}/d" "$TASKRC"\n')
                f.write(f'        tw_msg "Removed config from .taskrc"\n')
                f.write(f'        debug_msg "Removed from .taskrc: {first_config}" 2\n')
                f.write('    fi\n\n')
            
            # Unregister wrapper if applicable
            if info.type == 'wrapper' and info.wrapper_keyword:
                f.write('    # Unregister wrapper from tw\n')
                f.write('    WRAPPERS_FILE="${HOME}/.task/config/.tw_wrappers"\n')
                f.write(f'    if grep -q "^{info.wrapper_keyword}|" "$WRAPPERS_FILE" 2>/dev/null; then\n')
                f.write(f'        sed -i.bak "/^{info.wrapper_keyword}|/d" "$WRAPPERS_FILE"\n')
                f.write(f'        tw_msg "Unregistered wrapper: {info.wrapper_keyword}"\n')
                f.write(f'        debug_msg "Removed wrapper from .tw_wrappers" 2\n')
                f.write('    fi\n\n')
            
            f.write(f'    tw_success "Removed {info.name}"\n')
            f.write('    return 0\n')
            f.write('}\n\n')
            
            # Main entry point
            f.write('# ============================================================================\n')
            f.write('# Main\n')
            f.write('# ============================================================================\n\n')
            f.write('case "${1:-install}" in\n')
            f.write('    install)\n')
            f.write('        install\n')
            f.write('        ;;\n')
            f.write('    remove|uninstall)\n')
            f.write('        remove\n')
            f.write('        ;;\n')
            f.write('    *)\n')
            f.write('        echo "Usage: $0 {install|remove}"\n')
            f.write('        exit 1\n')
            f.write('        ;;\n')
            f.write('esac\n')
        
        # Make executable
        os.chmod(install_file, 0o755)
        success(f"Created {install_file} (executable)")
        return True
        
    except Exception as e:
        error(f"Failed to create {install_file}: {e}")
        return False


def cmd_meta(args, info=None) -> tuple:
    """Generate .meta file only. Returns (rc, info) so info can flow to cmd_install."""
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --meta")
    msg("=" * 70)
    print()

    if info is None:
        info = detect_project_info()
        print()

        info.files = _load_or_detect_files()
        if not info.files:
            return 1, None
        print()

        if not prompt_for_metadata(info):
            return 1, None

        info.checksums = calculate_checksums(info.files)
        if not info.checksums:
            return 1, None
        print()

    if not generate_meta_file(info):
        return 1, None

    print()
    success(".meta file generated!")
    print()
    return 0, info


def cmd_install(args, info=None) -> int:
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --install")
    msg("=" * 70)
    print()

    standalone = info is None

    if info is None:
        info = detect_project_info()
        print()

    # Respect hand-crafted installers — skip generation if sentinel is present,
    # but still sync VERSION= from .meta so the manifest records the right version.
    install_file = Path(f"{info.name}.install")
    if install_file.exists() and 'HANDCRAFTED' in install_file.read_text():
        warn(f"{install_file} is marked HANDCRAFTED — skipping installer generation")
        old_text = install_file.read_text()
        new_text = re.sub(r'^VERSION="[^"]*"', f'VERSION="{info.version}"',
                          old_text, count=1, flags=re.MULTILINE)
        if new_text != old_text:
            install_file.write_text(new_text)
            msg(f"Synced VERSION=\"{info.version}\" in {install_file}")
        else:
            msg(f"VERSION already \"{info.version}\" in {install_file}")
        # Recalculate checksums in .meta — VERSION sync changed the file content
        meta_file = Path(f"{info.name}.meta")
        if meta_file.exists():
            meta_text = meta_file.read_text()
            if 'checksums=' in meta_text:
                # Reload files= list from meta to recalculate in correct order
                files_line = next((l for l in meta_text.splitlines() if l.startswith('files=')), None)
                if files_line:
                    file_entries = [e.split(':')[0] for e in files_line[6:].split(',')]
                    new_checksums = []
                    ok = True
                    for fname in file_entries:
                        try:
                            sha = hashlib.sha256(Path(fname).read_bytes()).hexdigest()
                            new_checksums.append(sha)
                        except Exception as e:
                            warn(f"Could not checksum {fname}: {e}")
                            ok = False
                            break
                    if ok:
                        new_cs_line = 'checksums=' + ','.join(new_checksums)
                        new_meta = re.sub(r'^checksums=.*$', new_cs_line,
                                          meta_text, flags=re.MULTILINE)
                        meta_file.write_text(new_meta)
                        msg(f"Updated checksums in {meta_file}")
        return 0

    if standalone:
        info.files = _load_or_detect_files()
        if not info.files:
            return 1
        print()

        if not prompt_for_metadata(info):
            return 1

        info.checksums = calculate_checksums(info.files)
        if not info.checksums:
            return 1
        print()

        if not generate_meta_file(info):
            return 1

    if not generate_installer(info):
        return 1

    print()
    success("Installation files generated!")
    print()

    return 0


# ============================================================================
# TESTING (Stub)
# ============================================================================

def cmd_testing(args) -> int:
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --testing")
    msg("=" * 70)
    print()
    warn("Test infrastructure not yet implemented")
    print()
    return 0


# ============================================================================
# STDHELP (Stub)
# ============================================================================

def cmd_stdhelp(args) -> int:
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --stdhelp")
    msg("=" * 70)
    print()
    warn("Help standardisation not yet implemented")
    print()
    return 0


# ============================================================================
# PUSH (Git + Registry)
# ============================================================================

def push_project_repo(commit_msg: str) -> bool:
    """Show status, confirm, git add/commit/push the project repo."""
    try:
        result = subprocess.run(['git', 'status', '--short'],
                              capture_output=True, text=True, check=True)

        if not result.stdout.strip():
            msg("Working tree clean, nothing to commit")
            msg("Skipping project commit (will still update registry)")
            return True

        msg("Files to be committed:")
        print(result.stdout)

        try:
            response = input("Commit and push these files? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            msg("Cancelled")
            return False
        if response == 'n':
            msg("Skipping project commit")
            return True  # Not an error - user chose to skip

        msg("Git add...")
        subprocess.run(['git', 'add', '.'], check=True)

        msg(f"Commit: {commit_msg}")
        result = subprocess.run(['git', 'commit', '-m', commit_msg],
                              capture_output=True, text=True)

        if result.returncode != 0:
            if 'nothing to commit' in result.stdout or 'nothing to commit' in result.stderr:
                msg("Nothing to commit after staging")
                return True
            else:
                error("Git commit failed")
                print(result.stderr)
                return False

        msg("Push...")
        result = subprocess.run(['git', 'push'],
                              capture_output=True, text=True)

        if result.returncode != 0:
            error("Git push failed")
            print(result.stderr)
            return False

        success("Project pushed")
        return True

    except Exception as e:
        error(f"Git failed: {e}")
        return False


def push_registry(project_name: str) -> bool:
    """Copy .install/.meta to registry repo, commit --only those files, push."""
    registry_path = Path.home() / 'dev' / 'awesome-taskwarrior'

    if not registry_path.exists():
        error(f"Registry not found: {registry_path}")
        return False

    # Resolve file paths BEFORE any chdir
    original_dir = Path.cwd()
    install_file = original_dir / f"{project_name}.install"
    meta_file = original_dir / f"{project_name}.meta"

    if not install_file.exists():
        error(f"Install file not found: {install_file}")
        return False

    if not meta_file.exists():
        error(f"Meta file not found: {meta_file}")
        return False

    try:
        import shutil

        # Self-referential: cwd IS the registry — project commit already done, nothing more to do
        if original_dir.resolve() == registry_path.resolve():
            msg("Self-push: registry sync skipped (awesome-taskwarrior is not a managed app)")
            return True

        # Copy to registry directories
        msg("Copying to registry...")
        shutil.copy(install_file, registry_path / 'installers' / install_file.name)
        shutil.copy(meta_file, registry_path / 'registry.d' / meta_file.name)
        success(f"Copied {install_file.name} -> installers/")
        success(f"Copied {meta_file.name} -> registry.d/")

        # Switch to registry repo
        os.chdir(registry_path)

        # Stage only our two files
        subprocess.run(['git', 'add',
                       f'installers/{install_file.name}',
                       f'registry.d/{meta_file.name}'], check=True)

        # Commit --only so other dirty files in the registry are untouched
        result = subprocess.run(['git', 'commit', '--only', '-m',
                               f"Updated {project_name}",
                               f'installers/{install_file.name}',
                               f'registry.d/{meta_file.name}'],
                              capture_output=True, text=True)

        if result.returncode != 0:
            if 'nothing to commit' in result.stdout or 'nothing to commit' in result.stderr:
                msg("Registry files unchanged, nothing to commit")
                os.chdir(original_dir)
                return True
            else:
                error("Registry commit failed")
                print(result.stderr)
                os.chdir(original_dir)
                return False

        msg("Push registry...")
        result = subprocess.run(['git', 'push'],
                              capture_output=True, text=True)

        if result.returncode != 0:
            error("Registry push failed")
            print(result.stderr)
            os.chdir(original_dir)
            return False

        success("Registry updated")
        os.chdir(original_dir)
        return True

    except Exception as e:
        error(f"Registry update failed: {e}")
        try:
            os.chdir(original_dir)
        except:
            pass
        return False


def cmd_push(args, commit_msg: str = None) -> int:
    """Push project repo and update registry."""
    # Get project name from .meta file
    meta_files = list(Path('.').glob('*.meta'))
    if not meta_files:
        error("No .meta file found. Run --install first.")
        return 1

    meta_file = meta_files[0]
    project_name = meta_file.stem

    # Default commit message if none provided
    if not commit_msg:
        commit_msg = f"Update {project_name}"

    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --push")
    msg(f"Project: {project_name}")
    msg(f"Message: {commit_msg}")
    msg("=" * 70)
    print()

    # Step 1: Push the project repo
    msg("--- Project repo ---")
    if not push_project_repo(commit_msg):
        return 1
    print()

    # Step 2: Copy to registry and push (no-op when self-push)
    msg("--- Registry ---")
    if not push_registry(project_name):
        return 1

    print()
    success("Push complete!")
    print()

    return 0


# ============================================================================
# PIPELINE
# ============================================================================

def cmd_pipeline(commit_msg: str) -> int:
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} - FULL PIPELINE")
    msg(f"Message: {commit_msg}")
    msg("=" * 70)
    print()

    # Stages: (name, gated)  — stubs are not gated so pipeline continues
    stages = [
        ('Debug',    True),
        ('Testing',  False),
        ('Timing',   True),
        ('Envar',    False),   # non-gated: isolation patches, won't block pipeline
        ('Stdhelp',  False),
        ('Meta',     True),
        ('Install',  True),
        ('Push',     True),
    ]

    meta_info = None
    for i, (name, gated) in enumerate(stages, 1):
        msg(f"STAGE {i}/{len(stages)}: {name}")

        if name == 'Debug':
            rc = cmd_debug(None)
        elif name == 'Testing':
            rc = cmd_testing(None)
        elif name == 'Timing':
            rc = cmd_timing(None)
        elif name == 'Envar':
            rc = cmd_envar(None)
        elif name == 'Stdhelp':
            rc = cmd_stdhelp(None)
        elif name == 'Meta':
            rc, meta_info = cmd_meta(None)
        elif name == 'Install':
            rc = cmd_install(None, info=meta_info)
        elif name == 'Push':
            rc = cmd_push(None, commit_msg)

        if rc != 0 and gated:
            error(f"{name} stage failed")
            return 1
        print()

    msg("=" * 70)
    success("PIPELINE COMPLETE!")
    msg("=" * 70)
    print()

    return 0


# ============================================================================
# Fleet
# ============================================================================

def load_fleet_config() -> list:
    """Load awesome.rc from same directory as this script.

    Returns list of dicts, one per non-skipped app, with keys:
      name, path, type, timing, debug, skip
    """
    import configparser
    rc_path = SCRIPT_DIR / 'awesome.rc'
    if not rc_path.exists():
        error(f"awesome.rc not found at {rc_path}")
        return []

    cfg = configparser.ConfigParser()
    cfg.read(rc_path)

    apps = []
    for name in cfg.sections():
        s = cfg[name]
        path = Path(s.get('path', '')).expanduser()
        skip = s.get('skip', 'no').strip().lower() == 'yes'
        status = s.get('status', 'release').strip().lower()
        apps.append({
            'name':        name,
            'path':        path,
            'type':        s.get('type', 'unknown'),
            'timing':      s.get('timing', 'no').strip().lower() == 'yes',
            'debug':       s.get('debug', 'no').strip().lower() == 'yes',
            'skip':        skip,
            'status':      status,
            'envar_ready': s.get('envar_ready', 'no').strip().lower() == 'yes',
        })
    return apps


def cmd_fleet_status(apps) -> int:
    """Fleet diagnostic: path check, git status, type distribution, eligibility."""
    import subprocess as _sp
    from collections import Counter

    active  = [a for a in apps if not a['skip']]
    skipped = [a for a in apps if a['skip']]

    msg("=" * 70)
    msg(f"Fleet status -- {len(apps)} apps total  ({len(active)} active, {len(skipped)} skipped)")
    msg("=" * 70)
    print()

    type_counts = Counter(a['type'] for a in active)
    msg("Type distribution (active apps):")
    for t, n in sorted(type_counts.items()):
        print(f"  {t:<12} {n}")
    print()

    timing_elig  = sum(1 for a in active if a['timing'])
    debug_elig   = sum(1 for a in active if a['debug'])
    envar_ready  = sum(1 for a in active if a['envar_ready'])
    msg("Eligibility:")
    print(f"  --timing      {timing_elig} eligible")
    print(f"  --debug       {debug_elig} eligible")
    print()

    from collections import Counter as _Counter2
    status_counts = _Counter2(a['status'] for a in apps)
    msg("Status breakdown:")
    STATUS_ORDER = ['release', 'testing', 'wip', 'suspended', 'archived']
    for st in STATUS_ORDER:
        n = status_counts.get(st, 0)
        if n:
            print(f"  {st:<12} {n}")
    print(f"  envar_ready  {envar_ready}/{len(active)} active apps")
    print()

    msg("App status:")
    for app in apps:
        name  = app['name']
        atype = app['type']
        path  = app['path']

        if app['skip']:
            warn(f"  SKIP  {name:<24} {atype:<10} {path}")
            continue

        if not path.is_dir():
            error(f"  MISS  {name:<24} {atype:<10} {path}  (path not found)")
            continue

        # Git status
        result = _sp.run(['git', 'status', '--porcelain'], cwd=path,
                         capture_output=True, text=True)
        if result.returncode != 0:
            git_str = 'no-git '
        elif result.stdout.strip():
            git_str = 'dirty  '
        else:
            git_str = 'clean  '

        # Timing block presence
        py_files = list(path.glob('*.py'))
        py_files += [f for f in path.iterdir()
                     if f.is_file() and not f.suffix and os.access(f, os.X_OK)]
        has_timing = any('TW_TIMING' in f.read_text(errors='replace')
                         for f in py_files if f.exists())
        has_debug  = any('Auto-generated by make-awesome' in f.read_text(errors='replace')
                         for f in py_files if f.exists())

        cs_status = check_meta_checksums(path)
        cs_str = {'ok': 'cs:[+]', 'mismatch': 'cs:[!]', 'no-meta': 'cs:[-]', 'error': 'cs:[?]'}[cs_status]

        flags = []
        if app['timing']:
            flags.append(f"timing:[{'T' if has_timing else ' '}]")
        if app['debug']:
            flags.append(f"debug:[{'D' if has_debug else ' '}]")
        flags.append(cs_str)
        flags.append(f"env:[{'✓' if app['envar_ready'] else ' '}]")
        flag_str = '  '.join(flags)

        status = app['status']
        STATUS_WARN = {'wip', 'testing', 'suspended', 'archived'}
        line = f"  {name:<24} {atype:<10} [{status:<9}] git:{git_str}  {flag_str}"
        if status in STATUS_WARN:
            warn(line)
        else:
            success(line)

    print()
    return 0


def cmd_fleet_list(apps, pattern: str = '') -> int:
    """List fleet apps, optionally filtered by name pattern."""
    if pattern:
        apps = [a for a in apps if pattern.lower() in a['name'].lower()]

    if not apps:
        warn(f"No apps matching '{pattern}'")
        return 0

    home = str(Path.home())
    print(f"\n{'NAME':<24} {'TYPE':<10} {'STATUS':<11} {'ENV':<5} {'TIME':<5} {'DBG':<5} {'SKIP':<5} PATH")
    print("-" * 90)
    for a in apps:
        skip_str   = 'yes' if a['skip']        else '-'
        timing_str = 'yes' if a['timing']       else 'no'
        debug_str  = 'yes' if a['debug']        else 'no'
        envar_str  = 'yes' if a['envar_ready']  else 'no'
        path_str   = str(a['path']).replace(home, '~')
        print(f"{a['name']:<24} {a['type']:<10} {a['status']:<11} {envar_str:<5} {timing_str:<5} {debug_str:<5} {skip_str:<5} {path_str}")

    print(f"\n{len(apps)} app(s)")
    return 0


def cmd_fleet_add(name: str) -> int:
    """Interactively add a new app entry to awesome.rc."""
    rc_path = SCRIPT_DIR / 'awesome.rc'

    apps = load_fleet_config()
    if any(a['name'] == name for a in apps):
        error(f"App '{name}' already exists in awesome.rc")
        return 1

    msg(f"Adding '{name}' to awesome.rc")
    print()

    default_path = f"~/dev/{name}"
    path_in = input(f"  Path [{default_path}]: ").strip() or default_path

    valid_types = ['hook', 'script', 'wrapper', 'ui', 'core']
    type_in = ''
    while type_in not in valid_types:
        type_in = input(f"  Type [{'|'.join(valid_types)}] (default: hook): ").strip().lower()
        if not type_in:
            type_in = 'hook'
            break

    timing_in  = input("  Timing eligible? [y/N]: ").strip().lower()
    timing_val = 'yes' if timing_in in ('y', 'yes') else 'no'

    debug_in  = input("  Debug eligible? [Y/n]: ").strip().lower()
    debug_val = 'no' if debug_in in ('n', 'no') else 'yes'

    valid_statuses = ['release', 'testing', 'wip', 'suspended', 'archived']
    status_in = ''
    while status_in not in valid_statuses:
        status_in = input(f"  Status [{'|'.join(valid_statuses)}] (default: testing): ").strip().lower()
        if not status_in:
            status_in = 'testing'
            break

    envar_in  = input("  Envar-ready (TW_TASK_DIR)? [y/N]: ").strip().lower()
    envar_val = 'yes' if envar_in in ('y', 'yes') else 'no'

    skip_in   = input("  Skip (exclude from fleet ops)? [y/N]: ").strip().lower()
    skip_line = "skip        = yes\n" if skip_in in ('y', 'yes') else ''

    entry = (
        f"\n[{name}]\n"
        f"path        = {path_in}\n"
        f"type        = {type_in}\n"
        f"timing      = {timing_val}\n"
        f"debug       = {debug_val}\n"
        f"status      = {status_in}\n"
        f"envar_ready = {envar_val}\n"
        + skip_line
    )

    with open(rc_path, 'a') as f:
        f.write(entry)

    success(f"Added '{name}' to awesome.rc")
    return 0


def cmd_fleet_remove(name: str) -> int:
    """Remove an app entry from awesome.rc, registry.d, installers, and manifest."""
    removed_anything = False
    registry_files_removed = []  # track for git commit

    # Remove from awesome.rc (optional — app may only be in registry.d)
    rc_path = SCRIPT_DIR / 'awesome.rc'
    with open(rc_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    in_section = False
    found_in_rc = False

    for line in lines:
        if line.strip() == f'[{name}]':
            in_section = True
            found_in_rc = True
            continue
        if in_section:
            if line.startswith('[') and line.strip().endswith(']'):
                in_section = False
                new_lines.append(line)
            # else: skip (belongs to removed section)
        else:
            new_lines.append(line)

    if found_in_rc:
        with open(rc_path, 'w') as f:
            f.writelines(new_lines)
        success(f"Removed '{name}' from awesome.rc")
        registry_files_removed.append('awesome.rc')
        removed_anything = True
    else:
        msg(f"'{name}' not in awesome.rc (may be registry-only)")

    # Remove from registry.d/
    meta_path = SCRIPT_DIR / 'registry.d' / f'{name}.meta'
    if meta_path.exists():
        meta_path.unlink()
        success(f"Removed registry.d/{name}.meta")
        registry_files_removed.append(f'registry.d/{name}.meta')
        removed_anything = True
    else:
        msg(f"No registry.d/{name}.meta to remove")

    # Remove from installers/
    install_path = SCRIPT_DIR / 'installers' / f'{name}.install'
    if install_path.exists():
        install_path.unlink()
        success(f"Removed installers/{name}.install")
        registry_files_removed.append(f'installers/{name}.install')
        removed_anything = True
    else:
        msg(f"No installers/{name}.install to remove")

    # Remove from ~/.task/config/.tw_manifest (installed file records)
    manifest_path = Path.home() / '.task' / 'config' / '.tw_manifest'
    if manifest_path.exists():
        manifest_lines = manifest_path.read_text().splitlines(keepends=True)
        kept = [l for l in manifest_lines if not l.startswith(f'{name}|')]
        removed_count = len(manifest_lines) - len(kept)
        if removed_count:
            manifest_path.write_text(''.join(kept))
            success(f"Removed {removed_count} manifest entr{'y' if removed_count == 1 else 'ies'} for '{name}'")
            removed_anything = True
        else:
            msg(f"No manifest entries for '{name}' (not installed)")
    else:
        msg("No .tw_manifest found — skipping")

    if not removed_anything:
        error(f"App '{name}' not found anywhere — nothing removed")
        return 1

    # Commit registry changes so a git push is all that remains
    if registry_files_removed:
        msg("Committing registry changes...")
        _git(SCRIPT_DIR, 'add', '--', *registry_files_removed)
        r = _git(SCRIPT_DIR, 'commit', '-m', f"Remove {name} from registry")
        if r.returncode == 0:
            success("Registry commit done — run 'git push' to publish removal")
        else:
            warn("Git commit failed — changes are on disk but not committed")
            warn(r.stderr.strip() or r.stdout.strip())

    return 0


def _git(path: Path, *git_args) -> 'subprocess.CompletedProcess':
    """Run a git command in path, capturing output."""
    return subprocess.run(['git'] + list(git_args), cwd=path,
                         capture_output=True, text=True)


def check_meta_checksums(path: Path) -> str:
    """Compare .meta checksums against files on disk.
    Returns: 'ok', 'mismatch', 'no-meta', 'error'
    """
    meta_files = list(path.glob('*.meta'))
    if not meta_files:
        return 'no-meta'
    meta_text = meta_files[0].read_text()
    if 'checksums=' not in meta_text or 'files=' not in meta_text:
        return 'no-meta'
    files_line = next((l for l in meta_text.splitlines() if l.startswith('files=')), None)
    cs_line    = next((l for l in meta_text.splitlines() if l.startswith('checksums=')), None)
    if not files_line or not cs_line:
        return 'no-meta'
    file_entries     = [e.split(':')[0] for e in files_line[6:].split(',')]
    stored_checksums = cs_line[10:].split(',')
    if len(file_entries) != len(stored_checksums):
        return 'error'
    for fname, stored_sha in zip(file_entries, stored_checksums):
        try:
            actual_sha = hashlib.sha256((path / fname).read_bytes()).hexdigest()
            if actual_sha != stored_sha:
                return 'mismatch'
        except Exception:
            return 'error'
    return 'ok'


def recalculate_meta_checksums(path: Path) -> bool:
    """Recalculate checksums= in the project's .meta file (if one exists).

    Reads the files= list from the existing .meta, recomputes SHA256 for each
    file relative to path, and rewrites the checksums= line in place.
    Returns True if checksums were updated, False if skipped or failed.
    """
    meta_files = list(path.glob('*.meta'))
    if not meta_files:
        return False

    meta_file = meta_files[0]
    meta_text = meta_file.read_text()

    if 'checksums=' not in meta_text or 'files=' not in meta_text:
        return False

    files_line = next((l for l in meta_text.splitlines() if l.startswith('files=')), None)
    if not files_line:
        return False

    file_entries = [e.split(':')[0] for e in files_line[6:].split(',')]
    new_checksums = []
    for fname in file_entries:
        try:
            sha = hashlib.sha256((path / fname).read_bytes()).hexdigest()
            new_checksums.append(sha)
        except Exception as e:
            warn(f"  checksum failed for {fname}: {e}")
            return False

    new_cs_line = 'checksums=' + ','.join(new_checksums)
    new_meta = re.sub(r'^checksums=.*$', new_cs_line, meta_text, flags=re.MULTILINE)
    if new_meta != meta_text:
        meta_file.write_text(new_meta)
        msg(f"    checksums updated: {meta_file.name}")
        return True

    msg(f"    checksums unchanged: {meta_file.name}")
    return False


def cmd_fleet_push(apps: list, message: str, dry_run: bool = False) -> int:
    """Commit and push all dirty fleet repos, skipping .orig files."""
    results = []

    for app in apps:
        if app['skip']:
            continue

        name = app['name']
        path = app['path']

        if not path.is_dir():
            warn(f"  SKIP  [{name}]  path not found")
            results.append((name, 'SKIP', 'path not found'))
            continue

        # Must be a git repo
        if _git(path, 'rev-parse', '--git-dir').returncode != 0:
            warn(f"  SKIP  [{name}]  not a git repo")
            results.append((name, 'SKIP', 'not a git repo'))
            continue

        # Must have a remote
        if not _git(path, 'remote').stdout.strip():
            warn(f"  SKIP  [{name}]  no remote configured")
            results.append((name, 'SKIP', 'no remote'))
            continue

        # Must have an upstream branch
        if _git(path, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}').returncode != 0:
            warn(f"  SKIP  [{name}]  no upstream branch")
            results.append((name, 'SKIP', 'no upstream branch'))
            continue

        # Check dirty status, ignoring .orig files
        status_lines = _git(path, 'status', '--porcelain').stdout.splitlines()
        pushable = [l for l in status_lines if not l.rstrip().endswith('.orig')]

        if not pushable:
            msg(f"  SKIP  [{name}]  clean")
            results.append((name, 'SKIP', 'clean'))
            continue

        # Show what will be committed
        msg(f"\n  [{name}]  {path}")
        for line in pushable:
            print(f"    {line}")

        # Recalculate .meta checksums if a .meta file exists
        recalculate_meta_checksums(path)

        if dry_run:
            msg(f"    -> [dry-run] would commit: {message!r}")
            results.append((name, 'DRY-RUN', ''))
            continue

        msg(f"    -> commit: {message!r}")

        # Stage everything, then explicitly unstage .orig files
        _git(path, 'add', '-A')
        _git(path, 'reset', 'HEAD', '--', '*.orig')

        r = _git(path, 'commit', '-m', message)
        if r.returncode != 0:
            error(f"  FAIL  [{name}]  commit: {r.stderr.strip()}")
            results.append((name, 'FAIL', 'commit failed'))
            continue

        r = _git(path, 'push')
        if r.returncode != 0:
            error(f"  FAIL  [{name}]  push: {r.stderr.strip()}")
            results.append((name, 'FAIL', 'push failed'))
            continue

        success(f"  OK    [{name}]  pushed")
        results.append((name, 'OK', ''))

    # Summary
    print()
    prefix = "[dry-run] " if dry_run else ""
    msg(f"{prefix}Fleet push summary:")
    for name, status, note in results:
        note_str = f"  ({note})" if note else ''
        if status == 'OK':
            success(f"  {name}: {status}{note_str}")
        elif status in ('SKIP', 'DRY-RUN'):
            warn(f"  {name}: {status}{note_str}")
        else:
            error(f"  {name}: {status}{note_str}")

    failed = [r for r in results if r[1] == 'FAIL']

    # Sync registry.d in awesome-taskwarrior for all successfully pushed apps
    pushed = [app for app, status, _ in results if status == 'OK']
    if pushed and not dry_run:
        _sync_fleet_registry(apps, pushed, message)

    return 1 if failed else 0


def _sync_fleet_registry(apps: list, pushed_names: list, message: str):
    """Copy updated .meta (and .install) files into awesome-taskwarrior registry.d/installers/
    for each successfully pushed app, then commit+push the registry repo."""
    registry_path = SCRIPT_DIR
    registry_d   = registry_path / 'registry.d'
    installers_d = registry_path / 'installers'

    if not registry_d.exists():
        warn("registry.d not found — skipping registry sync")
        return

    synced = []
    app_map = {a['name']: a for a in apps}

    for name in pushed_names:
        app = app_map.get(name)
        if not app:
            continue
        path = app['path']

        meta_src = next(path.glob('*.meta'), None)
        if meta_src:
            shutil.copy2(meta_src, registry_d / meta_src.name)
            synced.append(f"registry.d/{meta_src.name}")

        install_src = next(path.glob('*.install'), None)
        if install_src and installers_d.exists():
            shutil.copy2(install_src, installers_d / install_src.name)
            synced.append(f"installers/{install_src.name}")

    if not synced:
        return

    msg(f"\n[registry] Syncing {len(synced)} file(s) to awesome-taskwarrior...")
    r = _git(registry_path, 'add', *synced)
    if _git(registry_path, 'diff', '--cached', '--quiet').returncode == 0:
        msg("[registry] No registry changes to commit")
        return

    r = _git(registry_path, 'commit', '-m', f"[fleet] registry sync: {message}")
    if r.returncode != 0:
        warn(f"[registry] commit failed: {r.stderr.strip()}")
        return

    r = _git(registry_path, 'push')
    if r.returncode != 0:
        warn(f"[registry] push failed: {r.stderr.strip()}")
    else:
        success(f"[registry] pushed ({len(pushed_names)} app(s) synced)")


def cmd_fleet_checksum(apps: list, dry_run: bool = False) -> int:
    """Recalculate .meta checksums across all fleet apps."""
    updated = skipped = missing = errors = 0

    for app in apps:
        if app['skip']:
            continue

        name = app['name']
        path = app['path']

        if not path.is_dir():
            warn(f"  MISS  [{name}]  path not found")
            errors += 1
            continue

        meta_files = list(path.glob('*.meta'))
        if not meta_files:
            msg(f"  --    [{name}]  no .meta file")
            missing += 1
            continue

        cs_before = check_meta_checksums(path)

        if dry_run:
            status_str = {'ok': 'already ok', 'mismatch': 'would update',
                          'no-meta': 'no .meta', 'error': 'error reading'}.get(cs_before, '?')
            if cs_before == 'mismatch':
                warn(f"  DRY   [{name}]  {status_str}")
            elif cs_before == 'ok':
                msg(f"  --    [{name}]  {status_str}")
            else:
                warn(f"  --    [{name}]  {status_str}")
            skipped += 1
            continue

        changed = recalculate_meta_checksums(path)
        if changed:
            success(f"  OK    [{name}]  checksums updated")
            updated += 1
        else:
            msg(f"  --    [{name}]  checksums already current")
            skipped += 1

    print()
    msg(f"Fleet checksum: updated={updated}  unchanged={skipped}  no-meta={missing}  errors={errors}")
    return 1 if errors else 0


def cmd_fleet(args) -> int:
    """Fleet management: status, list, add, remove, or apply stage(s) across all repos."""
    import os

    apps = load_fleet_config()
    if not apps:
        return 1

    do_timing    = getattr(args, 'timing',    False)
    do_debug     = getattr(args, 'debug',     False)
    do_checksum  = getattr(args, 'checksum',  False)
    dry_run      = getattr(args, 'dry_run',   False)
    list_pat     = getattr(args, 'list',      None)
    add_name     = getattr(args, 'add',       None)
    remove_name  = getattr(args, 'remove',    None)
    push_msg     = getattr(args, 'push',      None)

    # Sub-commands: list / add / remove (no stage ops)
    if list_pat is not None:
        return cmd_fleet_list(apps, list_pat)
    if add_name is not None:
        return cmd_fleet_add(add_name)
    if remove_name is not None:
        return cmd_fleet_remove(remove_name)
    if do_checksum and not do_timing and not do_debug and push_msg is None:
        return cmd_fleet_checksum(apps, dry_run=dry_run)

    # No flags at all → diagnostic / stats
    if not do_timing and not do_debug and push_msg is None:
        return cmd_fleet_status(apps)

    # Validate push message early if push is requested
    if push_msg is not None and not push_msg:
        error("--fleet --push requires a commit message: --fleet --push \"message\"")
        return 1

    # Stage flags → apply across fleet first (timing/debug before push)
    if do_timing or do_debug:
        origin  = Path.cwd()
        results = []

        for app in apps:
            if app['skip']:
                continue

            if do_timing and not app['timing']:
                continue
            if do_debug and not app['debug']:
                continue

            if not app['path'].is_dir():
                warn(f"[{app['name']}] path not found: {app['path']} -- skipping")
                results.append((app['name'], 'SKIP', 'path not found'))
                continue

            msg(f"\n--- [{app['name']}] {app['path']} ---")
            os.chdir(app['path'])

            rc = 0
            if do_timing:
                rc = cmd_timing(args)
            if rc == 0 and do_debug:
                rc = cmd_debug(args)

            results.append((app['name'], 'OK' if rc == 0 else 'FAIL', ''))

        os.chdir(origin)

        print()
        prefix = "[dry-run] " if dry_run else ""
        msg(f"{prefix}Fleet summary:")
        for name, status, note in results:
            note_str = f"  ({note})" if note else ''
            if status == 'OK':
                success(f"  {name}: {status}{note_str}")
            elif status == 'SKIP':
                warn(f"  {name}: {status}{note_str}")
            else:
                error(f"  {name}: {status}{note_str}")

        failed = [r for r in results if r[1] == 'FAIL']
        if failed:
            return 1

    # Checksum pass before push (if --checksum --push)
    if do_checksum and push_msg is not None:
        rc = cmd_fleet_checksum(apps, dry_run=dry_run)
        if rc != 0:
            return rc

    # Push — either standalone or after stage flags
    if push_msg is not None:
        return cmd_fleet_push(apps, push_msg, dry_run=dry_run)

    return 0


# ============================================================================
# Main
# ============================================================================

PIPELINE_ORDER = ['debug', 'testing', 'timing', 'envar', 'stdhelp', 'meta', 'install', 'push']


def main():
    parser = argparse.ArgumentParser(
        description='make-awesome.py - Full pipeline tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            f"Pipeline order: {' → '.join(PIPELINE_ORDER)}\n"
            "With commit message: runs full pipeline\n"
            "With flags: runs selected stages in pipeline order\n"
            "  e.g. make-awesome.py --meta --push 'update registry'"
        ),
    )

    parser.add_argument('commit_message', nargs='?',
                       help='Commit message — runs full pipeline')
    parser.add_argument('--debug', action='store_true',
                       help='Debug enhancement')
    parser.add_argument('--testing', action='store_true',
                       help='Run test suite [STUB]')
    parser.add_argument('--timing', action='store_true',
                       help='Inject TW_TIMING timing block')
    parser.add_argument('--envar', action='store_true',
                       help='Patch hardcoded ~/.task paths to use TW_TASK_DIR/TASKRC env vars')
    parser.add_argument('--stdhelp', action='store_true',
                       help='Standardise help output [STUB]')
    parser.add_argument('--meta', action='store_true',
                       help='Generate .meta file only')
    parser.add_argument('--install', action='store_true',
                       help='Generate .install (and .meta if run standalone)')
    parser.add_argument('--push', nargs='?', const='', default=None,
                       metavar='MESSAGE',
                       help='Git push + registry (message optional); with --fleet: commit+push all dirty repos (message required)')
    parser.add_argument('--force', action='store_true',
                       help='Force re-enhancement of already enhanced files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would happen without modifying files')
    parser.add_argument('--fleet', action='store_true',
                       help='Fleet management [fleet-mode only]')
    parser.add_argument('--list', nargs='?', const='', metavar='PATTERN',
                       help='List fleet apps, optional name filter [fleet-mode only]')
    parser.add_argument('--add', metavar='NAME',
                       help='Add a new app entry to awesome.rc [fleet-mode only]')
    parser.add_argument('--remove', metavar='NAME',
                       help='Remove an app entry from awesome.rc [fleet-mode only]')
    parser.add_argument('--checksum', action='store_true',
                       help='Recalculate .meta checksums across fleet [fleet-mode only]')
    parser.add_argument('--version', action='version',
                       version=f'v{VERSION}')

    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # Mode banner + guardrails
    # -------------------------------------------------------------------------
    fleet_flags   = args.fleet or args.list is not None or args.add or args.remove
    pipeline_flags = (args.commit_message or args.debug or args.testing or args.timing
                      or args.envar or args.stdhelp or args.meta or args.install
                      or args.push is not None)

    if IS_FLEET_MODE:
        msg(f"[fleet-mode] {SCRIPT_DIR}")
    else:
        msg(f"[project-mode] {Path.cwd().name}")

    if fleet_flags and not IS_FLEET_MODE:
        error(
            "Fleet commands (--fleet, --list, --add, --remove) require running from "
            f"the awesome-taskwarrior directory:\n"
            f"  cd {SCRIPT_DIR}"
        )
        return 1

    # -------------------------------------------------------------------------

    if args.commit_message:
        return cmd_pipeline(args.commit_message)

    if args.fleet or args.list is not None or args.add or args.remove:
        return cmd_fleet(args)

    # Collect requested steps in pipeline order
    def flag_set(name):
        if name == 'push':
            return args.push is not None
        return bool(getattr(args, name, False))

    steps = [s for s in PIPELINE_ORDER if flag_set(s)]

    if not steps:
        parser.print_help()
        return 1

    # Run steps in pipeline order; meta passes its info to install
    meta_info = None
    for step in steps:
        if step == 'debug':
            rc = cmd_debug(args)
        elif step == 'testing':
            rc = cmd_testing(args)
        elif step == 'timing':
            rc = cmd_timing(args)
        elif step == 'envar':
            rc = cmd_envar(args)
        elif step == 'stdhelp':
            rc = cmd_stdhelp(args)
        elif step == 'meta':
            rc, meta_info = cmd_meta(args)
        elif step == 'install':
            rc = cmd_install(args, info=meta_info)
            meta_info = None
        elif step == 'push':
            rc = cmd_push(args, args.push if args.push else None)

        if rc != 0:
            return rc

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        sys.exit(1)
