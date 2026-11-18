# kill-mutants

StrykerJS mutation testing → agent triage → tests → PR.

A tamias-installable peregrin campaign bundle. An operator injects a
`mutate.requested` event naming a repo checkout and a package with a
`stryker.conf.json`; the campaign cuts a lasius worktree, installs
dependencies, runs the package's mutation suite, summarizes the
survivors, hands them to a sepia agent session that kills real gaps
with new tests (and silences only *empirically proven*
equivalent/unreachable mutants), then commits, pushes and opens a PR —
all git/forge operations through lasius.

Pilot-validated domain: `ktbhealth/product` `packages/crypto`
(per-package `stryker.conf.json` + `"mutate": "stryker run"`,
`reports/mutation/mutation.json` report, ~2–5 min runs).

## Boundaries

| concern | owner |
| --- | --- |
| git / forge (fetch, worktree, commit, push, PR create) | lasius (`lasius --root <lasius_root> vcs|forge …`) |
| agent session (create, prompt, mode) | sepia (`POST <node_url>/api/sessions/run`) |
| orchestration, routing, policy | peregrin |
| distribution, shims, services | tamias |

No raw `git`/`gh`/`devin` anywhere in `main.yaml`. The bearer token
reaches curl via `--config -` on stdin, never argv.

## Triggering a run

There is no webhook ingress — runs are operator-injected events on the
shared campaign listener (`campaign serve`, `:29173` on this
deployment):

```bash
curl -X POST http://127.0.0.1:29173/api/events/inject \
  -H "authorization: Bearer $PEREGRIN_TOKEN" \
  -H 'content-type: application/json' \
  -d '{
    "type": "mutate.requested",
    "payload": {
      "id": "crypto-mutation",
      "package": "packages/crypto",
      "checkout": "/home/luis/GitHub/ktbhealth/repos/product",
      "base_branch": "main"
    },
    "idempotencyKey": "crypto-mutation-1",
    "campaign": "kill-mutants",
    "source": "ops"
  }'
```

Payload fields (all strings):

| field | required | meaning |
| --- | --- | --- |
| `id` | yes | run id — `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. Keys the worktree (`wt-<id>`), request file, artifacts and branch (`test/<id>`). **Unique per run.** Convention: `<pkg>-mutation` → branch `test/<pkg>-mutation`. |
| `package` | yes | package dir relative to the checkout root, containing `stryker.conf.json` (e.g. `packages/crypto`). |
| `checkout` | yes* | local clone path lasius operates on. *Falls back to `config.checkout`. |
| `base_branch` | no | PR base + worktree rev (default `config.default_branch` = `main`). |

`idempotencyKey` dedups transport retries at the ingest layer; `id`
itself is not deduped — pick a fresh id per logical run (see Safety).

Response `{"ok": true, "delivered": N}` means the event fanned into
the running campaign's trigger channel; watch progress with
`tamias logs kill-mutants` or the history JSONL (Ops below).

## Pipeline

```
mutate.requested ──route──► requested.<id>
   │  validate payload + stat <checkout>/<pkg>/stryker.conf.json,
   │  persist <worktree_base>/requests/<id>.env
   ▼
worktree ──► install ──► mutate ──► summarize ──► agent ──► push ──► pr ──► cleanup ──► report
 (lasius    (config.   (config.    (jq counts +   (sepia   (lasius  (lasius  (lasius   (terminal
  fetch +    install_   mutate_     detail file;   session,  commit  forge    worktree   echo)
  worktree   cmd @ wt   cmd @ pkg,  zero          tests +   + push  pr       remove)
  add        root)      tee log,    actionable →   proven     HEAD:…) create)
  test/<id>)            report      clean.<id>)   disables)
                                     must parse)
```

Failure at any stage emits `*.<stage>.failed.<id>` (or the un-suffixed
`request.invalid`/`request.failed`) → terminal `report`. Failed runs
keep their worktree for inspection.

## Installing & configuring

1. **Prereqs on the host** — `lasius` (any lasius.toml workspace via
   `lasius_root`), `bun`/`jq`/`curl`, a sepia agent (default `devin`)
   authenticated for unattended sessions, and `PEREGRIN_TOKEN`
   resolvable (`~/.config/peregrin/env` — it is listed under
   `capabilities.secrets`).

2. **Repo prereqs** — the target package needs:
   - `stryker.conf.json` with a `jsonReporter` writing
     `reports/mutation/mutation.json` (the `mutate_report` default);
   - a `"mutate": "stryker run"`-style script (the `mutate_cmd`
     default is `bun run mutate`, run inside the package dir);
   - **no `thresholds.break`** in `stryker.conf.json` — Stryker must
     exit 0 on a completed run; survivors are data, not failures;
   - the report dir git-ignored (e.g. `**/reports/mutation/` —
     ktbhealth/product already does). `lasius vcs commit` stages
     everything; an un-ignored `mutation.json` would land in the PR.
     The agent is also instructed to keep report artifacts out, but
     the ignore rule is the real guard.

3. **Install + deploy** — `tamias install --allow-drivers
   <path-to-bundle>` then `tamias deploy`. Deploy renders
   `~/.config/peregrin/serve/kill-mutants.yaml`, which `include:`s
   the bundle's `main.yaml` and carries a `config:` block — the
   loader deep-merges it over the bundle defaults (outer keys win).
   Set per-deployment values there (see the table below), then
   `systemctl --user restart peregrin-campaign` — every
   peregrin-bundle renders into that one shared service.

   > `tamias deploy` **regenerates** this file — re-apply the config
   > block after every deploy/uninstall cycle.

   | key | required | meaning |
   | --- | --- | --- |
   | `checkout` | no* | fallback clone path when the payload omits `checkout` |
   | `agent` / `agent_mode` | no | sepia agent id + ACP mode (`bypass` default — see safety) |
   | `install_cmd` / `mutate_cmd` / `mutate_report` | no | package-manager + stryker invocation (defaults fit bun monorepos) |
   | `actionable_statuses` / `summary_max_lines` | no | which mutant statuses reach the agent; prompt detail cap |
   | `branch_prefix` / `default_branch` | no | `test/<id>` branch prefix; fallback PR base |
   | `agent_timeout_ms` | no | session timeout (default 30 min; keep < ~3600000 — the node ceiling is ~66 min) |
   | `worktree_base`, `node_url`, `lasius_root` | no | paths/URLs |

   Alternatively run once without deploying:
   `peregrin campaign run main.yaml` — but `mutate.requested` is an
   injected event, so the served campaign (`campaign serve`) is the
   practical path; `campaign run` has no inject endpoint.

## What the agent is told

The triage prompt (built by `kill-mutants.agent`) carries the
package path, branch/base, and the survivor detail file
(`<worktree_base>/reports/<id>-mutants.txt` — one line per actionable
mutant: `file:line [mutator] status — reason → replacement`). Rules:

- kill survivors by adding/strengthening tests; re-run the package
  suite (and optionally the mutation suite) to verify;
- `// Stryker disable next-line <mutator>: <reason>` is allowed
  **only** after empirically proving equivalence/unreachability —
  never assumed; killing is preferred over disabling;
- a mutant exposing a real bug may be fixed, and must be called out;
- stay inside the package (+ test-required root changes); English;
  follow repo test conventions; no git/lasius/forge commands; no
  commits — the campaign owns all of that.

## Safety model

- **Bounded blast radius** — work happens in a disposable lasius
  worktree on `test/<id>`; nothing touches the operator's checkout.
  Agents never run git — every commit/push/PR is a campaign node.
- **`agent_mode` is required** — unattended turns cannot answer ACP
  `session/request_permission`; devin's default `accept-edits`
  prompts on exec and deadlocks. `bypass` auto-approves everything
  (fine in a disposable worktree); `smart` is the safer middle ground.
- **Honest empty results** — no `--allow-empty` commits: an agent
  that produced no diff fails the push instead of opening an empty
  PR. Zero actionable mutants skips the agent entirely
  (`summarize.clean.<id>` → cleanup → report).
- **Per-id agent lock** — a second `agent` fire for the same id
  while a session is in flight exits instead of double-running
  (`<worktree_base>/wt-<id>.agent-lock`, released on every exit).
- **Unique-id contract** — `id` keys the worktree path, request file,
  branch and artifacts. Re-using an id removes the stale worktree and
  re-creates the branch (losing uncommitted work there). The route
  node restricts `id` to `[A-Za-z0-9][A-Za-z0-9._-]{0,63}` and rejects
  payload values containing quotes/newlines before they are
  single-quoted into the request env file.
- **Payload validation at the door** — missing fields, unsafe
  `package` paths (`..`, absolute, odd charset) or a missing
  `stryker.conf.json` emit `request.invalid` before any worktree or
  install happens (checked against both the checkout and the fresh
  worktree).
- **Report integrity** — `mutate` requires exit 0 AND a parseable
  JSON report; `summarize` copies the report out of the worktree
  before cleanup so artifacts survive.

## Ops

- Logs: `tamias logs kill-mutants` / campaign history JSONL under
  `~/.local/share/peregrin/serve-history/kill-mutants.jsonl`.
- Worktrees: `<worktree_base>/wt-<id>` — removed automatically after
  PR creation and on clean runs; **kept on failures** for inspection
  (`lasius --root <lasius_root> vcs worktree remove <checkout> --dir
  <path>` to gc manually).
- Artifacts (kept after cleanup):
  - `<worktree_base>/requests/<id>.env` — the validated request
    (package/checkout/base/branch);
  - `<worktree_base>/reports/<id>-mutation.json` — the Stryker report
    copy;
  - `<worktree_base>/reports/<id>-mutants.txt` — the agent-facing
    survivor summary;
  - `<worktree_base>/reports/<id>-mutate.log` — raw stryker output.
- Branches: `test/<id>` stays open as the PR head until a human
  merges/closes it (org rule: no agent merges).
- Re-run: inject a fresh `id` — never reuse one whose worktree you
  still need.

## Known gaps

- **No per-stage retry budgets** — unlike pr-heal's per-PR attempt
  ledger, a failed stage is terminal for that id; re-run with a new
  id. `agent`/`mutate` node `retry` blocks cover transient transport
  failures only.
- **No re-mutation verification** — the campaign does not re-run
  stryker after the agent to prove the score improved; the agent is
  told to verify kills itself, and CI/humans judge the PR. A
  verify-loop stage is a natural v2.
- **Single-package scope** — one `package` per request; monorepo-wide
  mutation runs are N requests (or a future fan-out node).
- **`checkout` must be a lasius-visible path** — the route node stats
  `<checkout>/<package>/stryker.conf.json` directly, so a bare clone
  *name* under `repos_dir` only works if it also resolves as a path;
  pass absolute paths.
- **Prompt-size ceiling** — `summary_max_lines` (default 300) caps
  the survivor list in the agent prompt; packages with thousands of
  survivors get a truncated view (full detail stays in the artifact
  file the agent can also read).
