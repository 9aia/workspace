#!/usr/bin/env python3
"""spec-lock — tamper-evident digest pin for the spec packs.

spec-guard.py gates *changes* (proposal ref + no regression vs
merge-base). spec-lock pins the *committed truth*: sha256 of every
spec file, so a spec edited and committed through a path that
skipped review still trips `--check`.

  spec-lock.py --write   # (re)generate specs-lock.json
  spec-lock.py --check   # verify lock matches disk (exit 1 on drift)

Covers workspace specs/ and every repos/<name>/specs/ clone.
strigi (archived) is exempt.
"""

import hashlib
import json
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
LOCK = WS / "specs-lock.json"
SKIP = {"strigi"}


def spec_files() -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {}
    ws_specs = WS / "specs"
    if ws_specs.is_dir():
        out["workspace"] = sorted(
            p for p in ws_specs.iterdir()
            if p.suffix in {".toml", ".yaml", ".yml", ".json"}
        )
    repos = WS / "repos"
    if repos.is_dir():
        for repo in sorted(repos.iterdir()):
            if repo.name in SKIP or not (repo / ".git").exists():
                continue
            sd = repo / "specs"
            if sd.is_dir():
                out[repo.name] = sorted(
                    p for p in sd.iterdir()
                    if p.suffix in {".toml", ".yaml", ".yml", ".json"}
                )
    return out


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot() -> dict:
    return {
        repo: {p.name: digest(p) for p in files}
        for repo, files in spec_files().items()
    }


def main() -> int:
    if "--write" in sys.argv:
        LOCK.write_text(json.dumps(snapshot(), indent=2, sort_keys=True) + "\n")
        print(f"spec-lock: wrote {LOCK.relative_to(WS)}")
        return 0
    if "--check" not in sys.argv:
        print(__doc__)
        return 2
    if not LOCK.is_file():
        print("spec-lock: no lock file — run --write", file=sys.stderr)
        return 1
    want = json.loads(LOCK.read_text())
    got = snapshot()
    drift = []
    for repo, files in got.items():
        for name, sha in files.items():
            if want.get(repo, {}).get(name) != sha:
                drift.append(f"{repo}/{name}: digest mismatch")
    for repo, files in want.items():
        for name in files:
            if name not in got.get(repo, {}):
                drift.append(f"{repo}/{name}: spec missing on disk")
    for d in drift:
        print(f"  DRIFT {d}")
    if drift:
        print("spec-lock: FAIL — specs changed without lock update",
              file=sys.stderr)
        return 1
    print("spec-lock: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
