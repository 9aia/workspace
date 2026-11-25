import * as github from "@pulumi/github";
import { REPOS } from "./repos.ts";
import { registerRulesets } from "./rulesets.ts";
import { registerTeams } from "./teams.ts";

/**
 * Pulumi program for 9aia org GitHub policies — the 9aia counterpart
 * of ktbhealth/infra/github.
 *
 * Manages:
 * - github.Repository for every repo in REPOS (src/repos.ts):
 *   squash-only merge, delete-branch-on-merge, per-repo visibility,
 *   archived pinned. Import existing repos first — see README.
 * - github.RepositoryRuleset resources codifying "main-protected" +
 *   "guard quality-gate paths" on every public non-archived repo
 *   (src/rulesets.ts); private repos are skipped on the free plan.
 * - github.Team "trusted-contributors" + memberships — the team the
 *   pr-heal/pr-review campaign gates and the code-owner ruleset both
 *   key on (src/teams.ts). Pre-exists; import before first `up`.
 *
 * NO org webhook here: 9aia forge ingress is per-repo bupha webhook
 * secrets (cuora://bupha/BUPHA_WH_9AIA_*), not an org hook, and the
 * admin token lacks admin:org_hook anyway.
 *
 * Auth: a GitHub token with admin:org via `GITHUB_TOKEN` env or
 * `pulumi config set github:token`. CI uses the ORG_ADMIN_TOKEN repo
 * secret (see .github/workflows/github-policy.yml).
 */

for (const repo of REPOS) {
  new github.Repository(
    `repo-${repo.name}`,
    {
      name: repo.name,
      visibility: repo.visibility,
      allowSquashMerge: true,
      allowMergeCommit: false,
      allowRebaseMerge: false,
      deleteBranchOnMerge: true,
      archived: repo.archived,
      hasIssues: repo.hasIssues,
      hasWiki: repo.hasWiki,
      hasProjects: repo.hasProjects,
    },
    {
      // Only the fields above are policy. Everything else on the repo
      // (description, homepageUrl, topics, …) is unmanaged — without
      // ignoreChanges Pulumi would null them out on update.
      ignoreChanges: ["description", "homepageUrl", "topics", "securityAndAnalysis"],
    },
  );
}

registerRulesets({ protect: true });
registerTeams();
