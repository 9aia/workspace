#!/usr/bin/env python3
"""spec-guard — approval gate for specs/ changes.

specs/ is the org's conformance truth: an agent that can edit a
spec can weaken the standard it is measured against. This guard
makes specs/ changes attributable:

  1. Any change under specs/ (this repo's specs/ or the workspace
     pack) must reference a live org proposal — `proposal-NNNN`
     (or `P-NNNN`) in a `# proposal:` spec header or in the commit
     messages being introduced. The proposal must exist in the org
     ledger (repos/project/project/proposals/) with status
     open|done|accepted — cancelled/deferred don't count.
  2. Coverage regressions are always printed: removed files/dirs
     entries, severity fail→warn downgrades, match narrowing,
     shrunken cover lists, deleted spec files. With a valid
     proposal they pass (the proposal is the justification); the
     diff stays visible for review.

Usage:
    spec-guard.py                 # check committed range vs merge-base
    spec-guard.py --staged        # also check uncommitted/staged specs
    spec-guard.py --base <ref>    # explicit base ref
    spec-guard.py --report        # print findings, never fail

Exit 1 on violations, 0 clean, 2 on usage/setup errors.
"""

import re
import subprocess
import sys
import tomllib
from pathlib import Path

PROPOSAL_RE = re.compile(r"proposal-(\d{4})|\bP-(\d{3})\b")
LIVE_STATUSES = {"open", "done", "accepted"}
SEV_RANK = {"fail": 2, "warn": 1}


def sh(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git(repo: Path, *args: str) -> str:
    r = sh(["git", *args], repo)
    return r.stdout if r.returncode == 0 else ""


def find_workspace(repo: Path) -> Path | None:
    for d in [repo, *repo.parents]:
        if (d / "lasius.toml").is_file():
            return d
    return None


def ledger_dir(ws: Path | None) -> Path | None:
    if ws is None:
        return None
    p = ws / "repos" / "project" / "project" / "proposals"
    return p if p.is_dir() else None


def proposal_status(ledger: Path | None, num: str) -> str | None:
    """Status of proposal-NNNN in the org ledger, or None."""
    if ledger is None:
        return None
    for f in ledger.glob(f"proposal-{num}-*.md"):
        head = f.read_text()[:2000]
        m = re.search(r'^status\s*=\s*"([^"]+)"', head, re.M)
        return m.group(1) if m else "unknown"
    return None


def refs_in_text(text: str) -> list[str]:
    out = []
    for m in PROPOSAL_RE.finditer(text):
        num = m.group(1) or m.group(2)
        out.append(num.zfill(4) if len(num) == 3 else num)
    return out


def collect_refs(repo: Path, base: str, changed: list[str]) -> set[str]:
    refs: set[str] = set()
    # commit messages in the range
    log = git(repo, "log", "--format=%B", f"{base}..HEAD")
    refs.update(refs_in_text(log))
    # spec file headers (new content)
    for path in changed:
        f = repo / path
        if f.is_file():
            refs.update(refs_in_text(f.read_text()[:4000]))
    return refs


def load_spec(text: str) -> dict | None:
    try:
        return tomllib.loads(text)
    except Exception:
        return None


def regression_findings(repo: Path, base: str, path: str) -> list[str]:
    """Old-vs-new spec diff findings for one modified file."""
    old_text = git(repo, "show", f"{base}:{path}")
    new_file = repo / path
    if not old_text or not new_file.is_file():
        return []
    old, new = load_spec(old_text), load_spec(new_file.read_text())
    if old is None or new is None:
        return [f"{path}: spec no longer parses — manual review"]
    out = []
    for key in ("files", "dirs", "cover", "cover_dirs"):
        removed = set(old.get(key, [])) - set(new.get(key, []))
        for item in sorted(removed):
            out.append(f"{path}: `{key}` entry removed: {item}")
    old_sev = SEV_RANK.get(old.get("severity", "fail"), 0)
    new_sev = SEV_RANK.get(new.get("severity", "fail"), 0)
    if new_sev < old_sev:
        out.append(
            f"{path}: severity downgraded "
            f"{old.get('severity')} → {new.get('severity')}"
        )
    old_match = old.get("match", [])
    new_match = new.get("match", [])
    if not old_match and new_match:
        out.append(f"{path}: `match` narrowed from all-repos to {new_match}")
    return out


def main() -> int:
    args = sys.argv[1:]
    report_only = "--report" in args
    staged = "--staged" in args
    base = None
    if "--base" in args:
        base = args[args.index("--base") + 1]

    repo = Path.cwd()
    while not (repo / ".git").exists() and repo != repo.parent:
        repo = repo.parent
    if not (repo / ".git").exists():
        print("spec-guard: not inside a git repo", file=sys.stderr)
        return 2

    if base is None:
        for cand in ("origin/main", "origin/HEAD", "main", "master"):
            if git(repo, "rev-parse", "--verify", cand).strip():
                base = cand
                break
    if base is None:
        print("spec-guard: no base ref found (tried origin/main, main, master)",
              file=sys.stderr)
        return 2
    merge_base = git(repo, "merge-base", "HEAD", base).strip() or base

    # specs/ changes: committed range + (optionally) worktree
    deleted: set[str] = set()
    status = git(repo, "diff", "--name-status", f"{merge_base}...HEAD", "--", "specs/")
    changed = []
    for line in status.splitlines():
        if not line.strip():
            continue
        # name-status: "M\tpath" | "D\tpath" | "R100\told\tnew"
        parts = line.split("\t")
        path = parts[-1]
        if parts[0].startswith("D"):
            deleted.add(path)
        changed.append(path)
    if staged:
        st = git(repo, "status", "--porcelain", "-uall", "--", "specs/")
        for line in st.splitlines():
            if line.strip():
                path = line[3:]
                if line[:2].strip() == "D" or "D" in line[:2]:
                    deleted.add(path)
                changed.append(path)
    changed = sorted(set(changed))

    if not changed:
        print("spec-guard: no specs/ changes")
        return 0

    ws = find_workspace(repo)
    ledger = ledger_dir(ws)
    refs = collect_refs(repo, merge_base, changed)

    print(f"spec-guard: {len(changed)} specs/ file(s) changed vs {merge_base[:8]}")
    for c in changed:
        print(f"  {c}")

    findings: list[str] = []
    live: list[str] = []
    for num in sorted(refs):
        st = proposal_status(ledger, num)
        if st in LIVE_STATUSES:
            live.append(f"proposal-{num} ({st})")
        else:
            findings.append(
                f"proposal-{num}: "
                + ("not found in org ledger" if st is None
                   else f"status={st} (needs open|done|accepted)")
            )
    if ledger is None:
        findings.append("org ledger not found — proposal refs unverifiable")
    if not live and not any("proposal-" in f for f in findings):
        findings.append(
            "no proposal reference found — add `proposal-NNNN` to a "
            "spec header or the commit range"
        )

    for path in changed:
        if path in deleted:
            findings.append(f"{path}: spec file deleted")
        findings += regression_findings(repo, merge_base, path)

    for f in findings:
        print(f"  FINDING {f}")
    if live:
        print(f"  proposal refs: {', '.join(live)}")

    if findings and not report_only:
        print("spec-guard: FAIL — specs/ changes need a live proposal ref "
              "(proposal-NNNN in spec header or commit range)", file=sys.stderr)
        return 1
    print("spec-guard: ok" if not findings else "spec-guard: report-only, findings above")
    return 0


if __name__ == "__main__":
    sys.exit(main())
