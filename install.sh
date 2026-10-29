#!/usr/bin/env bash
# awesome-taskwarrior bootstrap: installs tw, which installs everything else.
#
#   curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/install.sh | bash
#
# Puts tw in ~/.task/scripts and offers to add that folder to your PATH. Doesn't need Taskwarrior:
# without it, tw still runs, and this says where to get 2.6.2. Desktop Linux or Termux.
# Questions are read from the terminal; with none (a pipe in CI, ssh without -t), each takes its default.
#
# Everything runs from main, called on the last line: a download cut short runs nothing.

set -euo pipefail

RAW_BASE="https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main"
TW26_URL="https://github.com/linuxcaffe/taskwarrior-2.6"
TASK_DIR="$HOME/.task"
SCRIPTS_DIR="$TASK_DIR/scripts"
TMP=""   # a download in progress, removed on exit

say()  { printf '%s\n' "$*"; }
ok()   { printf '  ok    %s\n' "$*"; }
warn() { printf '  warn  %s\n' "$*"; }
fail() { printf '  FAIL  %s\n' "$*" >&2; exit 1; }

is_termux() { [ -n "${TERMUX_VERSION:-}" ] || [[ "${PREFIX:-}" == /data/data/com.termux* ]]; }

# ask "question" default(y|n): 0 for yes. Reads the terminal, not stdin (stdin is this script under curl | bash).
ask() {
    local q=$1 def=$2 hint reply
    [ "$def" = y ] && hint="Y/n" || hint="y/N"
    if { exec 3</dev/tty; } 2>/dev/null; then
        printf '%s [%s] ' "$q" "$hint" >/dev/tty
        read -r reply <&3 || reply=""
        exec 3<&-
    else
        say "$q [$hint] (no terminal: taking the default, $def)"
        reply=""
    fi
    reply=${reply:-$def}
    [[ $reply =~ ^[Yy] ]]
}

need() {  # need command termux-package
    command -v "$1" >/dev/null 2>&1 && return 0
    if is_termux; then
        fail "$1 not found: pkg install $2, then run this again"
    else
        fail "$1 not found: install it with your package manager, then run this again"
    fi
}

shell_rc() {
    case "${SHELL##*/}" in
        zsh) printf '%s' "$HOME/.zshrc" ;;
        *)   printf '%s' "$HOME/.bashrc" ;;
    esac
}

main() {
    say "awesome-taskwarrior: installing tw"
    say ""

    need python3 python
    need curl curl
    ok "python3 and curl"

    mkdir -p "$SCRIPTS_DIR" "$TASK_DIR/docs" "$TASK_DIR/config"

    # Download beside the target, then move: never leaves a half-written tw
    TMP="$SCRIPTS_DIR/.tw.download.$$"
    trap '[ -z "$TMP" ] || rm -f "$TMP"' EXIT
    curl -fsSL "$RAW_BASE/tw" -o "$TMP" || fail "could not download $RAW_BASE/tw"
    chmod +x "$TMP"
    local out
    out=$(python3 "$TMP" -v 2>&1) || fail "the downloaded tw doesn't run: $out"
    mv -f "$TMP" "$SCRIPTS_DIR/tw"
    TMP=""
    [[ $out =~ tw\ v([0-9]+\.[0-9]+\.[0-9]+) ]] && out=" ${BASH_REMATCH[1]}" || out=""
    ok "tw$out in $SCRIPTS_DIR/tw"

    if curl -fsSL "$RAW_BASE/README.md" -o "$TASK_DIR/docs/tw_README.md"; then
        ok "documentation in $TASK_DIR/docs/tw_README.md"
    else
        warn "couldn't download the README (not needed)"
    fi

    # PATH
    local rc line='export PATH="$HOME/.task/scripts:$PATH"'
    rc=$(shell_rc)
    if [[ ":$PATH:" == *":$SCRIPTS_DIR:"* ]]; then
        ok "$SCRIPTS_DIR is on your PATH"
    elif [ -f "$rc" ] && grep -qF '.task/scripts' "$rc"; then
        ok "$rc already adds $SCRIPTS_DIR to PATH (open a new shell, or: source $rc)"
    elif ask "Add $SCRIPTS_DIR to your PATH in $rc?" y; then
        printf '\n# awesome-taskwarrior\n%s\n' "$line" >> "$rc"
        ok "added to $rc (open a new shell, or: source $rc)"
    else
        warn "$SCRIPTS_DIR is not on your PATH; add this to your shell's rc file: $line"
    fi

    # Taskwarrior
    say ""
    local v first=""
    v=$(task --version 2>/dev/null | head -1 || true)
    case "$v" in
        2.6.*)
            ok "Taskwarrior $v" ;;
        "")
            warn "Taskwarrior is not installed. tw works without it; the tools it installs need it."
            say "        Get Taskwarrior 2.6.2 (Termux or Linux): $TW26_URL"
            first="  first: Taskwarrior 2.6.2, from $TW26_URL" ;;
        *)
            warn "Taskwarrior $v is installed. awesome-taskwarrior is written for 2.6.2, not 3.x:"
            say "        3.x keeps its data differently, and the hooks and tools here aren't tested with it."
            say "        Getting 2.6.2 back (save your tasks first): $TW26_URL" ;;
    esac

    say ""
    say "Done. Next:"
    [ -n "$first" ] && say "$first"
    say "  tw -l          what tw can install"
    say "  tw -I <app>    install one"
    say "  tw -h          everything else"
    say "To update tw itself later, run this installer again."
}

main "$@"
