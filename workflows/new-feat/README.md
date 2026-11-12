# new-feat

End-to-end feature implementation workflow — migrated from
`repos/peregrin/libraries/common/new-feat` onto the PL-015 ownership
boundaries.

A tamias-installable peregrin campaign bundle. Manually triggered
(`on: start`): it creates a lasius worktree on a fresh
`feat/<feat_id>` branch off `origin/<pr_base>`, then drives a sepia
agent through ADR → tests → implementation, committing each stage via
lasius, looping agent-fix (≤3) until `test_cmd` passes, opening a PR
via lasius forge, running an agent review with a bounded rework loop
(≤3), and squash-merging via lasius forge.

## Boundaries

| concern | owner |
| --- | --- |
| git / forge (worktree, commit, push, PR create/list/merge) | lasius |
| agent turns (ADR, tests, impl, fix, review, rework) | sepia (`POST /api/sessions/run` → `sessions.prompt_wait`) |
| orchestration, routing, retries, caps | peregrin |
| distribution, shims, services | tamias |

No raw `git`/`gh`/`devin` anywhere in `main.yaml`. The old
`agent/*` snippets (which spawned `devin -p`), the `git/*` snippets
(raw `git worktree add`/`commit`/`push`) and the `github/*` snippets
(raw `gh pr create`/`merge`) are all inlined under the new owners.

## Pipeline

```
start → worktree (lasius) → adr (sepia) → write-tests (sepia)
  → commit-tests (lasius) → impl (sepia) → commit-impl (lasius)
  → test ──fail──► fix (sepia, ≤3) → commit-fix (lasius) ──► test
       └─pass─► pr (lasius push + forge pr create)
         → review (sepia, VERDICT: APPROVE|REJECT)
           ├─ approve → merge (lasius forge pr merge --squash --delete-branch) → report
           └─ reject → rework (sepia, ≤3) → commit-rework (lasius commit+push) → review
```

Any `*.failed` event (or `node.exhausted` when a `max_fires` cap is
hit) routes to `new-feat.abort` → `new-feat.aborted`.

## Running it

`peregrin campaign run` has **no `--config` flag** — per-run knobs go
in the campaign's `config:` block. Use a wrapper yaml (the same
include+config-merge mechanism `~/.config/peregrin/serve/*.yaml`
uses):

```yaml
# run-my-feat.yaml — lives next to wherever you keep run configs
include:
  - /home/luis/GitHub/9aia/workspace/workflows/new-feat/main.yaml
config:
  feat_id: "my-feature"
  feat_description: "add a reusable snippet library"
  checkout: "/home/luis/GitHub/9aia/workspace/repos/<repo>"
  test_cmd: "cargo test"        # optional overrides
  agent: "devin"                # optional
  agent_mode: "bypass"          # optional
```

```bash
peregrin campaign run run-my-feat.yaml
# or, after `tamias install --allow-drivers` + `tamias deploy`, the
# bundle is also usable through the shared campaign service surface.
```

Config deep-merges with outer keys winning, so the wrapper only needs
the keys it overrides.

## Opt-in / config table

| key | required | meaning |
| --- | --- | --- |
| `feat_id` | yes | feature id — branch `feat/<id>`, worktree `wt-<slug>`, `docs/adr/<id>.md`, PR title |
| `feat_description` | no | one-paragraph description for agent prompts + PR body |
| `checkout` | yes | local clone lasius operates on |
| `lasius_root` | no | lasius `--root` workspace (default: the 9aia org workspace) |
| `node_url` | no | `peregrin serve` base URL for `/api/sessions/run` (default `http://127.0.0.1:18787`) |
| `worktree_base` / `worktree_prefix` | no | worktree location (default `~/.local/share/new-feat/worktrees/wt-<slug>`) |
| `branch_prefix` | no | branch prefix (default `feat`) |
| `pr_base` | no | PR base + worktree rev (default `main`) |
| `test_cmd` | no | test command in the worktree (default `bun test` — override per repo) |
| `agent` / `agent_mode` | no | sepia agent id + ACP mode (`bypass` default — see safety) |

Secret: `PEREGRIN_TOKEN` (resolved record → env → keyring →
`~/.config/peregrin/env`, same as pr-heal).

## Safety notes

- **`agent_mode` is required** — unattended turns cannot answer ACP
  `session/request_permission`; devin's default `accept-edits`
  prompts on exec and deadlocks. `bypass` auto-approves everything
  (acceptable inside a disposable worktree the campaign owns);
  `smart` is the safer middle ground.
- **Agent self-review** — the *same* agent that implemented the
  feature reviews its own PR (original semantics preserved). There
  is no independent reviewer and no GitHub review submission; the
  verdict is parsed from the session text (`VERDICT: APPROVE` /
  `VERDICT: REJECT` as the final line). Missing verdict, timeout, or
  transport failure all take the reject path — fail-safe into the
  bounded rework loop.
- **Agents never touch git/forge** — every prompt forbids
  commit/push/PR; all mutations are campaign nodes through lasius.
  `commit-rework` also pushes explicitly so the PR tracks rework.
- **Bounded loops** — fix and rework are capped at 3 fires each;
  exhaustion emits `node.exhausted` → abort.
- **`--allow-empty` commits** — preserved from the old flow: an
  agent turn that produced no diff still commits so the pipeline
  advances (and the test gate decides honestly).
- **Stateless** — no stdout→state channel in the Rust engine, so
  feat_id/worktree/branch are recomputed deterministically per node
  (same pattern as pr-heal). Review feedback rides a file
  (`<worktree_base>/review-<slug>.txt`) instead of event payload.

## Known gaps

- **No `lasius vcs branch delete`** — the old flow deleted a stale
  `feat/<id>` branch before re-creating the worktree. A leftover
  branch now makes `worktree add --branch` fail honestly → abort.
  Delete it manually (`git branch -D feat/<id>` in the checkout) or
  pick a new `feat_id`. TODO marker in `main.yaml`.
- **No `--admin` merge equivalent** — `gh pr merge --admin` bypassed
  branch protection; `lasius forge pr merge` has no admin flag, so a
  protected base branch makes merge fail honestly → abort.
- **No PR-status polling node** — the old flow had no CI gate either
  (review was the only gate), so nothing was lost; if you want
  checks-before-merge, that is a follow-up (pr-heal already covers
  the CI-heal direction).
- **`campaign run` can't override config** — per-run knobs require
  the wrapper-yaml pattern above (or editing `config:` in place).
  `campaign submit --config` exists in newer peregrin but is not in
  the installed 0.2.0 CLI.

## Ops

- Run logs: campaign history JSONL under
  `~/.local/share/peregrin/serve-history/` (serve) or `--history`
  for `campaign run`.
- Worktrees: `<worktree_base>/wt-<slug>` — removed automatically at
  the start of a re-run of the same feat_id; kept after aborts for
  inspection (`lasius --root <ws> vcs worktree remove <checkout>
  --dir <path>` to gc).
- Review text: `<worktree_base>/review-<slug>.txt` — overwritten each
  review round; read it to see why a PR was rejected.
