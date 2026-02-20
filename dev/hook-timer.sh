#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  hook-timer.sh [--hooks DIR] [--log FILE] [--keep] -- <command...>
  hook-timer.sh <command...>

Options:
  --hooks DIR  Hooks directory (default: task show data.location + /hooks)
  --log FILE   Log file (default: ~/.task/hook-timer.log)
  --keep       Keep temp workspace (debug)
  --           End of options; everything after is the command to run

Examples:
  ./hook-timer.sh -- task add test +x
  ./hook-timer.sh --hooks ~/.task/hooks -- tw @_ add test +x
EOF
}

logfile="$HOME/.task/hook-timer.log"
keep=0
hooks_dir=""

args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --log)
      shift
      logfile="${1:-}"
      [[ -n "$logfile" ]] || { echo "Error: --log needs a filename"; exit 2; }
      ;;
    --hooks)
      shift
      hooks_dir="${1:-}"
      [[ -n "$hooks_dir" ]] || { echo "Error: --hooks needs a directory"; exit 2; }
      ;;
    --keep) keep=1 ;;
    --)
      shift
      args+=("$@")
      break
      ;;
    *)
      args+=("$1")
      ;;
  esac
  shift || true
done

if [[ ${#args[@]} -lt 1 ]]; then
  usage
  exit 2
fi

mkdir -p "$(dirname "$logfile")"

now_ns() {
  date +%s%N 2>/dev/null || python3 -c 'import time; print(int(time.time()*1e9))'
}

# ---- determine hooks dir if not provided ----
if [[ -z "$hooks_dir" ]]; then
  data_location="$(task show data.location 2>/dev/null | tail -n1 | tr -d '\r')"
  hooks_dir="$data_location/hooks"
fi

if [[ ! -d "$hooks_dir" ]]; then
  echo "Hooks dir not found: $hooks_dir"
  exit 1
fi

# ---- workspace ----
workdir="$(mktemp -d)"
backup="$workdir/hooks.backup"
instrumented="$workdir/hooks.instrumented"
moved_original="$workdir/hooks.original.moved"

cleanup() {
  # If we swapped hooks_dir out, restore it.
  if [[ -d "$moved_original" ]]; then
    # remove instrumented hooks dir (which lives at hooks_dir)
    # IMPORTANT: this is safe because it is the instrumented copy, not the real one.
    rm -rf "$hooks_dir"
    mv "$moved_original" "$hooks_dir"
  fi

  if [[ "$keep" -eq 0 ]]; then
    rm -rf "$workdir"
  else
    echo
    echo "(kept workspace: $workdir)"
  fi
}
trap cleanup EXIT INT TERM

# ---- copy hooks to backup and to instrumented ----
# We copy rather than move so we never touch your real dir until swap time.
cp -a "$hooks_dir" "$backup"
cp -a "$hooks_dir" "$instrumented"

# ---- run marker ----
run_id="$(date +%Y%m%d-%H%M%S)-$$"
start_iso="$(date -Is)"
{
  echo "# ------------------------------------------------------------"
  echo "# RUN START  id=$run_id  time=$start_iso"
  echo "# cmd: ${args[*]}"
  echo "# format: epoch_ms<TAB>dur_ms<TAB>hookpath<TAB>run_id"
} >> "$logfile"

# ---- instrument hooks in the instrumented copy ----
# We wrap any executable file OR executable symlink.
# We do it recursively, because your hooks dir contains subdirs.
wrapped=0

# Use find -print0 to handle spaces safely.
while IFS= read -r -d '' f; do
  # Only wrap if it's executable
  [[ -x "$f" ]] || continue

  rel="${f#$instrumented/}"
  real="$f.real"

  # If something is already .real, skip
  [[ "$f" == *.real ]] && continue

  # Move original aside
  mv "$f" "$real"

  # Create wrapper
  cat > "$f" <<EOF
#!/usr/bin/env bash
set -euo pipefail

hookpath="$rel"
logfile="$logfile"
run_id="$run_id"

now_ns() {
  date +%s%N 2>/dev/null || python3 -c 'import time; print(int(time.time()*1e9))'
}

start_ns=\$(now_ns)

# Call the real hook
"$real" "\$@"
rc=\$?

end_ns=\$(now_ns)
dur_ms=\$(( (end_ns - start_ns) / 1000000 ))
epoch_ms=\$(( end_ns / 1000000 ))

printf "%s\t%s\t%s\t%s\n" "\$epoch_ms" "\$dur_ms" "\$hookpath" "\$run_id" >> "\$logfile"

exit \$rc
EOF

  chmod +x "$f"
  wrapped=$((wrapped + 1))

done < <(find "$instrumented" \( -type f -o -type l \) -print0)

# ---- swap hooks dir ----
# Move your real hooks dir out of the way, and put the instrumented one in place.
mv "$hooks_dir" "$moved_original"
mv "$instrumented" "$hooks_dir"

echo "Hook timer: wrapped $wrapped executable hook file(s) (recursive)"
echo "Hooks dir : $hooks_dir"
echo "Log file  : $logfile"
echo
echo "Running:"
printf "  %q " "${args[@]}"
echo
echo

# ---- run command with wall-clock timing ----
cmd_start_ns="$(now_ns)"

set +e
"${args[@]}"
cmd_rc=$?
set -e

cmd_end_ns="$(now_ns)"
cmd_wall_ms=$(( (cmd_end_ns - cmd_start_ns) / 1000000 ))

echo
echo "Exit code: $cmd_rc"
echo

# ---- run end marker ----
end_iso="$(date -Is)"
{
  echo "# RUN END    id=$run_id  time=$end_iso  exit=$cmd_rc  wall_ms=$cmd_wall_ms"
  echo "# ------------------------------------------------------------"
} >> "$logfile"

# ---- compute hook totals for this run ----
hook_total_ms="$(
  awk -F'\t' -v run="$run_id" '
  $0 ~ /^#/ { next }
  NF >= 4 && $4 == run { sum += ($2+0) }
  END { printf "%.0f", sum+0 }
  ' "$logfile"
)"

non_hook_ms=$((cmd_wall_ms - hook_total_ms))
if [[ "$non_hook_ms" -lt 0 ]]; then
  non_hook_ms=0
fi

echo "Timing breakdown:"
echo "----------------------------------------"
printf "Wall time        : %d ms\n" "$cmd_wall_ms"
printf "Total hook time  : %d ms\n" "$hook_total_ms"
printf "Non-hook time    : %d ms\n" "$non_hook_ms"
echo "----------------------------------------"
echo

echo "Hook calls for this run:"
echo "----------------------------------------"
awk -F'\t' -v run="$run_id" '
$0 ~ /^#/ { next }
NF >= 4 && $4 == run {
  dur=$2+0
  hook=$3
  printf "%7dms  %s\n", dur, hook
}' "$logfile"
echo "----------------------------------------"
echo

echo "Summary:"
awk -F'\t' -v run="$run_id" '
$0 ~ /^#/ { next }
NF >= 4 && $4 == run {
  dur=$2+0
  hook=$3
  count[hook]++
  total[hook]+=dur
  if (dur > max[hook]) max[hook]=dur
}
END {
  printf "%-45s %7s %10s %10s %10s\n", "hook", "count", "total_ms", "avg_ms", "max_ms"
  for (h in count) {
    avg = total[h] / count[h]
    printf "%-45s %7d %10d %10.1f %10d\n", h, count[h], total[h], avg, max[h]
  }
}' "$logfile" | sort -k3 -n

echo
echo "Top 10 slowest single calls:"
awk -F'\t' -v run="$run_id" '
$0 ~ /^#/ { next }
NF >= 4 && $4 == run {
  dur=$2+0
  hook=$3
  printf "%10d\t%s\n", dur, hook
}' "$logfile" | sort -n | tail -n 10 | awk -F'\t' '{ printf "%7dms  %s\n", $1, $2 }'

# ---- restore happens in trap cleanup ----
exit "$cmd_rc"

