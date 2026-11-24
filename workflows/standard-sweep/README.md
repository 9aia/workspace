# standard-sweep

Fleet conformance sweep as a peregrin campaign — the scheduled/on-demand
CI leg for `mimus standard`. Inspired by handl-lang's
`workflows/lib/mimus-standard.node.yml` (advisory per-repo node inside
its `gate.yaml`); here it is a fleet bundle in the handl-verify shape:
one shell node wraps the org's declared sweep entrypoint,
`scripts/standard.sh`.

## What it does

1. **`sweep.schedule`** (driver `schedule`, nightly — default
   `41 4 * * *` America/Sao_Paulo) emits `sweep.due`.
2. **`sweep.run`** (driver `shell`, on `start` + `sweep.due`) cds into
   the lasius workspace and runs `scripts/standard.sh`, teeing output
   to `<results_dir>/last.log` and writing the exit code to
   `last.rc`. Exit 0 → `sweep.done`; anything else (fail-severity
   violations, missing `mimus` binary → rc 2) → `sweep.failed`.

`start` is in the run node's `on:` list, so `peregrin campaign run`
sweeps immediately — same path as the nightly tick.

## Operator knobs

Every `${config.*}`/`${env(...)}` lookup resolves env-first with a
built-in default; only `cron` is declared in `config:` (a set-but-empty
config key would defeat the env fallback, so the rest stay undeclared).
`STANDARD_SWEEP_*` env vars (see `capabilities.env`):

| knob | env | default |
| --- | --- | --- |
| workspace root (holds `specs/` + `repos/`) | `STANDARD_SWEEP_WORKSPACE` | `$HOME/GitHub/9aia/workspace` |
| cron (`config.cron` also settable) | `STANDARD_SWEEP_CRON` | `41 4 * * *` |
| mimus binary (`""` → PATH → `repos/mimus/target/debug/mimus`, per `standard.sh`) | `STANDARD_SWEEP_MIMUS` | auto |
| repo subset (`""` → every clone; `strigi` always skipped as archived) | `STANDARD_SWEEP_REPOS` | all |
| results dir (`last.log`, `last.rc`) | `STANDARD_SWEEP_RESULTS_DIR` | `$HOME/.local/share/standard-sweep` |
| node timeout | — | fixed `1800`s (`params.timeout` rejects templated values) |

## Install / run

```bash
# validate before deploying
peregrin campaign validate workflows/standard-sweep/main.yaml

# dry-run the pack resolution first
tamias install --plan --allow-drivers ./workflows/standard-sweep

# install the bundle (shared provider — no new service)
tamias install --allow-drivers ./workflows/standard-sweep

# deploy renders ~/.config/peregrin/serve/standard-sweep.yaml on the
# shared peregrin-campaign.service; or run one-shot without serving:
peregrin campaign run workflows/standard-sweep/main.yaml
STANDARD_SWEEP_WORKSPACE=/path/to/workspace peregrin campaign run workflows/standard-sweep/main.yaml

# cheap verdict poll without the campaign log:
cat ~/.local/share/standard-sweep/last.rc   # 0 = clean/warn-only, 1 = fail violations, 2 = no mimus
```

## Boundaries / notes

- **Read-only on specs.** `specs/` dirs are approval-gated
  (`scripts/spec-guard.py`); this campaign only runs the checker.
- **Not the per-push gate.** bupha's `ci-gate` fleet runs each repo's
  `scripts/ci.sh` on push; this sweep is the cross-repo conformance
  pass over the *workspace* layout (`specs/` + `repos/*/specs/`), which
  no single repo checkout can see. If per-repo `mimus standard` legs
  are wanted inside `scripts/ci.sh` gates later, that is a separate
  change — each repo would need its spec pack reachable.
- Serial by construction (standard.sh loops); a `driver: runner`
  fan-out like handl-verify's `verify.work.*` workers is the upgrade
  path if the fleet outgrows the timeout.
