# docs-deploy

Docs-site deployment as a peregrin bundle (PL-009 / P-009): on a
verified `push` to a watched repo's `refs/heads/docs` (or
`refs/heads/main` for `9aia.github.io`, whose site *is* main) →
detached worktree at the pushed sha → `bun install` + the repo's own
`docs:deploy` (vitepress build → `gh-pages`) → GitHub commit status
under `docs/deploy`. This is the campaign-shaped replacement for the
GHA `deploy.yml` workflows deleted org-wide in C3.

## v1 scope (D1 audit + D6 dual-checkout)

Two repo shapes, one campaign:

- **Self-contained** — the `docs` orphan branch *is* the site
  checkout (`package.json` + `bun.lock` + `.vitepress/` at its
  root), so the worktree root is the build root: `9aia/sepia`,
  `9aia/peregrin`, `9aia/lasius`.
- **Gen-dependent** — `docs:deploy` runs `docs:gen`/`docs:api`
  steps that `cd ..` into the main checkout for `cargo run` /
  `cargo doc`: `9aia/myco`, `9aia/tamias`, `9aia/cuora`, `9aia/pavo`,
  `9aia/hypha`, `9aia/sturn`, `9aia/kuda`, `9aia/mimus`, `9aia/bupha`.
  Their deploy nodes build the D6 dual checkout in shell: a
  `main_ref` worktree at `<run>` plus the docs-branch worktree at
  `<run>/docs`, with the deploy cmd's cwd the docs worktree —
  exactly the dev layout (`repo/` + `repo/docs/` worktree), so
  `cd ..` hits the main checkout and the gen scripts' `docs/…`
  output paths land back in the docs tree. Both checkouts are
  destroyed with the run.
- **Main-branch site** — `9aia/9aia.github.io`: the org site lives on
  `main` (no `docs` branch), so its triplet subscribes
  `push.9aia/9aia.github.io.refs/heads/main.**.*`. Self-contained —
  the repo root IS the site (`bun install` + `docs:deploy` =
  `vitepress build` → `bunx gh-pages -d dist`). Its `secret_env` is
  `BUPHA_WH_9AIA_GITHUB_IO` (dots in the repo name can't ride an env
  var). **Operator step:** the repo's Pages source is currently
  `build_type: workflow` (the deleted `deploy.yml`'s
  `actions/deploy-pages`); switch it once to *Deploy from a branch →
  `gh-pages` / (root)* — the built output is identical, only the
  delivery mechanism changes.

The shipped `cmd` exports a persistent per-host
`CARGO_TARGET_DIR=$HOME/.local/share/peregrin/cargo-target` — the
worktrees are ephemeral, so without it every deploy cold-builds the
gen step and can exceed the 600s inner-shell cap. (mimus's
`docs:api` pins `CARGO_TARGET_DIR=target` itself, so it stays
cold — a repo-side fix, not ours.)

**Converted — `9aia.github.io`** (was deferred): migrated pnpm → bun
(`bun.lock`, `docs:deploy` script on the repo's `ghpages-conv`
branch), and its triplet watches `refs/heads/main`. Remaining ops:
create the `BUPHA_WH_9AIA_GITHUB_IO` webhook secret + forge hook, and
switch the repo's Pages source from Actions-artifact to the
`gh-pages` branch (see v1 scope above).

## Mechanics

- **Ingress**: `docs.ingress.webhook` (`github-webhook`) watches the
  thirteen repos; `secret_env` names follow the existing
  `BUPHA_WH_<OWNER>_<REPO>` convention (dots sanitized —
  `9aia.github.io` → `BUPHA_WH_9AIA_GITHUB_IO`) — *names only*, granted via
  `capabilities.secrets` (`BUPHA_TOKEN` + the thirteen `BUPHA_WH_*`).
  `~/.config/peregrin/env` must carry a `BUPHA_WH_9AIA_<REPO>` value
  per watched repo plus `BUPHA_TOKEN`. As of D6 the env file already
  has `BUPHA_WH_9AIA_{BUPHA,CUORA,KUDA,MIMUS,MYCO,PEREGRIN,STURN}`;
  ops must add `BUPHA_WH_9AIA_{SEPIA,LASIUS,TAMIAS,PAVO,HYPHA}` plus
  `BUPHA_WH_9AIA_GITHUB_IO` (and
  confirm `BUPHA_TOKEN`). The webhook node resolves every listed
  `secret_env` at startup, so all thirteen values must exist before
  deploying — a repo whose secret is missing fails the whole
  ingress, not just its own pushes.
- **Routing**: `docs.route` re-emits every verified push as
  `push.<repo>.<ref>.<clone_url>.<sha>`; per-repo pipelines subscribe
  `push.<repo>.refs/heads/docs.**.*` — except `9aia.github.io`, which
  subscribes `refs/heads/main` — so main-branch pushes on the other
  repos route but match nothing (ci-gate's territory).
- **Deploy**: each pipeline is a `driver: shell` node that drives
  **lasius** end-to-end (the org rule: all VCS/forge ops go through
  lasius — `driver: git`/`driver: github-status` are gone). It
  clone-if-missing's via `lasius add <clone>` (a no-op when the clone
  exists under `config.lasius_root`), `lasius vcs fetch`es, then
  `lasius vcs worktree add --rev <sha>` materializes the detached
  checkout under `worktree_base/docs-<repo>-<sha>`; an `EXIT` trap
  `lasius vcs worktree remove`s it. Gen-dependent repos add a second
  worktree of `config.main_ref` (`origin/main` — remote-tracking, so
  it reflects the last fetch) at the run root `<run>` *before* the
  nested `<run>/docs` docs-branch checkout — the same D6 layout the
  git driver's `extra_worktrees` produced; teardown removes
  `docs/` first, then the run root. The deploy command itself
  (`config.cmd`) is the repo's own `docs:deploy` — unchanged.
- **Secrets**: node `env:` injects `BUPHA_TOKEN` (the shipped cmd's
  gh-pages `credential.helper` reads `$BUPHA_TOKEN`) and `GH_TOKEN`
  (`gh api` inside `lasius forge`/`lasius add`) from
  `secret.BUPHA_TOKEN` — secret *values* still never appear in the
  campaign.
- **gh-pages auth**: the worktree's `origin` is the lasius clone's
  own remote, so `gh-pages` detects the repo itself. The shipped cmd
  exports an env-scoped `credential.helper` (reads `$BUPHA_TOKEN`)
  plus author/committer env — the token never lands in any git
  config, and `GIT_CONFIG_*` env propagates into gh-pages' internal
  git invocations. If you override `cmd`, keep that export.
- **Statuses**: `pending` on gate, verdict (`done.*`→success,
  `failed.*`→failure) under context `docs/deploy`, posted by
  `lasius forge status create` (`gh api repos/{o}/{r}/statuses/{sha}`).
  Event types now carry the sha — `docs.<repo>.done.<sha>` /
  `docs.<repo>.failed.<sha>` — because shell events have no
  `payload.sha` for the status node to template (pr-heal's `*.{sha}`
  convention); `on:` subscriptions use the `.*` wildcards. Spawn-level
  `node.failed`s still route through `docs.failmap`.
- **Supersede**: `{repo}:{ref}` latest-wins, `cancel_running: true`.

## Install + deploy (tamias provider flow)

```sh
tamias install ./libraries/docs-deploy
tamias deploy docs-deploy        # → peregrin-campaign.service (shared)
```

`tamias install`/`deploy` dispatch `tamias-driver-peregrin`, which
writes `~/.config/peregrin/docs-deploy.yaml` **and** the campaign-host
copy `~/.config/peregrin/serve/docs-deploy.yaml` (`include:` of the
bundle's `main.yaml`). Because the campaign yaml ships its own
webhook node, `provider.ingress` deliberately declares **no**
`hooks[]` — otherwise deploy would generate a second ingress node
(`PEREGRIN_WH_*` names) and every push would double-deliver.

**Shared campaign host (T8-7):** `provider.name: peregrin` is the
provider identity every `peregrin-bundle` shares, so this bundle's
`campaign` service renders the same `peregrin-campaign.service` as
ci-gate's — ONE unit running `campaign serve
~/.config/peregrin/serve`, which hosts every deployed bundle's
generated config on a single `SharedWebhook` listener demuxed by
`repository.full_name` (per-node `listen`/`path` are ignored under
`serve`). There is no per-bundle standalone unit anymore; keep the
`exec` identical to the other bundles' (last deploy wins the unit
file). `tamias uninstall docs-deploy` removes this bundle's host
config; the shared unit survives while any bundle still declares it.

Forge-hook registration (pointing each repo's webhook at the public
URL) and adding the missing `BUPHA_WH_9AIA_*` values to
`~/.config/peregrin/env` (see Ingress above) are operator steps.

## Params (validated against `params.schema.json`)

| Key | Default | Meaning |
| --- | --- | --- |
| `worktree_base` | `~/.local/share/peregrin/worktrees` | Base dir for `docs-<repo>-<sha>` worktree runs |
| `lasius_root` | `/home/luis/GitHub/9aia/workspace` | lasius `--root` — clone names resolve under `<root>/repos/` |
| `token_env` | `BUPHA_TOKEN` | Secret **name** injected as `BUPHA_TOKEN` + `GH_TOKEN` |
| `timeout` | `600` | Inner deploy-command cap, seconds (node shell cap: 900) |
| `context` | `docs/deploy` | Commit-status context (via `lasius forge status create`) |
| `main_ref` | `origin/main` | Rev checked out at `<run>` for gen-dependent repos' dual-checkout |
| `cmd` | see `main.yaml` | Deploy command at the worktree root |

## Migration note (lasius boundaries)

This bundle was migrated off `driver: git` + `driver:
github-status` onto lasius verbs — every clone/fetch/worktree/status
call is now `lasius vcs …` / `lasius forge status create` inside
`driver: shell` nodes (same pattern as `workflows/pr-heal`).
Semantic deltas vs the git driver:

- **Clone source**: worktrees come from the lasius workspace clone
  (`<lasius_root>/repos/<name>`), not a private bare-clone cache under
  `worktree_base/.repos` keyed on the webhook `clone_url`. The clone
  must exist (or be clonable via `lasius add`, which needs `gh repo
  list` access); fetch/push auth is whatever the clone's own remote
  uses — the old argv-scoped `http.extraHeader` token injection is
  gone.
- **`main_ref`**: now `origin/main` (remote-tracking, fresh after
  `lasius vcs fetch`) instead of `refs/heads/main` — the old driver
  fetched `+refs/heads/*:refs/heads/*` into its bare cache so its
  `refs/heads/main` *was* remote-fresh; a lasius clone's local
  `refs/heads/main` can lag.
- **Event types**: `docs.<repo>.done`/`.failed` →
  `docs.<repo>.done.<sha>`/`.failed.<sha>` (sha in the type — shell
  events carry no `payload.sha`). Anything subscribing to the bare
  types must move to the `.*` wildcard.
- **Status auth**: `lasius forge status create` shells `gh api`,
  authed by `GH_TOKEN` (injected from `secret.BUPHA_TOKEN`) — same
  token, different transport (gh CLI vs raw REST).
