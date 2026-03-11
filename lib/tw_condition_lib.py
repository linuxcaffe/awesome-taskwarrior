#!/usr/bin/env python3
"""
tw_condition_lib.py - Shared condition/token utilities for sanity-check, smart-nag, etc.
Version: 0.1.0

Provides:
  - Date utilities:       tw_to_date, fmt_date, age_str
  - Token substitution:   compute_action  (<field>, <field±offset>, <field.age>, {count})
  - RC loading:           load_rc         (condition.X.* blocks, include-chain aware)
  - Task sorting:         sort_tasks      (multi-key: 'due+,urgency-')
  - ANSI constants:       TOKEN_COLOR, RESET

Usage (dev time, from project directory):
    import sys, os
    sys.path.insert(0, os.path.expanduser('~/dev/awesome-taskwarrior/lib'))
    from tw_condition_lib import compute_action, load_rc, sort_tasks

Usage (installed):
    sys.path.insert(0, os.path.expanduser('~/.task/scripts'))
    from tw_condition_lib import compute_action, load_rc, sort_tasks
"""

import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional


# ── ANSI ─────────────────────────────────────────────────────────────────────

TOKEN_COLOR = '\033[33m'   # yellow — substituted token values in display text
RESET       = '\033[0m'


# ── Date utilities ────────────────────────────────────────────────────────────

def tw_to_date(tw_date: str) -> Optional[date]:
    """Parse a Taskwarrior date string (YYYYMMDD or ISO) to a date object."""
    if not tw_date:
        return None
    try:
        return datetime.strptime(tw_date[:8], '%Y%m%d').date()
    except (ValueError, TypeError):
        return None


def fmt_date(tw_date: str) -> str:
    """Format a TW date string as YYYY-MM-DD, or '' if unparseable."""
    d = tw_to_date(tw_date)
    return d.strftime('%Y-%m-%d') if d else ''


def age_str(tw_date: str) -> str:
    """Return a human-readable age: 'today', '3d ago', 'in 2w', etc."""
    d = tw_to_date(tw_date)
    if not d:
        return ''
    delta = (date.today() - d).days
    if delta == 0:   return 'today'
    elif delta > 0:  return f'{delta}d ago'
    else:            return f'in {-delta}d'


# ── Token substitution ────────────────────────────────────────────────────────

_OFFSET_RE = re.compile(r'<([\w.]+?)([+-]\d+[dwmy])?>')


def compute_action(template: str, task: dict, colorize: bool = False,
                   count: int = 0) -> str:
    """Interpolate tokens in a template string using task field values.

    Supported tokens:
      <field>           — direct field substitution (string or date → YYYY-MM-DD)
      <field±Nd/w/m/y>  — date field with offset, e.g. <due+1w>
      <field.age>       — human-readable age of a date field, e.g. <entry.age>
      {count}           — integer count (supplied by caller)

    colorize=True wraps substituted values in TOKEN_COLOR for display use.
    Unresolvable tokens (field absent or unparseable) are left as-is.
    """
    if not template:
        return ''

    # {count} substitution first (simple replace, no regex needed)
    result = template.replace('{count}', str(count))

    def _wrap(val: str) -> str:
        return f'{TOKEN_COLOR}{val}{RESET}' if colorize else val

    def _replace(m):
        token  = m.group(1)
        offset = m.group(2) or ''

        # <field.age> — human-readable magnitude of a date field
        if token.endswith('.age'):
            base = tw_to_date(task.get(token[:-4], ''))
            if not base:
                return m.group(0)
            days = (date.today() - base).days
            if days < 7:     mag = f'{days}d'
            elif days < 30:  mag = f'{days // 7}w'
            elif days < 365: mag = f'{days // 30}mo'
            else:            mag = f'{days // 365}y'
            return _wrap(mag)

        if token == 'today':
            base = date.today()
        else:
            val = task.get(token, '')
            if not val:
                return m.group(0)
            base = tw_to_date(val)
            if base is None:
                # Non-date string field — substitute directly, offset not applicable
                return _wrap(str(val)) if not offset else m.group(0)

        if offset:
            sign = 1 if offset[0] == '+' else -1
            num  = int(offset[1:-1])
            unit = offset[-1]
            days = {'d': num, 'w': num * 7, 'm': num * 30, 'y': num * 365}[unit]
            base = base + timedelta(days=days * sign)
        return _wrap(base.strftime('%Y-%m-%d'))

    return _OFFSET_RE.sub(_replace, result)


# ── Condition loading ─────────────────────────────────────────────────────────

def load_rc(rc_file, app_prefix: str = '', _visited: Optional[set] = None) -> tuple:
    """Parse an rc file for condition blocks, following include directives.

    Any key starting with 'condition.' is collected into an ordered conditions list.
    Any key starting with '{app_prefix}.' (if app_prefix is set) is stripped of the
    prefix and added to global_cfg — e.g. app_prefix='sanity' stores 'sanity.foo'
    as global_cfg['foo'].  If app_prefix='' all non-condition keys are stored as-is.

    Circular includes are silently ignored.

    Returns:
        (global_cfg dict, conditions list)
        global_cfg   — settings keyed without prefix
        conditions   — list of dicts, each with 'name' + arbitrary keys from
                       condition.NAME.KEY = VALUE lines; order = file order,
                       first definition of each name wins across includes
    """
    if _visited is None:
        _visited = set()

    rc_file = Path(rc_file).expanduser().resolve()
    if rc_file in _visited or not rc_file.exists():
        return {}, []
    _visited.add(rc_file)

    global_cfg = {}
    raw        = {}   # name → dict
    order      = []   # names in file order

    prefix_dot = f'{app_prefix}.' if app_prefix else ''

    with rc_file.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('include '):
                inc_path = Path(line.split(None, 1)[1].strip()).expanduser()
                sub_cfg, sub_conds = load_rc(inc_path, app_prefix, _visited)
                for k, v in sub_cfg.items():
                    global_cfg.setdefault(k, v)   # first (caller's) definition wins
                for cond in sub_conds:
                    if cond['name'] not in raw:
                        raw[cond['name']] = cond
                        order.append(cond['name'])
                continue
            if '=' not in line:
                continue
            k, _, v = line.partition('=')
            k = k.strip()
            v = v.split('#')[0].strip()

            if k.startswith('condition.'):
                parts = k.split('.', 2)   # ['condition', name, attr]
                if len(parts) != 3:
                    continue
                _, name, attr = parts
                if name not in raw:
                    raw[name] = {'name': name}
                    order.append(name)
                raw[name][attr] = v
            elif prefix_dot and k.startswith(prefix_dot):
                global_cfg[k[len(prefix_dot):]] = v
            elif not prefix_dot:
                global_cfg[k] = v

    return global_cfg, [raw[n] for n in order]


# ── Task sorting ──────────────────────────────────────────────────────────────

def sort_tasks(tasks: list, sort_str: str) -> list:
    """Sort tasks by a comma-separated TW-style sort spec, e.g. 'due+,urgency-'.

    Each key: FIELD[+|-]  where + = ascending (default), - = descending.
    Keys are applied right-to-left (last = least significant) for stable multi-key sort.
    Missing field values sort last regardless of direction.
    """
    if not sort_str or not tasks:
        return list(tasks)

    result = list(tasks)
    keys = [k.strip() for k in sort_str.split(',') if k.strip()]

    for key_spec in reversed(keys):
        reverse = key_spec.endswith('-')
        field   = key_spec.rstrip('+-')

        # Detect field type from first task that has the field
        numeric = False
        for t in result:
            v = t.get(field)
            if v is not None:
                numeric = isinstance(v, (int, float))
                break

        if numeric:
            result = sorted(result,
                key=lambda t, f=field: (0, float(t.get(f) or 0)),
                reverse=reverse)
        else:
            result = sorted(result,
                key=lambda t, f=field: (0 if t.get(f) else 1, str(t.get(f) or '')),
                reverse=reverse)

    return result
