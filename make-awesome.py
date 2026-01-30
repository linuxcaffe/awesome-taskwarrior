#!/usr/bin/env python3
"""
make-awesome.py - Complete development-to-deployment pipeline for awesome-taskwarrior

This tool provides a full workflow from development through deployment:
- --debug: Enhance with debug infrastructure (tw --debug=2 compatible)
- --test: Run test suite (tw --test compatible) [STUB]
- --install: Generate .install and .meta files for registry
- --push: Git commit/push + registry update

Single command pipeline: make-awesome.py "commit message"
  Runs: debug Ã¢â€ â€™ test Ã¢â€ â€™ install Ã¢â€ â€™ push (each stage gated on previous success)

Version: 4.2.3
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

VERSION = "4.2.3"

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
    print(f"{Colors.GREEN}[make] Ã¢Å“â€œ{Colors.NC} {text}")

def error(text):
    print(f"{Colors.RED}[make] Ã¢Å“â€”{Colors.NC} {text}", file=sys.stderr)

def warn(text):
    print(f"{Colors.YELLOW}[make] Ã¢Å¡Â {Colors.NC} {text}")


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
                if f'import {skip}' in line or f'from {skip} ' in line:
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
        enhanced.append('# Determine log directory based on context\n')
        enhanced.append('def get_log_dir():\n')
        enhanced.append('    """Auto-detect dev vs production mode"""\n')
        enhanced.append('    cwd = Path.cwd()\n')
        enhanced.append('    \n')
        enhanced.append('    # Dev mode: running from project directory (has .git)\n')
        enhanced.append("    if (cwd / '.git').exists():\n")
        enhanced.append("        log_dir = cwd / 'logs' / 'debug'\n")
        enhanced.append('    else:\n')
        enhanced.append('        # Production mode\n')
        enhanced.append("        log_dir = Path.home() / '.task' / 'logs' / 'debug'\n")
        enhanced.append('    \n')
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
                if f'import {skip}' in line or f'from {skip} ' in line:
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
        enhanced.append('    cwd = Path.cwd()\n')
        enhanced.append("    if (cwd / '.git').exists():\n")
        enhanced.append("        log_dir = cwd / 'logs' / 'debug'\n")
        enhanced.append('    else:\n')
        enhanced.append("        log_dir = Path.home() / '.task' / 'logs' / 'debug'\n")
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


def process_python_file(filepath: str) -> bool:
    """Process a single Python file"""
    msg(f"Processing: {filepath}")
    
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
    
    force = args and hasattr(args, 'force') and args.force
    
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
            if not force and 'Auto-generated by make-awesome' in file.read():
                warn(f"Already enhanced: {f}")
                skipped += 1
                continue
        
        try:
            if process_python_file(f):
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
# INSTALL Generation
# ============================================================================

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
            info.repo = match.group(1).rstrip('.git')
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
    
    # Detect hooks (on-add*, on-exit*, on-modify*)
    for hook in ['on-add', 'on-exit', 'on-modify']:
        for ext in ['py', 'sh']:
            for f in Path('.').glob(f'{hook}*.{ext}'):
                if not f.name.startswith('debug.') and not f.name.endswith('.orig'):
                    if f.is_file():
                        files.append((f.name, 'hook'))
                        msg(f"  Hook: {f.name}")
    
    # Detect scripts - check ALL files in root directory for executables
    exclude_patterns = [
        'debug.',           # debug.* files
        '.orig',            # backup files
        'on-add',           # hooks (handled above)
        'on-modify',        # hooks
        'on-exit',          # hooks
        'make-awesome.py',  # this script itself
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
    
    print("Type: (1) hook, (2) script, (3) config, (4) theme")
    response = input("Select [1]: ").strip()
    type_map = {'1': 'hook', '2': 'script', '3': 'config', '4': 'theme'}
    info.type = type_map.get(response, 'hook')
    
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
    
    for filename, _ in files:
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
    
    files_list = ','.join([f"{name}:{ftype}" for name, ftype in info.files])
    checksums_list = ','.join(info.checksums)
    base_url = f"https://raw.githubusercontent.com/{info.repo}/{info.branch}/"
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
            f.write(f'BASE_URL="https://raw.githubusercontent.com/{info.repo}/{info.branch}/"\n\n')
            
            # Colors and helper functions
            f.write("# Colors\n")
            f.write("RED='\\033[0;31m'\n")
            f.write("GREEN='\\033[0;32m'\n")
            f.write("BLUE='\\033[0;34m'\n")
            f.write("NC='\\033[0m'\n\n")
            f.write('tw_msg() { echo -e "${BLUE}[tw]${NC} $*"; }\n')
            f.write('tw_success() { echo -e "${GREEN}[tw] Ã¢Å“â€œ${NC} $*"; }\n')
            f.write('tw_error() { echo -e "${RED}[tw] Ã¢Å“â€”${NC} $*" >&2; }\n\n')
            
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
            f.write('TASKRC="${HOME}/.taskrc"\n')
            f.write('TASK_DIR="${HOME}/.task"\n')
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
            
            # Separate files by type
            hooks = [(name, ftype) for name, ftype in info.files if ftype == 'hook']
            scripts = [(name, ftype) for name, ftype in info.files if ftype == 'script']
            configs = [(name, ftype) for name, ftype in info.files if ftype == 'config']
            docs = [(name, ftype) for name, ftype in info.files if ftype == 'doc']
            
            # Download hooks
            for filename, _ in hooks:
                f.write(f'    debug_msg "Downloading hook: {filename}" 2\n')
                f.write(f'    curl -fsSL "$BASE_URL/{filename}" -o "$HOOKS_DIR/{filename}" || {{\n')
                f.write(f'        tw_error "Failed to download {filename}"\n')
                f.write(f'        debug_msg "Download failed: {filename}" 1\n')
                f.write('        return 1\n')
                f.write('    }\n')
                f.write(f'    chmod +x "$HOOKS_DIR/{filename}"\n')
                f.write(f'    debug_msg "Installed hook: $HOOKS_DIR/{filename}" 2\n\n')
            
            # Download scripts
            for filename, _ in scripts:
                f.write(f'    debug_msg "Downloading script: {filename}" 2\n')
                f.write(f'    curl -fsSL "$BASE_URL/{filename}" -o "$SCRIPTS_DIR/{filename}" || {{\n')
                f.write(f'        tw_error "Failed to download {filename}"\n')
                f.write(f'        debug_msg "Download failed: {filename}" 1\n')
                f.write('        return 1\n')
                f.write('    }\n')
                f.write(f'    chmod +x "$SCRIPTS_DIR/{filename}"\n')
                f.write(f'    debug_msg "Installed script: $SCRIPTS_DIR/{filename}" 2\n\n')
            
            # Download configs
            for filename, _ in configs:
                f.write(f'    debug_msg "Downloading config: {filename}" 2\n')
                f.write(f'    curl -fsSL "$BASE_URL/{filename}" -o "$CONFIG_DIR/{filename}" || {{\n')
                f.write(f'        tw_error "Failed to download {filename}"\n')
                f.write(f'        debug_msg "Download failed: {filename}" 1\n')
                f.write('        return 1\n')
                f.write('    }\n')
                f.write(f'    debug_msg "Installed config: $CONFIG_DIR/{filename}" 2\n\n')
            
            # Add config to .taskrc if needed
            if configs:
                first_config = configs[0][0]
                f.write('    # Add config to .taskrc\n')
                f.write('    tw_msg "Adding configuration to .taskrc..."\n')
                f.write(f'    local config_line="include $CONFIG_DIR/{first_config}"\n\n')
                f.write('    if ! grep -qF "$config_line" "$TASKRC" 2>/dev/null; then\n')
                f.write('        echo "$config_line" >> "$TASKRC"\n')
                f.write('        tw_msg "Added config include to .taskrc"\n')
                f.write('        debug_msg "Added to .taskrc: $config_line" 2\n')
                f.write('    else\n')
                f.write('        tw_msg "Config already in .taskrc"\n')
                f.write('        debug_msg "Config already present in .taskrc" 2\n')
                f.write('    fi\n\n')
            
            # Download docs
            for filename, _ in docs:
                docname = f"{info.name}_{filename}"
                f.write('    tw_msg "Downloading documentation..."\n')
                f.write(f'    curl -fsSL "$BASE_URL/{filename}" -o "$DOCS_DIR/{docname}" 2>/dev/null || true\n')
                f.write(f'    debug_msg "Downloaded doc: $DOCS_DIR/{docname}" 2\n\n')
            
            # Manifest tracking
            f.write('    # Track in manifest\n')
            f.write('    debug_msg "Writing to manifest" 2\n')
            f.write('    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"\n')
            f.write('    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")\n')
            f.write('    mkdir -p "$(dirname "$MANIFEST_FILE")"\n\n')
            
            # Add manifest entries for each file
            for filename, ftype in info.files:
                if ftype == 'hook':
                    dir_var = '$HOOKS_DIR'
                elif ftype == 'script':
                    dir_var = '$SCRIPTS_DIR'
                elif ftype == 'config':
                    dir_var = '$CONFIG_DIR'
                elif ftype == 'doc':
                    dir_var = '$DOCS_DIR'
                    filename = f"{info.name}_{filename}"
                
                f.write(f'    echo "$APPNAME|$VERSION|{dir_var}/{filename}||$TIMESTAMP" >> "$MANIFEST_FILE"\n')
                f.write(f'    debug_msg "Manifest entry: {dir_var}/{filename}" 3\n')
            
            # Finish install function
            f.write('\n')
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
                f.write('    # Remove config from .taskrc\n')
                f.write(f'    local config_line="include $CONFIG_DIR/{first_config}"\n')
                f.write('    if grep -qF "$config_line" "$TASKRC" 2>/dev/null; then\n')
                f.write('        sed -i.bak "\\|$config_line|d" "$TASKRC"\n')
                f.write('        tw_msg "Removed config from .taskrc"\n')
                f.write('        debug_msg "Removed from .taskrc: $config_line" 2\n')
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


def cmd_install(args) -> int:
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --install")
    msg("=" * 70)
    print()
    
    info = detect_project_info()
    print()
    
    info.files = detect_files()
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
# TEST (Stub)
# ============================================================================

def cmd_test(args) -> int:
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --test")
    msg("=" * 70)
    print()
    warn("Test infrastructure not yet implemented")
    print()
    return 0


# ============================================================================
# PUSH (Git + Registry)
# ============================================================================

def check_git_status() -> bool:
    try:
        result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            # Parse git status format: "XY filename"
            # X = index status, Y = working tree status
            lines = result.stdout.strip().split('\n')
            
            changed_files = []
            for line in lines:
                if not line.strip():
                    continue
                # Git status format: first 2 chars are status, rest is filename
                filename = line[3:].strip() if len(line) > 3 else ""
                if filename:
                    changed_files.append(filename)
            
            # Check if it's ONLY .install and .meta files (expected from --install stage)
            only_registry_files = all(
                fname.endswith('.install') or fname.endswith('.meta')
                for fname in changed_files
            )
            
            if only_registry_files and changed_files:
                msg("Found new .install and .meta files (expected from --install stage)")
                return True
            else:
                error("Git working directory not clean!")
                print(result.stdout)
                response = input("Continue? [y/N]: ").strip().lower()
                return response == 'y'
        return True
    except:
        error("Git status check failed")
        return False


def git_commit_and_push(commit_msg: str) -> bool:
    try:
        # Show what will be added
        msg("Files to be committed:")
        result = subprocess.run(['git', 'status', '--short'], 
                              capture_output=True, text=True, check=True)
        
        if not result.stdout.strip():
            msg("Working tree clean, nothing to commit")
            msg("Skipping git commit (but will update registry)")
            return True  # Success - proceed to registry update
        
        print(result.stdout)
        
        # Confirm git add
        response = input("Run 'git add .'? [Y/n]: ").strip().lower()
        if response and response != 'y':
            msg("Skipping git add, using staged files only")
        else:
            msg("Git add...")
            subprocess.run(['git', 'add', '.'], check=True)
        
        msg(f"Commit: {commit_msg}")
        result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            # Check if it's "nothing to commit"
            if 'nothing to commit' in result.stdout or 'nothing to commit' in result.stderr:
                msg("Nothing to commit, working tree clean")
                msg("Skipping git push (but will update registry)")
                return True  # Success - proceed to registry update
            else:
                error("Git commit failed")
                print(result.stderr)
                return False
        
        msg("Push...")
        subprocess.run(['git', 'push'], check=True)
        
        success("Git push complete")
        return True
    except Exception as e:
        error(f"Git failed: {e}")
        return False


def update_registry(project_name: str) -> bool:
    registry_path = Path.home() / 'dev' / 'awesome-taskwarrior'
    
    if not registry_path.exists():
        error(f"Registry not found: {registry_path}")
        return False
    
    # Save current directory before changing
    original_dir = Path.cwd()
    
    install_file = original_dir / f"{project_name}.install"
    meta_file = original_dir / f"{project_name}.meta"
    
    if not install_file.exists() or not meta_file.exists():
        error("Install/meta files not found")
        error(f"  Looking for: {install_file}")
        error(f"  Looking for: {meta_file}")
        return False
    
    try:
        import shutil
        msg("Copying to registry...")
        shutil.copy(install_file, registry_path / 'installers' / install_file.name)
        shutil.copy(meta_file, registry_path / 'registry.d' / meta_file.name)
        success("Copied files")
        
        msg("Updating registry...")
        os.chdir(registry_path)
        
        # Add only the specific files we care about
        subprocess.run(['git', 'add',
                       f'installers/{install_file.name}',
                       f'registry.d/{meta_file.name}'], check=True)
        
        # Commit with --only to ignore other changes in working tree
        result = subprocess.run(['git', 'commit', '--only', '-m',
                               f"Updated registry for {project_name}",
                               f'installers/{install_file.name}',
                               f'registry.d/{meta_file.name}'],
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            # Check if it's "nothing to commit" (files unchanged)
            if 'nothing to commit' in result.stdout or 'nothing to commit' in result.stderr:
                msg("Registry files unchanged, nothing to commit")
                msg("Skipping registry push")
                os.chdir(original_dir)
                return True  # Success - files already in registry
            else:
                error("Registry commit failed")
                print(result.stderr)
                os.chdir(original_dir)
                return False
        
        subprocess.run(['git', 'push'], check=True)
        
        success("Registry updated")
        
        # Return to original directory
        os.chdir(original_dir)
        return True
        
    except Exception as e:
        error(f"Registry update failed: {e}")
        # Make sure we return to original directory even on error
        try:
            os.chdir(original_dir)
        except:
            pass
        return False


def cmd_push(args, commit_msg: str) -> int:
    msg("=" * 70)
    msg(f"make-awesome.py v{VERSION} --push")
    msg("=" * 70)
    print()
    
    # Get project name from .meta file, not directory name
    # (directory might be "tw-need_priority-hook" but app is "need-priority")
    meta_files = list(Path('.').glob('*.meta'))
    if not meta_files:
        error("No .meta file found. Run --install first.")
        return 1
    
    meta_file = meta_files[0]
    project_name = meta_file.stem  # e.g., "need-priority" from "need-priority.meta"
    msg(f"Project: {project_name}")
    
    if not check_git_status():
        return 1
    
    if not git_commit_and_push(commit_msg):
        return 1
    
    print()
    
    if not update_registry(project_name):
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
    
    msg("STAGE 1/4: Debug")
    if cmd_debug(None) != 0:
        error("Debug failed")
        return 1
    print()
    
    msg("STAGE 2/4: Test")
    cmd_test(None)
    print()
    
    msg("STAGE 3/4: Install")
    if cmd_install(None) != 0:
        error("Install failed")
        return 1
    print()
    
    msg("STAGE 4/4: Push")
    if cmd_push(None, commit_msg) != 0:
        error("Push failed")
        return 1
    print()
    
    msg("=" * 70)
    success("PIPELINE COMPLETE!")
    msg("=" * 70)
    print()
    
    return 0


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='make-awesome.py - Full pipeline tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('commit_message', nargs='?',
                       help='Commit message (runs full pipeline)')
    parser.add_argument('--debug', action='store_true',
                       help='Debug enhancement')
    parser.add_argument('--test', action='store_true',
                       help='Test suite [STUB]')
    parser.add_argument('--install', action='store_true',
                       help='Generate installer')
    parser.add_argument('--push', metavar='MESSAGE',
                       help='Git push + registry')
    parser.add_argument('--force', action='store_true',
                       help='Force re-enhancement of already enhanced files')
    parser.add_argument('--version', action='version',
                       version=f'v{VERSION}')
    
    args = parser.parse_args()
    
    if args.commit_message:
        return cmd_pipeline(args.commit_message)
    elif args.debug:
        return cmd_debug(args)
    elif args.test:
        return cmd_test(args)
    elif args.install:
        return cmd_install(args)
    elif args.push:
        return cmd_push(args, args.push)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
