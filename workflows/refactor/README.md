# refactor

Spec-driven refactor workflow — migrated from
`repos/peregrin/libraries/common/refactor` onto the PL-015 ownership
boundaries and packaged as a tamias-installable `peregrin-bundle`.

A lasius worktree is cut from `origin/<base>` on branch
`refactor/<id>`; a sepia agent session analyzes the spec into
`PLAN.md`, a second implements the refactor, then shell gates
(`<check_cmd>`, `<test_cmd>`) run in the worktree. Failures feed an
agent fix loop (max 3), green feeds an agent review whose
`VERDICT: APPROVED|REJECTED` line drives a rework loop (max 3), an
approved refactor gets a docs pass, and the branch is committed and
pushed through lasius. **No PR/merge** — in 9aia the pushed branch is
the deliverable; review/merge is a human/sturn call.

## Boundaries

| concern | owner |
| --- | --- |
| git (fetch, worktree, commit, push) | lasius (`lasius --root <lasius_root> vcs …`) |
| agent sessions (analyze/impl/fix/review/rework/docs) | sepia (`POST <node_url>/api/sessions/run`) |
| orchestration, routing, policy | peregrin |
| distribution, shims, services | tamias |

No raw `git`/`gh`/agent-driver anywhere in `main.yaml`. The bearer
token reaches curl via `--config -` on stdin, never argv.

## Pipeline

```
start → worktree ──► analyze ──► impl ──► check ──► test ──► review
                          │                    ▲          │    │
                          │              (fail)│     pass │    ├─ approved → docs
                          │                    │          │    │            → commit-docs → push → complete
                          │               fix (≤3)        │    └─ rejected → rework (≤3)
                          │                    │          │                 → commit-rework ──► review
                          │                    └── commit-fix ┘
                          └── any *.failed / node.exhausted → abort
```

Rework returns to **review** (not check/test) — same semantics as the
source campaign. Loop bounds: `check` max_fires 4 (initial + 3 fix
cycles), `fix`/`commit-fix`/`rework`/`commit-rework` max_fires 3,
`review` max_fires 6.

## Running

```bash
REFACTOR_ID=my-change \
REFACTOR_DESCRIPTION="generalize claims to typed URIs" \
REFACTOR_SPEC=project/proposals/proposal-0001-*.md \
REFACTOR_CHECKOUT=/home/luis/GitHub/9aia/workspace/repos/sturn \
peregrin campaign run main.yaml
```

`REFACTOR_*` env vars map onto `config:` keys (each config value is
`${env("REFACTOR_X",<default>)}`); the same keys can be set in the
rendered `~/.config/peregrin/serve/refactor.yaml` `config:` block
after `tamias deploy` — outer keys win over bundle defaults.

| key | env | required | meaning |
| --- | --- | --- | --- |
| `checkout` | `REFACTOR_CHECKOUT` | yes | local clone lasius operates on |
| `refactor_id` | `REFACTOR_ID` | yes | branch suffix `refactor/<id>` + worktree slug |
| `refactor_description` | `REFACTOR_DESCRIPTION` | no | one-liner woven into agent prompts |
| `spec` | `REFACTOR_SPEC` | no | spec file the agents read |
| `check_cmd` / `test_cmd` | `REFACTOR_CHECK_CMD` / `REFACTOR_TEST_CMD` | no | gate commands (defaults `cargo xtask check` / `cargo xtask test`) |
| `agent` / `agent_mode` | `REFACTOR_AGENT` / `REFACTOR_AGENT_MODE` | no | sepia agent id + ACP mode (`bypass` default — see safety) |
| `base` | — | no | base branch, worktree rev is `origin/<base>` (default `main`) |
| `worktree_base` | — | no | worktree root (default `~/.local/share/refactor/worktrees`) |
| `lasius_root` | — | no | lasius `--root` (default the 9aia workspace) |
| `node_url` | — | no | `peregrin serve` base URL (default `http://127.0.0.1:18787`) |

`PEREGRIN_TOKEN` must resolve for the agent nodes — ambient env or
`~/.config/peregrin/env` (it is listed under `capabilities.secrets`).

## Safety model

- **Agents never touch git** — prompts forbid git/lasius/forge; every
  commit/push is a campaign node through lasius.
- **`agent_mode` is required** — unattended turns cannot answer ACP
  `session/request_permission`; devin's default `accept-edits` prompts
  on exec and deadlocks. `bypass` auto-approves everything (fine
  inside a disposable worktree); `smart` is the safer middle ground.
- **No `--allow-empty` commits** — a fix/rework/docs pass that produced
  no diff fails the commit honestly instead of looping the gate.
- **Review verdict is explicit** — the review agent must end with
  `VERDICT: APPROVED|REJECTED`; an unparseable response emits
  `review.failed` → abort rather than silently approving.
- **Bounded loops** — fix and rework are capped at 3 agent passes;
  check/test at 4 fires; `node.exhausted` aborts.
- **Worktree reuse** — the path is deterministic per `refactor_id`;
  re-running with the same id removes and recreates the worktree and
  branch (losing uncommitted work there — use a fresh id for a fresh
  attempt).

## Ops

- Logs: `tamias logs refactor` / campaign history under
  `~/.local/share/peregrin/serve-history/` when served; `campaign run`
  prints the event log to stdout (`--history <file>` persists it).
- Worktrees: `<worktree_base>/wt-<slug>` — kept after completion and
  after aborts for inspection. GC manually:
  `lasius --root <lasius_root> vcs worktree remove <checkout> --dir <path>`.
- The pushed branch `refactor/<id>` is the deliverable — open the PR
  by hand (org rule: no PRs from agents).

## Known gaps

- **No lasius branch-delete verb** — the source worktree node ran
  `git branch -D` to clear a stale branch before recreating; lasius
  `vcs` has no equivalent, so a leftover local `refactor/<id>` branch
  from a previous run may collide with `worktree add --branch`.
  Delete it by hand or the worktree node fails honestly.
- **Rework skips the gates** — faithful to the source (rework →
  commit → review), but rework edits are not re-checked/re-tested
  before the next review. The reviewer is told checks are green;
  treat a rejected-then-approved cycle with suspicion.
- **`refactor_id` charset** — it is interpolated into shell commands
  and branch names; keep it slug-like (`[A-Za-z0-9._/-]`). No
  sanitization beyond `/`→`-` and space→`-` for the worktree dir.
- **Docs node assumes a myco ledger** — the prompt mentions updating
  spec status "if it lives in a myco ledger"; nothing verifies it.
- **`campaign run` has no config-override flag** — operator inputs go
  through env vars or a hand-edited copy of `main.yaml`; the rendered
  serve yaml is the deploy-time path.
