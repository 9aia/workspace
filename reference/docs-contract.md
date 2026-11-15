---
title: Docs contract
description: The org-wide documentation standard every 9aia repo follows.
---

# Docs contract

The standard every repo in the org follows. Source of truth for the rules:
[`AGENTS.md`](https://github.com/9aia/workspace/blob/main/AGENTS.md) → *Docs
contract*; this page is the published reference.

## README.md

Succinct, helpful, clear. What it is + why + quickstart. No crate tables,
verb dumps, or status essays — link to `AGENTS.md` / docs for depth.

## AGENTS.md

The agent/dev map: layout, commands, rules, boundary, docs pointer, and the
awareness blocks (myco / sturn / kuda). Crate and verb tables are allowed but
must match source exactly — generated where a generator exists, audited
otherwise.

## Per-file skeletons

| File | Contains |
| --- | --- |
| `README.md` | name + one-line what → boundary (owns / doesn't) → status (only if WIP) → quickstart (≤10 lines) → docs links |
| `AGENTS.md` | what-it-is → Layout → Commands → Boundary → Rules → Docs pointer → awareness blocks |

## Docs site IA

Every repo carries a `docs/` worktree — VitePress + Diátaxis.

| Path | Holds |
| --- | --- |
| `index.md` | what / why / boundary + quadrant links |
| `tutorials/` | learning-oriented paths |
| `how-to/` | task-oriented recipes |
| `reference/` | GENERATED ONLY — cli / config / crate-api, with a "do not edit" banner |
| `explanation/` | design rationale |

Nav order: **Get started → Tutorials → How-to → Reference → Explanation**.

## Voice

- Present tense, second person.
- No marketing adjectives; code over prose.
- Tables for enumerations.
- No versions in prose — versions live in pack manifests only.

## Rules

- **Generated, not handwritten** — crate maps, CLI references, and config
  fields come from `docs/gen-*.py` scripts rendered from source. Repos
  without generators get them; drift is a bug.
- **Status honesty** — "scaffold" / "wip" / "pending" only if true today;
  verify against code before writing.
- **No `CHANGELOG.md`** — git history + tarsi release notes are the
  changelog; do not add or keep one.
- **`SECURITY.md` / `CONTRIBUTING.md`** — house style where the repo ships
  code.
- **Content matters** — audit narrative and structure (what/why/boundary,
  Diátaxis quadrant purity), not just factual drift.

## Ecosystem

[tamias](https://9aia.com/tamias/) is the entrypoint — everything installs
and updates through tamias packs. The hierarchy reads
**packaging → engines → surfaces**.

## Deploy

Docs sites deploy to GitHub Pages only for public repos at
`https://9aia.com/<repo>/`. Private repos keep the site source, no deploy.
