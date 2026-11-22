# kill-mutants

StrykerJS mutation testing → agent triage → tests → PR.

Inject one event; the campaign cuts a lasius worktree, installs deps,
runs the package's mutation suite, hands survivors to a sepia agent
(kill with tests; `// Stryker disable` only for empirically-proven
equivalent mutants), then commits, pushes and opens a PR. All
git/forge via lasius, agent via sepia — no raw `git`/`gh`/`devin`.

## Trigger

```bash
curl -X POST http://127.0.0.1:29173/api/events/inject \
  -H "authorization: Bearer $PEREGRIN_TOKEN" \
  -H 'content-type: application/json' \
  -d '{"type":"mutate.requested","campaign":"kill-mutants",
       "payload":{"id":"rbac-mutation","package":"packages/rbac",
       "checkout":"/abs/path/to/clone","base_branch":"main"},
       "idempotencyKey":"rbac-mutation-1"}'
```

| field | req | meaning |
| --- | --- | --- |
| `id` | yes | `[A-Za-z0-9][A-Za-z0-9._-]{0,63}` — keys worktree, artifacts, branch `test/<id>`. Unique per run. |
| `package` | yes | dir with `stryker.conf.json`, relative to checkout |
| `checkout` | * | lasius clone path (fallback `config.checkout`) |
| `base_branch` | no | PR base / worktree rev (default `main`) |

## Pipeline

`route` (validate, persist request) → `worktree` (detached @
`origin/<base>`, checks `stryker.conf.json`) → `install` → `mutate`
(`bun run mutate` in pkg; needs rc 0 + parseable
`reports/mutation/mutation.json`) → `summarize` (counts + mutant
detail; zero actionable → clean stop) → `agent` (sepia session,
30 min default) → `push` (`HEAD:refs/heads/test/<id>`) → `pr` →
`cleanup` → `report`. Every terminal outcome removes the worktree.

## Install & config

`tamias install --allow-drivers <bundle>` → `tamias deploy` → set
`config:` in `~/.config/peregrin/serve/kill-mutants.yaml` (re-apply
after every deploy) → `systemctl --user restart peregrin-campaign`.

Repo prereqs: `stryker.conf.json` with `jsonReporter` →
`reports/mutation/mutation.json`, a `mutate` script, **no
`thresholds.break`**, report dir git-ignored.

Key knobs: `lasius_root`, `install_cmd`/`mutate_cmd`/`mutate_report`,
`agent`/`agent_mode` (`bypass` required unattended),
`agent_timeout_ms` (< ~3600000), `actionable_statuses`,
`summary_max_lines`, `branch_prefix`, `default_branch` — see
`params.schema.json`.

## Safety

- Disposable detached worktree; agents never run git — campaign owns
  commit/push/PR. Nothing merges.
- `agent_mode` required — unattended turns can't answer ACP prompts.
- No `--allow-empty` — zero-diff agents fail honestly, no empty PRs.
- Per-id agent lock; `id` charset-validated (rides event types).
- Payload values quote/newline-rejected before env-file persistence.

## Ops

- Logs: `tamias logs kill-mutants`;
  `~/.local/share/peregrin/serve-history/kill-mutants.jsonl`.
- Artifacts kept under `<worktree_base>/{requests,reports}/`
  (`<id>.env`, `-mutation.json`, `-mutants.txt`, `-mutate.log`).
- Worktrees `<worktree_base>/wt-<id>` — removed on every terminal
  outcome (success or failure); a dirty worktree `lasius` refuses to
  remove stays behind.
- Agent sessions: the agent node records the session id at
  `<worktree_base>/sessions/wt-<id>`. Success outcomes (`pr.created.*`,
  `summarize.clean.*`) delete it immediately via `sepia delete`
  (devin-gc cwd sweep as fallback); failure outcomes RETAIN it for 7
  days. Every cleanup appends to `<worktree_base>/cleanup-ledger.jsonl`
  — the reconcile pass inside `peregrin campaign serve` retries
  `failed` entries and expires `retained` ones. A session-delete
  failure emits `kill-mutants.cleanup.failed.*` (reported as
  terminal); a plain `devin-gc` sweep collects untracked leftovers.

## Known gaps

- No post-agent re-mutation verify loop — the PR is the check.
- One package per request; failed stages are terminal (re-run = new id).
- `agent` retry can't fit 3 full sessions in the ~66 min node ceiling.
- Prompt caps at `summary_max_lines` mutants (full file kept anyway).
- `checkout` must resolve under `lasius_root`'s workspace.
- `campaign run` can't inject events — use `campaign serve`.
- Reusing an `id` whose remote `test/<id>` branch diverged fails the
  push (no force) — pick a fresh id.

Pilot-validated domain: `ktbhealth/product` (`packages/crypto` ~95%,
`packages/rbac` baseline 71.5%).
</file_path>
/home/luis/GitHub/9aia/workspace/workflows/kill-mutants/README.md