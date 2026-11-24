#!/usr/bin/env bash
# ci-standard.sh — `mimus standard` conformance leg for gated repos.
#
# Shipped inside the 9aia-standard tamias pack; each repo's
# scripts/ci.sh installs the pack (`tamias install
# git:github.com/9aia/workspace//libraries/9aia-standard`, cache-hit
# cheap after the first fetch) and execs this file from the store
# payload. It also runs standalone: `bash ci-standard.sh` from a
# repo root uses the specs/ next to this script.
#
# Runs inside the pushed-sha worktree. Two adaptations vs the
# workspace sweep (scripts/standard.sh):
#
#   * Spec sources: this pack's specs/ (the 9aia/base floor plus
#     every org family spec, union-matched) plus the repo's own
#     specs/ dir when present — repo files shadow pack copies by
#     filename, so an unsynced pack can't weaken the delta.
#   * Repo name: bupha worktrees are named
#     <base>-<org>-<repo>-<sha>, so mimus's basename-derived repo
#     name never equals a spec's `match` glob and family specs
#     would silently not apply. We therefore build a temp spec dir
#     where every spec whose `match` globs cover THIS repo gets
#     `match = []` — selection already happened here; mimus just
#     applies them. Specs that don't match keep their globs and are
#     skipped by mimus exactly as in the sweep.
#
# Tooling: `mimus` and `python3` on PATH (the ci.sh leg checks both
# before calling). Env overrides: MIMUS (binary path),
# MIMUS_REPO_NAME (skip remote detection), MIMUS_STANDARD_PACK_DIR
# (specs source — defaults to the dir holding this script).
#
# Exit: mimus's own code — 0 pass/warn-only, nonzero on fail-
# severity violations (the gate fails). Missing mimus/python3 is a
# hard error here; the caller decides whether to skip the leg.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

PACK_DIR="${MIMUS_STANDARD_PACK_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
[ -d "$PACK_DIR/specs" ] || { echo "ci-standard: no specs/ under $PACK_DIR" >&2; exit 2; }

MIMUS="${MIMUS:-$(command -v mimus 2>/dev/null || true)}"
[ -n "$MIMUS" ] && [ -x "$MIMUS" ] || { echo "ci-standard: mimus binary not found" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "ci-standard: python3 not found" >&2; exit 2; }

# Repo name — the spec `match` target. Prefer the origin remote's
# basename (worktree dirs are sha-suffixed); fall back to the
# checkout basename, which is correct for normal clones.
NAME="${MIMUS_REPO_NAME:-}"
if [ -z "$NAME" ]; then
  NAME="$(git remote get-url origin 2>/dev/null | sed -E 's#\.git$##; s#.*[:/]##')"
fi
NAME="${NAME:-$(basename "$REPO_ROOT")}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/specs"

# Materialize the effective spec set: repo specs/ shadows pack
# specs/ by filename; every spec whose match globs cover $NAME is
# rewritten to `match = []` (it applies to this repo by
# construction). Everything else keeps its globs.
python3 - "$PACK_DIR/specs" "$REPO_ROOT" "$NAME" "$TMP/specs" <<'PY'
import fnmatch
import os
import re
import sys

pack_dir, repo_root, name, out_dir = sys.argv[1:5]
SUFFIXES = (".toml", ".yaml", ".yml", ".json")

candidates = []  # (path, from_repo_specs)
repo_specs = os.path.join(repo_root, "specs")
shadowed = set()
if os.path.isdir(repo_specs):
    for f in sorted(os.listdir(repo_specs)):
        if f.endswith(SUFFIXES) and os.path.isfile(os.path.join(repo_specs, f)):
            candidates.append((os.path.join(repo_specs, f), True))
            shadowed.add(f)
for f in sorted(os.listdir(pack_dir)):
    p = os.path.join(pack_dir, f)
    if f in shadowed or not (os.path.isfile(p) and f.endswith(SUFFIXES)):
        continue
    candidates.append((p, False))

# `match = [ ... ]` — tolerate multi-line arrays and single-quoted
# TOML strings; specs are generated single-line today.
match_re = re.compile(r"\bmatch\s*=\s*\[([^\]]*)\]", re.S)
str_re = re.compile(r"""["']([^"']+)["']""")

for src, _repo_file in candidates:
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    dst = os.path.join(out_dir, os.path.basename(src))
    m = match_re.search(text)
    if m is not None:
        pats = str_re.findall(m.group(1))
        applies = (not pats) or any(
            fnmatch.fnmatchcase(name, pat) for pat in pats
        )
        if applies:
            text = match_re.sub("match = []", text, count=1)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(text)
PY

n_specs="$(find "$TMP/specs" -maxdepth 1 -type f | wc -l)"
echo "ci-standard: repo=$NAME root=$REPO_ROOT specs=$n_specs (pack=$PACK_DIR)"

"$MIMUS" standard --repo "$REPO_ROOT" --spec "$TMP/specs"
