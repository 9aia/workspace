# 9aia workspace

Metarepo for the [9aia](https://github.com/9aia) GitHub org — config
only, managed by [lasius](https://github.com/9aia/lasius). GAIA: open
infrastructure for agent-driven development.

`repos/` is gitignored — each entry is an independent clone with its
own history, branches, and remotes. No submodules.
`9aia.code-workspace` is generated at runtime, never committed.

## Config

Everything lives in [`lasius.toml`](lasius.toml):

```toml
org = "9aia"
include_private = true   # org has private repos (project, pachira, camelus, …)
exclude = ["workspace"]  # the metarepo itself is not a member
```

Repo discovery is automatic — every non-archived repo in the org gets
cloned (private included). Archive a repo on GitHub to exclude it.

## Bootstrap

```bash
# install lasius
cargo install lasius
# or: cargo install --git https://github.com/9aia/lasius

lasius init      # clone every org repo into repos/ + generate the workspace file
```

Requires `git` and an authenticated `gh` on PATH.

Open `9aia.code-workspace` in VSCode/Windsurf for the full org.

## Commands

```bash
lasius clone                     # clone missing org repos
lasius update                    # git pull --ff-only in every clone
lasius status                    # branch / dirty / ahead-behind matrix
lasius code-workspace generate   # regenerate 9aia.code-workspace
lasius doctor                    # env + drift diagnostics
lasius exec -- <cmd>             # run a command in every clone
lasius rm <repo>                 # remove a clone after safety checks
```

All accept `--root <dir>`; `lasius.toml` is discovered upward from the
current directory.

## Repo map

| repo                       | what it is                                                              |
| -------------------------- | ----------------------------------------------------------------------- |
| `repos/tamias`             | Package & content manager for the agent factory — fetch, store, cache, dispense |
| `repos/myco`               | Records engine for agent work — views + mutations; PM is the prelude    |
| `repos/kuda`               | Code-map engine — verified per-module cards agents read before code     |
| `repos/mimus`              | Verification engine — proofs over what agents claim                     |
| `repos/sturn`              | Ephemeral coordination — claims/ops/topics over VCS state               |
| `repos/cuora`              | Secrets broker for agents — sealed, not spilled                         |
| `repos/sepia`              | Session lifecycle engine — start/resume/teardown for coding agents      |
| `repos/peregrin`           | Event-driven orchestration — campaigns of agent workflows, multi-machine |
| `repos/bupha`              | Queue engine for event-driven jobs — shipped as CI                      |
| `repos/cicada`             | Scheduled-work engine — calendars and recurring agent runs              |
| `repos/pavo`               | Agent UI / views layer                                                  |
| `repos/atta`               | Fungus-garden layer — tended architecture: crates, moves, drift (WIP)   |
| `repos/project`            | Org ledger — cross-repo proposals, plans, ADRs (myco, private)          |
| `repos/pachira`            | Local-first personal finance app (WIP, private)                         |
| `repos/camelus`            | Multi-tenant AI platform for capturing leads (private)                  |
| `repos/castor`             | SQL database CLI via JavaScript-defined blocks (private)                |
| `repos/mycena`             | Code scout — surfaces TODOs/notes into the myco ledger (private)        |
| `repos/lasius`             | Workspace gardener — this repo's manager                                |
| `repos/vitepress-theme-9aia` | VitePress theme for 9aia docs sites                                   |
| `repos/slidev-theme-9aia`  | Slidev theme for 9aia presentations                                      |
| `repos/9aia.github.io`     | Gaia's website                                                           |
| `repos/.github`            | Org profile README + community health files                             |

## Conventions

See [AGENTS.md](AGENTS.md). Each repo under `repos/` has its own
`AGENTS.md` — read it before working inside. `project/` and `docs/`
inside clones are git worktrees of orphan branches managed by myco /
docs tooling — never commit their contents to `main`.
