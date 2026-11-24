#!/usr/bin/env python3
"""rollout-ci-standard — append the mimus-standard CI leg to repo ci.sh files.

Every gated repo's `scripts/ci.sh` gets the same trailing block: it
installs the `9aia-standard` tamias pack (specs + the
`ci-standard.sh` runner shipped in its payload) and execs the runner.
Missing tamias/mimus skips with a warning; spec violations fail the
gate via mimus's exit code.

Mechanical + idempotent: the leg is always the file's tail, so a
file already carrying the marker block is rewritten to the current
BLOCK rather than duplicated. Dry-run by default — pass `--apply`
to write.

    rollout-ci-standard.py            # print the plan
    rollout-ci-standard.py --apply    # append/refresh the block
    rollout-ci-standard.py --repo tamias --apply   # one repo
"""

import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent

MARKER = "# --- mimus standard: org conformance leg"
BLOCK = """
# --- mimus standard: org conformance leg (9aia-standard pack) ------
# Specs + runner ship in the 9aia-standard tamias pack; `tamias
# install` is a cache hit after the first fetch. Missing tooling
# skips with a warning; fail-severity spec violations fail the gate.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if command -v tamias >/dev/null 2>&1 && command -v mimus >/dev/null 2>&1; then
  _std_label="$(tamias install --no-bins 'git:github.com/9aia/workspace//libraries/9aia-standard' 2>/dev/null | sed -n 's/^installed \\([^ ]*\\).*/\\1/p' | tail -1)"
  _std_dir=""
  [ -n "$_std_label" ] && _std_dir="$(tamias info "$_std_label" --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("dir",""))' 2>/dev/null || true)"
  # Offline rerun fallback: whatever single install already exists.
  [ -z "$_std_dir" ] && _std_dir="$(tamias info 9aia-standard --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("dir",""))' 2>/dev/null || true)"
  if [ -n "$_std_dir" ] && [ -f "$_std_dir/ci-standard.sh" ]; then
    bash "$_std_dir/ci-standard.sh"
  else
    echo "ci-standard: 9aia-standard pack unavailable — leg skipped" >&2
  fi
else
  echo "ci-standard: tamias/mimus not on PATH — leg skipped" >&2
fi
"""


def targets(only: list[str]) -> list[Path]:
    repos = WS / "repos"
    out = []
    for ci in sorted(repos.glob("*/scripts/ci.sh")):
        name = ci.parent.parent.name
        if only and name not in only:
            continue
        out.append(ci)
    return out


def rewrite(text: str) -> tuple[str, str]:
    """Return (new_text, action): append, refresh, or skip."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if MARKER in line:
            head = "".join(lines[:i]).rstrip("\n")
            return head + "\n" + BLOCK, "refresh"
    if not text.endswith("\n"):
        text += "\n"
    return text + BLOCK, "append"


def main() -> int:
    args = set(sys.argv[1:])
    apply = "--apply" in args
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    planned = []
    for ci in targets(only):
        text = ci.read_text()
        new, action = rewrite(text)
        if new == text:
            continue
        planned.append((ci, new, action))
    for ci, new, action in planned:
        rel = ci.relative_to(WS)
        print(f"{'apply' if apply else 'would'} {action}: {rel} "
              f"(+{len(BLOCK.splitlines())} lines)")
        if apply:
            ci.write_text(new)
    if not apply:
        print(f"\n{len(planned)} file(s) planned — rerun with --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
