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
| `index.md` | what / why / boundary + a router to the quadrants |
| `tutorials/` | exactly one golden path — scenario → install → first artifact → real use → what you now know |
| `how-to/` | atomic task recipes — goal → prerequisites → steps → verification → deeper link |
| `reference/` | GENERATED ONLY — cli / config / crate-api, with a "do not edit" banner |
| `explanation/` | the mental model — architecture, concepts, boundaries, decisions (+ optional `flow.md`) |

Nav order: **Get started → Tutorials → How-to → Reference → Explanation**.
The first nav item is always the org link: `{ text: "9aia", link:
"https://9aia.com", target: "_blank" }`.

## Voice

- Present tense, second person.
- No marketing adjectives; code over prose.
- Tables for enumerations.
- No versions in prose — versions live in pack manifests only.

## Rules

- **Generated, not handwritten** — crate maps, CLI references, and config
  fields come from [`cypera`](https://9aia.com/cypera/) (`cypera gen
  crate-map|cli|config|api`) driven by each repo's `cypera.toml`. Drift is
  a bug; `docs:check` regenerates and diffs.
- **Status honesty** — "scaffold" / "wip" / "pending" only if true today;
  verify against code before writing.
- **No `CHANGELOG.md`** — git history + tarsi release notes are the
  changelog; do not add or keep one.
- **`SECURITY.md` / `CONTRIBUTING.md`** — house style where the repo ships
  code.
- **Content matters** — audit narrative and structure (what/why/boundary,
  Diátaxis quadrant purity), not just factual drift.

## Content system

Diátaxis fixes the quadrants; this fixes what each page must contain.
Every page serves one reader journey: **evaluator** (index — what/why/
boundary in five minutes), **new user** (tutorials → how-to),
**maintainer/agent** (explanation → reference).

- **`index.md`** — what/why/boundary plus a router: which quadrant
  answers which goal.
- **`tutorials/`** — one golden path per repo; a second tutorial demotes
  to how-to.
- **`how-to/`** — task-titled recipes with a verification step.
- **`explanation/`** — engine repos carry `architecture.md` (the mental
  model — opens with the idea, never provenance), `concepts.md`
  (vocabulary), `boundaries.md` (owns / doesn't-own), `decisions.md`
  (decision → alternatives → consequence), and optionally `flow.md`
  (one end-to-end narrative).
- **Ecosystem position** — every engine repo's explanation carries a
  "Where it sits" block in the tamias → engines → orchestration →
  surfaces hierarchy.
- **Coverage bar** — engine: index + 1 tutorial + ≥3 how-tos + the
  explanation set + generated reference. Library/content repos run a
  lighter profile declared in `cypera.toml [check] profile`.

`cypera check` enforces the mechanical parts — required pages per
profile, index router links, tutorial count, no orphan
`getting-started.md`, generated freshness. Substance stays editorial.

## Ecosystem

[tamias](https://9aia.com/tamias/) is the entrypoint — everything installs
and updates through tamias packs. The hierarchy reads
**packaging → engines → surfaces**.

## Deploy

Docs sites deploy to GitHub Pages only for public repos at
`https://9aia.com/<repo>/`. Private repos keep the site source, no deploy.
