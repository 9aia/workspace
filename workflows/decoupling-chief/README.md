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
`PL-031`), hygiene/epic (`PL-032`, `PL-023` telemetry/lampy,
`PL-033` this workflow). `config.skip_ids`
holds plans blocked on owner decisions — currently empty
(`PL-023` was un-skipped once the telemetry repo name landed:
`lampy`).

## Watcher spec (PL-033 Phase 0)

One parameterized bundle covers every extraction — no per-plan
workflow files. The "per-extraction campaign" is the same
`chief.scan → chief.extract → flows/extract.yaml` loop; the plan
id is the only input.

| Concern | Mechanism |
| --- | --- |
| Who polls myco status | `chief.scan` (shell) runs `myco plan list --json` against the org ledger on `start`, `chief.loop`, and every `chief.tick` (schedule, `*/10 * * * *`). First non-`done`/`deferred` plan in `config.plan_order` wins; `in-progress`/`blocked`/`open` all count as ready so interrupted runs resume. |
| Who runs the gates | `extract.gate` inside the subflow — `cargo xtask check` in every repo worktree under `worktrees/<plan-slug>/` that has a `Cargo.toml`. Agent contract additionally requires `cargo xtask test` green before handoff; the workflow gate is the cheap outer check. |
| Agent driver | `extract.agent` POSTs `/api/sessions/run` on the shared sepia node (`config.node_url`) with bearer `PEREGRIN_TOKEN`; the agent is briefed solely by `myco resume <plan>` — the workflow carries no per-plan knowledge. |
| sturn claim globs | Agent-side, per repo `AGENTS.md`: `sturn claim "<glob>" --ws <ws>` before edits where `sturn.toml` exists. The workflow does not claim — claims are scoped to the repos a plan touches, which only the agent knows after reading the plan. |
| Retry policy | Node-level `retry`: agent 2 attempts / 10 s fixed, gate 1 attempt / 5 s, report 2 attempts / 1 s. A retried agent gets a fresh sepia session; worktrees persist so it resumes. |
| DLQ / escalation | `state/failed.txt` — `chief.report` appends a plan id on `chief.extract.failed`; `chief.scan` skips listed ids. Clear the file (or remove one line) to re-arm. Human escalation = read `state/chief.log` + `state/extract.log`, inspect `worktrees/<slug>/`, fix root cause, re-arm. No automatic page/notify in v1. |
| Phase gates | `config.plan_order` is the only ordering enforcement — human review at A→B, C, D boundaries is procedural (check `myco plan list` + handoffs), not encoded. |

## Dry-run evidence

The bundle has run end-to-end live on the shared
`peregrin-campaign.service` since 2026-11-22 (`~/.config/peregrin/serve/
decoupling-chief.yaml`). `state/chief.log` + `state/extract.log`
record every scan → resolve → agent → gate → report cycle: all
ten extraction plans (PL-023..PL-032) were picked in phase order,
agent sessions launched, gates ran, verdicts logged, and failures
armed the DLQ exactly as spec'd above. Mechanics are proven; the
extraction *outcomes* are tracked on the individual PL items, not
here.

## Release wave (Phase 2, not yet built)

The release campaign is deliberately not in this bundle: it runs
once at epic end, is `type: tarsi`/peregrin-bundle per P-052, and
needs `tamias verify` + `doctor` per pack. Foundations first
(cuora, tamias, scarab, lasius, lampy/telemetry), consumers in dep
order, tag-only repos via tarsi. Design it after Phase A–D extractions
merge — encoding it now would guess at crate names that don't exist
yet.

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
