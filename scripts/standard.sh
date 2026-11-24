#!/usr/bin/env bash
# standard.sh — fleet sweep of `mimus standard` over every clone.
#
# Each repo is checked against the union of:
#   specs/                — workspace pack (9aia/base floor)
#   repos/<name>/specs/   — the repo's own spec (its family delta)
#
# Usage:
#   scripts/standard.sh              # whole fleet
#   scripts/standard.sh tamias kuda  # subset
#   MIMUS=/path/to/mimus scripts/standard.sh
#
# Exit 0 when every repo passes or only warns; exit 1 on any
# fail-severity violation. Requires a `mimus` binary (cargo install
# --git https://github.com/9aia/mimus mimus, or the dev build at
# repos/mimus/target/debug/mimus).
set -uo pipefail

WS="$(cd "$(dirname "$0")/.." && pwd)"
MIMUS="${MIMUS:-$(command -v mimus 2>/dev/null || true)}"
[ -n "$MIMUS" ] || MIMUS="$WS/repos/mimus/target/debug/mimus"
[ -x "$MIMUS" ] || { echo "mimus binary not found — set MIMUS=" >&2; exit 2; }

names=()
if [ "$#" -gt 0 ]; then
  names=("$@")
else
  for d in "$WS"/repos/*/ "$WS"/repos/.[!.]*/; do
    n="$(basename "$d")"
    [ -e "$d/.git" ] && names+=("$n")
  done
fi

fail=0
for n in "${names[@]}"; do
  # archived repos are read-only reference clones — exempt
  [ "$n" = "strigi" ] && { echo "skip $n (archived)"; continue; }
  repo="$WS/repos/$n"
  [ -d "$repo" ] || { echo "skip $n (no clone)"; continue; }
  specs=("$WS/specs")
  [ -d "$repo/specs" ] && specs+=("$repo/specs")
  spec_args=()
  for s in "${specs[@]}"; do spec_args+=(--spec "$s"); done
  out="$("$MIMUS" standard --repo "$repo" "${spec_args[@]}" 2>&1)"
  rc=$?
  # warn-severity violations exit 0 but still print — surface them
  if [ $rc -ne 0 ] || grep -q "WARN" <<<"$out"; then
    [ $rc -ne 0 ] && fail=1
    echo "=== $n (rc=$rc) ==="
    echo "$out" | sed 's/^/  /'
  else
    echo "ok   $n"
  fi
done
exit $fail
