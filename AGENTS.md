# 9aia workspace — agent guide

Metarepo root for the 9aia org (GAIA — open infrastructure for
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
| `repos/sepia` | session lifecycle — start/resume/teardown |
| `repos/peregrin` | event-driven orchestration — campaigns, multi-machine |
| `repos/bupha` | CI integration for tamias (`type: bupha`) — queue → worktree → runner (`shell`/`dagger`/`gha`) → forge status |
| `repos/cicada` | scheduled-work engine — calendars, recurring runs |
| `repos/pavo` | agent UI / views |
| `repos/atta` | fungus-garden layer — tended architecture (WIP) |
| `repos/project` | org ledger — proposals, plans, ADRs (myco, private) |
| `repos/pachira` | local-first personal finance (WIP, private) |
| `repos/camelus` | multi-tenant AI lead platform (private) |
| `repos/castor` | SQL database CLI (private) |
| `repos/mycena` | code scout → myco ledger (private) |
| `repos/lasius` | workspace gardener — manages this repo |
| `repos/vitepress-theme-9aia` | VitePress theme |
| `repos/slidev-theme-9aia` | Slidev theme |
| `repos/9aia.github.io` | Gaia's website |
| `repos/.github` | org profile + community health |

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
- Never edit `node_modules`, `target/`, or generated files.

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
