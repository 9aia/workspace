# decoupling-chief

Chief-of-staff monitor for the ecosystem decoupling epic
(`PL-022` master plan; proposals `P-042`–`P-053`; per-item plans
`PL-023`–`PL-033` in the org ledger `repos/project`).

## What it does

Long-running campaign on the shared `peregrin-campaign.service`:

1. **`chief.tick`** (schedule, every 10 min) re-kicks the loop —
   watchdog for crashed subflows and newly-filed plans.
2. **`chief.scan`** reads `myco plan list --json` in the org ledger
   and picks the first plan in `config.plan_order` whose status is
   not `done`/`deferred` (`in-progress` counts — interrupted runs
   resume). Writes `state/next.json`.
3. **`chief.extract`** runs `flows/extract.yaml` as a subworkflow:
   resolve → sepia agent session (briefed by `myco resume <plan>`)
   → `cargo xtask check` gate per repo worktree → report.
4. **`chief.report`** logs the verdict and loops back to scan.
   `chief.idle` = queue drained; the run stays alive on the tick.

## Phase order

`config.plan_order` encodes PL-022's phases: foundations first
(`PL-024` secrets→cuora, `PL-025` lifecycle→tamias,
`PL-026` config→scarab), then integration (`PL-027` sessions→sepia,
`PL-028` ci-job→bupha, `PL-029` ACP→sepia), VCS (`PL-030`,
`PL-031`), hygiene/epic (`PL-032`, `PL-033`). `config.skip_ids`
holds plans blocked on owner decisions — currently `PL-023`
(telemetry repo, blocked on the binomial name).

## Install / run

```bash
# install the bundle (shared provider — no new service)
tamias install --allow-drivers ./workflows/decoupling-chief

# validate before deploying
peregrin campaign validate decoupling-chief

# deploy renders into ~/.config/peregrin/serve/ on the shared
# campaign service; or run one-shot:
peregrin campaign run decoupling-chief   # NOTE: long-running —
                                       # prefer serve + submit/poll
```

State lives in `~/.local/share/decoupling-chief/` (`next.json`,
`plans.json`, `chief.log`, `extract.log`, `worktrees/`).

## Agent contract (what extract agents must do)

Briefed entirely by `myco resume <plan>` — the workflow carries no
per-plan knowledge:

- worktrees under `worktree_base/<plan-slug>/<repo>` via
  `lasius vcs worktree`, branch `decouple/<plan-slug>`
- sturn claim before edits where `sturn.toml` exists
- `cargo xtask check` + `cargo xtask test` green per touched repo
- conventional commits, push branch, **no PRs**
- `myco handoff <plan>`; blocked → handoff + stop

## Known v1 limits

- Serial execution (one plan at a time) — deliberate: extractions
  share ports (lasius-vcs, scarab-config, cuora-secret) and would
  conflict.
- `chief.scan` treats any non-zero exit as idle (including real
  errors) — the 10-min tick retries; check `chief.log`.
- The gate runs `cargo xtask check` only (not `test`) — test suites
  are the agent's job per the brief; tighten if needed.
- `campaign run` one-shot will sit on the schedule tick — run under
  `campaign serve` (the provider default) or `submit`+poll.
