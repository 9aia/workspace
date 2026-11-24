# 9aia workspace — agent guide

Metarepo root for the 9aia org (Gaia — open infrastructure for
agent-driven development). **Config only** — repo management is
delegated to [lasius](https://github.com/9aia/lasius) via `lasius.toml`.
All org repositories are cloned under `repos/` (gitignored); each is an
independent repo with its own `AGENTS.md` — read it before working
inside.

## Repo map

| repo | role |
| ---- | ---- |
| `repos/tamias` | package & content manager — fetch, store, cache, dispense |
| `repos/myco` | records engine — views + mutations over the work ledger |
| `repos/kuda` | code-map engine — verified per-module cards |
| `repos/mimus` | verification engine — proofs over agent claims |
| `repos/sturn` | ephemeral coordination — claims/ops/topics over VCS state |
| `repos/cuora` | secrets broker — sealed, not spilled |
| `repos/tardigrada` | age-identity lifecycle — the per-machine, per-human key behind encrypted stores |
| `repos/sepia` | session lifecycle — start/resume/teardown |
| `repos/peregrin` | event-driven orchestration — campaigns, multi-machine |
| `repos/bupha` | CI integration for tamias (`type: bupha`) — queue → worktree → runner (`shell`/`dagger`/`gha`) → forge status |
| `repos/cicada` | scheduled-work engine — calendars, recurring runs |
| `repos/hypha` | distributed substrate — entities, ops, snapshots, locks across machines |
| `repos/scarab` | config & template expertise — generic config loading libs, templated content packs via tamias (P-017) |
| `repos/tarsi` | release plane — `tarsi-serve` ops (plan/changelog/bump/tag/publish/release); `type: tarsi` profile packs (`libraries/9aia-release`), peregrin `libraries/release` campaigns (P-013/PL-014, ADR-0005) |
| `repos/pavo` | agent UI / views |
| `repos/atta` | fungus-garden layer — tended architecture (WIP) |
| `repos/project` | org ledger — proposals, plans, ADRs (myco, private) |
| `repos/pachira` | local-first personal finance (WIP, private) |
| `repos/camelus` | multi-tenant AI lead platform (private) |
| `repos/castor` | SQL database CLI (private) |
| `repos/mycena` | code scout → myco ledger (private) |
| `repos/lasius` | git & workspace expertise — workspace gardener CLI + shared `lasius-vcs` port (P-019) |
| `repos/cypera` | docs utilities — reusable reference-doc generation for the org |
| `repos/vitepress-theme-9aia` | VitePress theme |
| `repos/slidev-theme-9aia` | Slidev theme |
| `repos/9aia.github.io` | Gaia's website |
| `repos/.github` | org profile + community health |
| `repos/ci-e2e` | bupha CI e2e validation scratch repo (private) |
| `repos/strigi` | natural-language CLI assistant — **archived** |
| `repos/delphis` | remote dev environments over Tailscale — revived (P-001: publish/attach for humans + agents) |

This workspace root is itself the `9aia/workspace` repo. `strigi` is
archived on GitHub (read-only) — cloned for reference, do not push to
it.

Org-level shared content lives at the workspace root: `workflows/`
(peregrin campaign bundles), `libraries/` (tamias packs — e.g.
`secrets-9aia`, the org sealed-secrets pack), and `projects.yaml`
(canonical project catalog — tagline/description/layer/links per repo;
drives 9aia.com and is mirrored into each repo's docs index).

## Cross-repo rules

- Sibling clones live at `repos/<name>`; `../<repo>` references inside
  a repo's docs resolve within `repos/`.
- `project` is the org-wide myco ledger — run `myco status --prompt`
  inside `repos/project` for cross-repo work, track with `myco todo
  add` / `myco proposal new`, hand off with `myco handoff <ID>`.
  Never hand-edit `project/` files — myco verbs are the write path.
  (`repos/<name>/project` and `repos/<name>/docs` are git worktrees of
  orphan branches — leave them alone; they were repaired after the
  move into `repos/`.)
- sturn-wired repos (`sturn.toml` present): `sturn claim` before edits.
- kuda-wired repos (`.kuda/` present): read cards before re-exploring;
  regenerate drifted cards in the same change.
- English everywhere (code, comments, commit messages).
- Mechanical changes (bulk edits, renames, generated-file syncs) go
  through a script with a dry-run mode — plan the diff first, apply
  after review; faster, safer, and re-runnable.
- Never edit `node_modules`, `target/`, or generated files.
- Org LoC reporting: every non-archived repo must appear in
  `repos/.github/packs/loc/loc.yaml` — `lasius doctor` enforces it
  (`loc coverage` check). New repos: add to the pack, bump nothing
  else; the weekly `loc` workflow picks it up.

## Docs contract

Org-wide documentation standard — applies to every repo:

- **README.md** — succinct, helpful, clear. What it is + why + quickstart.
  No crate tables, verb dumps, or status essays; link to AGENTS.md/docs for depth.
- **AGENTS.md** — the agent/dev map: layout, commands, rules, boundary.
  Crate/verb tables allowed but must match source exactly — generated where
  a generator exists, audited otherwise.
- **Generated, not handwritten** — crate maps, CLI references, config
  fields, and API docs come from `cypera gen` (`crate-map`/`cli`/`config`/
  `api`) driven by each repo's `cypera.toml`, rendered from source.
  `cypera check` fails on drift; `docs:check` regenerates and diffs.
- **Status honesty** — "scaffold"/"wip"/"pending" only if true today;
  verify against code before writing.
- **Docs sites** — every repo has a `docs/` worktree (VitePress +
  Diátaxis); deploy to GitHub Pages only for public repos
  (`https://9aia.com/<repo>/`). Private repos keep the site source,
  no deploy. The first nav item is always the org link:
  `{ text: "9aia", link: "https://9aia.com", target: "_blank" }`.
  Every site uses `vitepress-theme-9aia` (`.vitepress/theme/index.ts`
  re-exports it) with `search.provider: "local"` in themeConfig.
- **SECURITY.md / CONTRIBUTING.md** — house style where the repo ships code.
- **No CHANGELOG.md** — git history + tarsi release notes are the
  changelog; do not add or keep one.
- **Versions** live in pack manifests only, never prose.
- **Content matters** — audit narrative and structure (what/why/boundary,
  Diátaxis quadrant purity), not just factual drift.

### Docs content system

Diátaxis quadrants are fixed; this governs what each page must contain.

Reader model — every page serves one journey: **evaluator** (index,
5-minute what/why/boundary), **new user** (tutorials → how-to),
**maintainer/agent** (explanation → reference).

- **`index.md`** — what/why/boundary plus a router: which quadrant
  answers which goal.
- **`tutorials/`** — exactly one golden path per repo: scenario →
  install → first artifact → real use → what you now know. Learn by
  doing; no reference dumps. A second tutorial demotes to how-to.
- **`how-to/`** — atomic task recipes titled as tasks. Required shape:
  goal → prerequisites → numbered steps with real commands →
  verification ("you should see X") → deeper link.
- **`explanation/`** — fixed set for engine repos:
  - `architecture.md` — the mental model: components, data flow,
    ports table, crate-map splice. Opens with the idea, never
    provenance.
  - `concepts.md` — domain vocabulary, each term defined once.
  - `boundaries.md` — owns / doesn't-own, neighbors named (fold into
    architecture if <40 lines).
  - `decisions.md` — ADR-lite: decision → alternatives → consequence.
  - `flow.md` — optional but encouraged: one end-to-end narrative of a
    real operation.
  - `security.md` — only where a real threat surface exists.
- **Ecosystem position** — every engine repo's explanation carries a
  "Where it sits" block placing it in the delivery → memory → process →
  interface hierarchy (see `projects.yaml` `layer`).
- **Coverage bar** — engine repo: index + 1 tutorial + ≥3 how-tos +
  the explanation set + generated reference. Library/content repos:
  index + architecture + concepts + reference. Site/ledger repos are
  exempt via `cypera.toml [check] skip`.
- **`cypera check`** enforces the mechanical parts (required pages per
  profile, quadrant links, tutorial count); substance stays editorial.

## Specs & standards (mimus standard)

Org conformance is declarative — `mimus standard` diffs each repo
against spec packs:

- `specs/base.toml` — floor for every repo (contract files,
  `CHANGELOG.md` forbidden, `[providers.lasius]` remote_org+policy).
- `repos/<name>/specs/<name>.toml` — the repo's own family spec,
  generated by `scripts/gen-repo-specs.py` (dry-run default;
  `--apply` writes, `--repo <name>` scopes). Re-run only to
  re-snapshot coverage — edit deliberately otherwise.
- `templates/README/` — README skeletons per stack (engine/web/bare).
- `libraries/9aia-standard/` — the spec set as a tamias content pack
  (`type: files`, no driver). `specs/` inside it is a *generated
  copy* of the sources above, materialized by
  `scripts/sync-spec-pack.py` (dry-run default; `--apply` writes,
  `--check` verifies) — run it in the same change as any spec edit
  and bump the pack's `version:` in `tamias.yaml`. The pack exists
  for consumers without a sibling workspace checkout:

  ```bash
  tamias install --plan ./libraries/9aia-standard   # dry-run
  tamias install ./libraries/9aia-standard
  SPEC_DIR="$(tamias info 9aia-standard --json \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["dir"])')/specs"
  mimus standard --repo <path> --spec "$SPEC_DIR"
  ```

  `mimus standard --spec` takes files or dirs (non-recursive,
  union matching) — it does not resolve `tamias:` refs itself;
  the installed store path is the ref resolution. The fleet sweep
  keeps using the sibling paths; the pack is for CI/standalone
  consumers. Pack spec copies are approval-gated identically —
  spec-guard.py and spec-lock.py cover `libraries/*/specs/`.

  **CI leg** — every gated repo's `scripts/ci.sh` ends with the
  same block (rolled out by `scripts/rollout-ci-standard.py`,
  idempotent): `tamias install` the pack from its git ref, then
  exec `ci-standard.sh` from the store payload. The runner
  materializes the spec set (pack `specs/` + the repo's own
  `specs/`, repo files shadowing pack copies) and rebuilds `match`
  selection for sha-suffixed bupha worktrees, so `mimus standard`
  applies the same base+family specs the sweep does. Missing
  tamias/mimus skips with a warning; fail-severity violations fail
  the gate. There is no scheduled sweep — conformance is enforced
  per push.

Sweep: `scripts/standard.sh [names…]` (uses `MIMUS` env or the
sibling dev build). Warn violations print but don't fail; fail
violations do.

### specs/ is approval-gated

An agent that can edit a spec can weaken the standard it is measured
against — treat `specs/` (here, in every clone, and in
`libraries/*/specs/` pack payloads) as protected:

- **Any specs/ change requires a live org proposal** —
  `proposal-NNNN` (status open|done|accepted in
  `repos/project/project/proposals/`) referenced in a `# proposal:`
  spec header or in the commit range. `scripts/spec-guard.py`
  enforces: no live ref → exit 1.
- **No silent regression** — the guard prints removed
  files/dirs/cover entries, severity downgrades, `match` narrowing,
  and deleted specs vs merge-base. A proposal is the justification;
  the diff stays visible for review.
- Regenerating specs after legitimate file additions is fine — the
  new files must already be covered or the spec diff shows it.
- `scripts/spec-lock.py --write` re-pins `specs-lock.json` (sha256
  per spec file) — run it in the same change as any approved spec
  edit; `--check` verifies the committed truth independently of git
  diff.

## Workspace commands

Managed by [lasius](https://github.com/9aia/lasius) — `lasius.toml`
is the only config:

- `lasius init` — scaffold + clone all org repos + generate
  `9aia.code-workspace`
- `lasius update` — fast-forward pull every clone
- `lasius status` — branch / dirty / sync matrix (`--json` available)
- `lasius code-workspace generate` — regenerate the workspace file
- `lasius doctor` — env + drift diagnostics
- `lasius exec -- <cmd>` — run a command in every clone
- `lasius rm <repo>` — remove a clone after safety checks
- all accept `--root <dir>` (default: `lasius.toml` discovered upward)
