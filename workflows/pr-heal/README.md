# pr-heal

CI failure → agent fix → push → verified green → campaign-driven merge.

A tamias-installable peregrin campaign bundle. When a pull request's CI
check fails, an agent session (sepia — `devin` by default) gets a
detached worktree at the failing head, reproduces the failure, fixes
the root cause, and leaves the tree dirty; the campaign commits and
pushes through lasius, waits for the next CI result via GitHub
webhooks (no polling), and squash-merges through lasius forge once the
check on the *current* head sha is green.

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

2. **Webhook secret** — register a GitHub webhook on the repo pointing
   at the shared listener's public URL (`https://tamias.luisfuturist.com/hook`
   on this deployment) with events `push`, `pull_request`,
   `check_run`, `status`. Put the HMAC secret in the campaign env as
   `BUPHA_WH_<OWNER>_<REPO>` (uppercased, `-` → `_`), e.g.
   `BUPHA_WH_9AIA_MY_REPO` in `~/.config/peregrin/env`.

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
   | `ci_check_name` | no | `check_run.name` to react to (default `ci`) |
   | `default_branch` | no | push-enqueue gate (default `main`) |
   | `worktree_base`, `node_url`, `lasius_root` | no | paths/URLs |

   If the webhook secret env var isn't in `~/.config/peregrin/env`,
   also add its name under `capabilities.secrets` in the same file
   (the dict deep-merges too). Then
   `systemctl --user restart peregrin-campaign` — every
   peregrin-bundle renders into that one shared service.

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
- **Merge conflicts are NOT auto-resolved** — a `merge.failed` is
  reported terminally; resolving conflicts (merge base → agent rework
  loop) is tracked as follow-up hardening.

## Ops

- Run logs: `tamias logs pr-heal` / campaign history JSONL under
  `~/.local/share/peregrin/serve-history/pr-heal.jsonl`.
- Worktrees: `<worktree_base>/<sha12>` — removed automatically after a
  successful push and on PR close; kept on failures/give-ups for
  inspection (`lasius --root <ws> vcs worktree remove <checkout>
  --dir <path>` to gc manually).
- Attempt ledger: `<worktree_base>/attempts/pr-<n>` — delete the file
  to reset a PR's heal budget.
