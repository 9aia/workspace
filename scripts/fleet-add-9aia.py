#!/usr/bin/env python3
"""fleet-add-9aia — onboard the remaining 9aia clones to the bupha gate.

Adds the lockstep pair every watched repo needs (see
repos/bupha/scripts/fleet-sync.py for the same invariant):

  1. `repos/bupha/libraries/ci-gate/fleet.toml`   — `[[repo]]` entries
     (worker claim + `bash scripts/ci.sh` runner override, the 9aia
     convention)
  2. `repos/bupha/libraries/ci-ingress/main.yaml` — `repos[]` under the
     github-webhook node + `capabilities.secrets[]` names

NOT covered here (ops side, needs secrets — user territory):
  * `cuora put cuora://bupha/<SECRET_ENV>` — the HMAC value
  * GitHub webhook on the repo → https://ci.luisfuturist.com/hook
  * pack version bumps + `tamias deploy`/`tamias install` so the
    running watcher/worker pick the new fleet up

Dry-run by default; `--apply` writes. Idempotent: names already
present are skipped.

    fleet-add-9aia.py           # print the plan
    fleet-add-9aia.py --apply   # write both files
"""

import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
BUPHA = WS / "repos" / "bupha"
FLEET_TOML = BUPHA / "libraries" / "ci-gate" / "fleet.toml"
INGRESS_YAML = BUPHA / "libraries" / "ci-ingress" / "main.yaml"

# (fleet name, clone dir under repos/, secret_env name)
REPOS = [
    ("9aia/mimus", "mimus", "BUPHA_WH_9AIA_MIMUS"),
    ("9aia/lampy", "lampy", "BUPHA_WH_9AIA_LAMPY"),
    ("9aia/delphis", "delphis", "BUPHA_WH_9AIA_DELPHIS"),
    ("9aia/tardigrada", "tardigrada", "BUPHA_WH_9AIA_TARDIGRADA"),
    ("9aia/slidev-theme-9aia", "slidev-theme-9aia", "BUPHA_WH_9AIA_SLIDEV_THEME_9AIA"),
    ("9aia/vitepress-theme-9aia", "vitepress-theme-9aia", "BUPHA_WH_9AIA_VITEPRESS_THEME_9AIA"),
    ("9aia/9aia.github.io", "9aia.github.io", "BUPHA_WH_9AIA_GITHUB_IO"),
    ("9aia/.github", ".github", "BUPHA_WH_9AIA_GITHUB"),
]

FLEET_HEADER = """\
# Remaining 9aia clones onboarded to the gate — each carries
# scripts/ci.sh (real check floor + the 9aia-standard conformance
# leg). Webhook secrets resolve cuora-first as
# cuora://bupha/<secret_env>; repos whose secret/hook isn't
# provisioned yet simply never see verified deliveries.
"""


def fleet_block(name: str, directory: str, secret: str) -> str:
    return (
        "\n[[repo]]\n"
        f'name = "{name}"\n'
        f'dir = "~/GitHub/9aia/workspace/repos/{directory}"\n'
        'branch = "refs/heads/main"\n'
        f'secret_env = "{secret}"\n'
        "retry = 3\n"
        "[repo.runner]\n"
        'kind = "shell"\n'
        'token_env = "BUPHA_TOKEN"\n'
        "cancel_running = true\n"
        'cmd = "bash scripts/ci.sh"\n'
    )


def plan_fleet() -> tuple[list[str], list[str]]:
    """Return (missing_names, blocks) for fleet.toml."""
    text = FLEET_TOML.read_text()
    missing, blocks = [], []
    for name, directory, secret in REPOS:
        if f'name = "{name}"' in text:
            continue
        missing.append(name)
        blocks.append(fleet_block(name, directory, secret))
    return missing, blocks


def apply_fleet(blocks: list[str]) -> None:
    lines = FLEET_TOML.read_text().splitlines(keepends=True)
    # Insert before the first handl-lang [[repo]] — keeps the 9aia
    # section contiguous (same spot fleet-sync.py targets: before the
    # first non-9aia repo block).
    idx = next(
        i
        for i, l in enumerate(lines)
        if l.startswith("[[repo]]")
        and "handl-lang/" in "".join(lines[i : i + 3])
    )
    # back up over the blank line separating sections
    insert_at = idx
    while insert_at > 0 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    payload = FLEET_HEADER + "".join(blocks)
    lines[insert_at:insert_at] = [payload]
    FLEET_TOML.write_text("".join(lines))


def _yaml_list_insert_point(lines: list[str], key_re: re.Pattern) -> int:
    """Index where a `key:` YAML list ends (same logic as fleet-sync)."""
    i = next(i for i, l in enumerate(lines) if key_re.match(l))
    indent = re.match(r"^(\s*)", lines[i]).group(1)
    j = i + 1
    while j < len(lines):
        l = lines[j]
        if l.strip() == "" or l.lstrip().startswith("#"):
            j += 1
            continue
        cur = re.match(r"^(\s*)", l).group(1)
        if len(cur) > len(indent) or (cur == indent and l.lstrip().startswith("- ")):
            j += 1
            continue
        break
    return j


def plan_ingress() -> tuple[list[str], list[str], list[str]]:
    """Return (missing_repo_names, repo_yaml, secret_names)."""
    lines = INGRESS_YAML.read_text().splitlines(keepends=True)
    text = "".join(lines)
    missing_repos, repo_yaml, missing_secs = [], [], []
    for name, _directory, secret in REPOS:
        if f"- name: {name}\n" not in text:
            missing_repos.append(name)
            repo_yaml.append(f"    - name: {name}\n      secret_env: {secret}\n")
        if not re.search(rf"^    - {re.escape(secret)}\s*$", text, re.M):
            missing_secs.append(secret)
    return missing_repos, repo_yaml, missing_secs


def apply_ingress(repo_yaml: list[str], secrets: list[str]) -> None:
    lines = INGRESS_YAML.read_text().splitlines(keepends=True)

    # repos[] — insert after the last 9aia/* entry (before the first
    # handl-lang one) to keep the org grouping.
    j = _yaml_list_insert_point(lines, re.compile(r"^\s+repos:\s*$"))
    # walk back: find last '- name: 9aia/' item end within the list
    k = j - 1
    while k > 0 and not re.match(r"^\s+- name: 9aia/", lines[k]):
        k -= 1
    # k now at the last 9aia item's `- name:` line; its secret_env is k+1
    insert = k + 2
    lines[insert:insert] = repo_yaml

    # capabilities.secrets[] — keep alphabetical within the 9AIA run.
    lines = "".join(lines).splitlines(keepends=True)
    j = _yaml_list_insert_point(lines, re.compile(r"^  secrets:\s*$"))
    # insert each missing secret at its sorted position among the
    # existing `    - BUPHA_WH_...` items
    existing = [
        (i, re.match(r"^    - (\S+)\s*$", l).group(1))
        for i, l in enumerate(lines[:j])
        if re.match(r"^    - BUPHA_WH_", l)
    ]
    for sec in sorted(secrets):
        pos = next(
            (i for i, name in existing if name > sec),
            j,
        )
        lines.insert(pos, f"    - {sec}\n")
        # recompute insert region: everything after pos shifts; the
        # list-end index j moves too
        j += 1
        existing = [
            (i + (1 if i >= pos else 0), n)
            for i, n in existing
        ]
        existing.append((pos, sec))
        existing.sort()
    INGRESS_YAML.write_text("".join(lines))


def main() -> int:
    apply = "--apply" in sys.argv[1:]

    missing_f, blocks = plan_fleet()
    missing_r, repo_yaml, missing_s = plan_ingress()

    print(f"fleet.toml: +{len(missing_f)} [[repo]] entries")
    for n in missing_f:
        print(f"  + {n}")
    print(f"ci-ingress/main.yaml: +{len(missing_r)} repos[], +{len(missing_s)} secrets[]")
    for n in missing_r:
        print(f"  + repo {n}")
    for s in missing_s:
        print(f"  + secret {s}")

    if not missing_f and not missing_r and not missing_s:
        print("\nnothing to do — already in lockstep")
        return 0
    if not apply:
        print("\ndry-run — pass --apply to write")
        return 0

    if missing_f:
        apply_fleet(blocks)
    if missing_r or missing_s:
        apply_ingress(repo_yaml, missing_s)
    print("\napplied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
