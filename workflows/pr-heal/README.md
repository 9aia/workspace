# pr-heal

CI failure → agent fix → push → verified green → campaign-driven merge.

A tamias-installable peregrin campaign bundle. When a pull request's CI
check fails, an agent session (sepia — `devin` by default) gets a
detached worktree at the failing head, reproduces the failure, fixes
the root cause, and leaves the tree dirty; the campaign commits and
pushes through lasius, waits for the next CI result via the bupha
worker's `ci.job.completed` event (POST `/api/events/inject` on the
campaign listener — no polling, no forge status round-trip), and
squash-merges through lasius forge once the check on the *current*
head sha is green.

Validated end-to-end in the disposable `luisfuturist/pr-heal-spike`
repo — PR #3 went red → healed → green → merged entirely
campaign-driven.

## Boundaries

| concern | owner |
| --- | --- |
| git / forge (worktree, commit, push, PR, merge) | lasius |
| agent session (create, prompt, mode) | sepia |
| orchestration, routing, policy | peregrin |
| CI job execution + status | bupha |
| distribution, shims, services | tamias |

No raw `git`/`gh`/`devin` anywhere in `main.yaml`.

## Opting a repo in

1. **Clone + fleet entry** — the repo needs a bupha fleet entry so
   `ci-job` entities resolve (`~/.config/bupha/bundles/*.toml`, same
   as ci-ingress/ci-gate).

2. **Webhook secret + events feed** — register a GitHub webhook on the
   repo pointing at the shared listener's public URL
   (`https://tamias.luisfuturist.com/hook` on this deployment) with
   events `push` and `pull_request` — those are the only forge
   deliveries this campaign consumes (CI *completion* no longer
   rides forge `status`/`check_run` webhooks; see below). Put the
   HMAC secret in the campaign env as `BUPHA_WH_<OWNER>_<REPO>`
   (uppercased, `-` → `_`), e.g. `BUPHA_WH_9AIA_MY_REPO` in
   `~/.config/peregrin/env`.

   The completion channel is the bupha worker's `ci.job.completed`
   emit: set `[worker] events_url` (or `BUPHA_WORKER_EVENTS_URL`) in
   the bupha fleet config to the campaign listener's ingest route —
   `http://127.0.0.1:29173/api/events/inject` on this deployment —
   and keep `node_token_env = "PEREGRIN_TOKEN"` (the campaign
   listener's `/api/events/inject` accepts the same bearer). The
   route fans the event into every hosted campaign's trigger
   channel, scoped optionally by `"campaign": "<name>"`. Requires a
   peregrin new enough to serve `/api/events/inject` on `campaign
   serve` (the shared listener) — older builds only expose it on
   `peregrin serve`'s entity plane, which supervised campaigns
   never see.

3. **Configure + install** — `tamias install --allow-drivers
   <path-to-bundle>` then `tamias deploy`. Deploy renders
   `~/.config/peregrin/serve/pr-heal.yaml`, which `include:`s the
   bundle's `main.yaml` and carries a `config:` block — the loader
   deep-merges it over the bundle defaults (outer keys win). Set the
   per-deployment values there:

   | key | required | meaning |
   | --- | --- | --- |
   | `repo` | yes | `owner/name` watched repo |
   | `webhook_secret_env` | yes | env var name holding the HMAC |
   | `checkout` | yes | local clone lasius operates on |
   | `agent` / `agent_mode` | no | sepia agent id + ACP mode (`bypass` default — see below) |
   | `max_agent_attempts` | no | per-PR heal cap (default 3, durable ledger) |
   | `max_conflict_attempts` | no | per-PR conflict-resolution cap (default 2, durable ledger) |
   | `ci_check_name` | no | label used in the agent prompt (default `ci`) — `ci.job.completed` carries no per-check name; the bupha job `key` (`repo` or `repo:<job>`) is the lane identity |
   | `default_branch` | no | push-enqueue gate (default `main`) |
   | `worktree_base`, `node_url`, `lasius_root` | no | paths/URLs |

   If the webhook secret env var isn't in `~/.config/peregrin/env`,
   also add its name under `capabilities.secrets` in the same file
   (the dict deep-merges too). Then
   `systemctl --user restart peregrin-campaign` — every
   peregrin-bundle renders into that one shared service.

   > `tamias deploy` **regenerates** this file — re-apply the config
   > block after every deploy/uninstall cycle.

4. **Agent auth** — the sepia agent (devin) must be authenticated on
   the host; sessions run unattended.

## Safety model

- **Verified-sha merge** — merge only fires when an open PR's *current*
  `head_sha` equals the sha that went green. Stale greens find no PR
  and skip.
- **PR-lookup gate** — heal/merge/push all re-resolve the open PR by
  exact head sha; a superseded sha dies honestly.
- **Per-shPR attempt ledger** — `<worktree_base>/attempts/pr-<n>`
  counts agent runs per PR (default cap 3); over-cap emits
  `attempts.gaveup` and leaves the PR for a human.
- **Per-sha agent lock** — duplicate failure events for one sha can't
  start parallel agents.
- **`agent_mode` is required** — unattended turns cannot answer ACP
  `session/request_permission`; devin's default `accept-edits` prompts
  on exec and deadlocks. `bypass` auto-approves everything (fine in a
  disposable worktree); `smart` is the safer middle ground.
- **Merge conflicts auto-resolve, bounded** — when `lasius forge pr
  merge` fails and `pr view` reports the PR unmergeable
  (`mergeable=CONFLICTING` / `merge_state=DIRTY`, with the merge
  command's own output as fallback signal), the campaign emits
  `merge.conflict.<sha>` instead of terminal `merge.failed`. A
  conflict-heal chain then re-runs the agent loop: detached worktree
  at the PR's *live* head (the merge node persists the PR number in
  `<worktree_base>/conflicts/<sha>` so a moved head still resolves),
  sepia session merges the base branch in and resolves conflicts
  uncommitted, lasius commits (concluding the in-progress merge) and
  pushes `HEAD:refs/heads/<head_ref>`. CI re-runs and the normal
  green→merge path takes over. Budget: `max_conflict_attempts`
  per PR (default 2, `<worktree_base>/attempts/pr-<n>-conflicts`);
  over-cap gives up terminally. Non-conflict merge failures still
  emit `merge.failed` and are reported only.

## Ops

- Run logs: `tamias logs pr-heal` / campaign history JSONL under
  `~/.local/share/peregrin/serve-history/pr-heal.jsonl`.
- Worktrees: `<worktree_base>/<sha12>` — removed automatically after a
  successful push and on PR close; kept on failures/give-ups for
  inspection (`lasius --root <ws> vcs worktree remove <checkout>
  --dir <path>` to gc manually).
- Attempt ledgers: `<worktree_base>/attempts/pr-<n>` (heals) and
  `pr-<n>-conflicts` (conflict resolutions) — delete the file to
  reset that PR's budget for that lane.
- Conflict PR map: `<worktree_base>/conflicts/<sha>` holds the PR
  number for an in-flight conflict resolution — safe to delete once
  the PR merges or the attempt gives up.
