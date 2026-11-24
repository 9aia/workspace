#!/usr/bin/env python3
"""sync-spec-pack — materialize the 9aia-standard tamias pack payload.

The pack at libraries/9aia-standard/ distributes the org's mimus
standard spec set as a tamias content pack (`type: files` — no
driver, payload consumed by path). Its specs/ dir is a *copy* of
the spec sources of truth:

    specs/*.toml|yaml|yml|json              → pack specs/ (flat)
    repos/<name>/specs/*                    → pack specs/ (flat)

Flat layout on purpose: `mimus standard --spec <dir>` is
non-recursive and union-matches every spec in the dir, so one
installed pack covers base + every repo family. Repo spec files
are named `<repo>.toml` and never collide with `base.toml`.

This script keeps the copies honest — run it in the same change
as any spec edit (the sources stay approval-gated; the pack
copies ride spec-guard/spec-lock coverage of
libraries/9aia-standard/specs/). Bump the pack's `version:` in
tamias.yaml when spec content changes — the store keys entries
by name@version.

Usage:
    sync-spec-pack.py            # dry-run: print the plan
    sync-spec-pack.py --apply    # write/copy/remove to match sources
    sync-spec-pack.py --check    # exit 1 when pack != sources
"""

import shutil
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
SOURCES = [WS / "specs"] + sorted((WS / "repos").glob("*/specs"))
PACK = WS / "libraries" / "9aia-standard"
TARGET = PACK / "specs"
SPEC_SUFFIXES = {".toml", ".yaml", ".yml", ".json"}
SKIP_REPOS = {"strigi"}  # archived — no spec anyway, belt & braces


def source_files() -> dict[str, Path]:
    """filename → source path; collisions are a hard error."""
    out: dict[str, Path] = {}
    for d in SOURCES:
        if not d.is_dir():
            continue
        # repos/<name>/specs — skip archived clones defensively
        if d.parent.name in SKIP_REPOS:
            continue
        for p in sorted(d.iterdir()):
            if p.is_file() and p.suffix in SPEC_SUFFIXES:
                if p.name in out and out[p.name] != p:
                    sys.exit(f"sync-spec-pack: filename collision on {p.name}: "
                             f"{out[p.name]} vs {p}")
                out[p.name] = p
    return out


def target_files() -> dict[str, Path]:
    if not TARGET.is_dir():
        return {}
    return {p.name: p for p in TARGET.iterdir()
            if p.is_file() and p.suffix in SPEC_SUFFIXES}


def identical(a: Path, b: Path) -> bool:
    return a.read_bytes() == b.read_bytes()


def plan() -> tuple[list[tuple[str, Path, Path | None]], list[str], list[str]]:
    """(copies, removals, unchanged) — copies are (name, src, dst)."""
    src, dst = source_files(), target_files()
    copies, stale, same = [], [], []
    for name, sp in sorted(src.items()):
        tp = TARGET / name
        if name not in dst:
            copies.append((name, sp, tp))
        elif not identical(sp, tp):
            copies.append((name, sp, tp))
        else:
            same.append(name)
    for name in sorted(set(dst) - set(src)):
        stale.append(name)
    return copies, stale, same


def main() -> int:
    args = set(sys.argv[1:])
    apply = "--apply" in args
    check = "--check" in args
    if apply and check:
        print(__doc__)
        return 2

    copies, stale, same = plan()
    for name, sp, _ in copies:
        print(f"  {'copy ' if (TARGET / name).exists() else 'add  '} {name}  <- {sp.relative_to(WS)}")
    for name in stale:
        print(f"  rm    {name}  (no longer a spec source)")
    print(f"sync-spec-pack: {len(copies)} to write, {len(stale)} to remove, "
          f"{len(same)} unchanged ({len(source_files())} sources)")

    if check:
        if copies or stale:
            print("sync-spec-pack: FAIL — pack payload drifted from sources",
                  file=sys.stderr)
            return 1
        print("sync-spec-pack: ok")
        return 0

    if not apply:
        print("sync-spec-pack: dry-run — pass --apply to write, --check to verify")
        return 0

    TARGET.mkdir(parents=True, exist_ok=True)
    for name, sp, tp in copies:
        shutil.copyfile(sp, tp)
    for name in stale:
        (TARGET / name).unlink()
    print(f"sync-spec-pack: applied ({len(copies)} written, {len(stale)} removed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
