# infra/github — 9aia org GitHub policies

Pulumi (`@pulumi/github`) codifying org-level GitHub policy for
`github.com/9aia` — the 9aia counterpart of
`ktbhealth/infra/github`. Applied via `.github/workflows/github-policy.yml`
on push to `main` (paths `infra/github/**`), PR preview, daily schedule,
and `workflow_dispatch`.

- **`src/repos.ts`** — explicit desired-state map for all 32 org repos:
  squash-only merge (`allow_merge_commit`/`allow_rebase_merge` off),
  `delete_branch_on_merge`, per-repo `visibility` (public/private mix is
  intentional — never flip), `archived` pinned (strigi stays archived).
  - Merge settings were NOT uniform before this program — the
    squash-only baseline is a deliberate org-wide policy change.
- **`src/rulesets.ts`** — branch rulesets on every **public,
  non-archived** repo (free plan has no rulesets on private repos):
  - `main-protected` — deletion + non-fast-forward on the default
    branch, bypass luisfuturist.
  - `guard quality-gate paths` — PR rule on `refs/heads/main` with
    code-owner review, bypass `@9aia/trusted-contributors`. Each repo's
    `.github/CODEOWNERS` maps `/.github/workflows/` and `/infra/` to
    that team, so agent-driven campaigns (pr-heal, pr-review) cannot
    merge policy/infra changes without trusted-contributor review.
  - Private repos (atta, camelus, castor, ci-e2e, delphis, mycena,
    pachira, project) are skipped — upgrading the org to a paid plan
    removes the filter automatically (lists derive from `repos.ts`).
- **`src/teams.ts`** — `trusted-contributors` team + memberships. The
  team PRE-EXISTS (created via API for the campaign gates) and the
  memberships pre-exist, so bootstrap imports them — see below.
- **No org webhook** — 9aia forge ingress is per-repo bupha webhook
  secrets (`cuora://bupha/BUPHA_WH_9AIA_*`), not an org hook.

## Bootstrap (one-time)

```sh
cd infra/github
bun install
pulumi stack init prod
```

State backend: Cloudflare R2 DIY backend — bucket `9aia-pulumi-state`
on the same account as ktbhealth's (`PULUMI_BACKEND_URL` is set in the
workflow env; locally export the same plus):

```sh
export AWS_ACCESS_KEY_ID=...        # R2 token, cuora://9aia/r2-access-key-id
export AWS_SECRET_ACCESS_KEY=...    # cuora://9aia/r2-secret-access-key
export AWS_REGION=auto
export PULUMI_CONFIG_PASSPHRASE=... # cuora://9aia/pulumi-passphrase
export GITHUB_TOKEN=...             # admin:org PAT — cuora://peregrin/GITHUB_TOKEN works
```

Then import the pre-existing resources (all repos, the team, and its
memberships) so `pulumi up` converges instead of recreating:

```sh
# 32 repos — repo-<name> → 9aia/<name>
for r in $(gh repo list 9aia --limit 100 --json name -q '.[].name'); do
  pulumi import github:index/repository:Repository "repo-$r" "9aia/$r"
done
# team + memberships (import IDs: team numeric id / teamid:username)
pulumi import github:index/team:Team trusted-contributors 20874639
for u in luisfuturist vinicenter Kruceo eccarneiro; do
  pulumi import github:index/teamMembership:TeamMembership \
    "trusted-$u" "20874639:$u"
done
pulumi up --stack prod
```

After `up`, verify zero drift: `pulumi preview --stack prod`.

## CI secrets (repo: 9aia/workspace)

`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `PULUMI_CONFIG_PASSPHRASE`,
`ORG_ADMIN_TOKEN` — set via `gh secret set` (values in cuora, never in
the repo).
