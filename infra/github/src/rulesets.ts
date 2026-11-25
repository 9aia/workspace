import * as pulumi from "@pulumi/pulumi";
import * as github from "@pulumi/github";
import { REPOS } from "./repos.ts";
import { TRUSTED_TEAM_NUMERIC_ID } from "./teams.ts";

/**
 * Codifies branch rulesets for the 9aia org — same shape as
 * ktbhealth/infra/github (myco T-054 there):
 *
 * - "main-protected" on every eligible repo: block branch deletion +
 *   non-fast-forward on the default branch. Bypass: luisfuturist.
 * - "guard quality-gate paths" on every eligible repo: PR rule on
 *   refs/heads/main requiring code-owner review — so changes to
 *   /.github/workflows/ and /infra/ (owned by @9aia/trusted-contributors
 *   via each repo's .github/CODEOWNERS) can't auto-merge unreviewed
 *   under the pr-heal/pr-review campaigns. Bypass: trusted-contributors.
 *
 * ELIGIBILITY — GitHub free org plan: branch rulesets on PRIVATE repos
 * require a paid plan (same constraint that pushed ktbhealth to flip
 * its drafts public). Rulesets therefore apply to public, non-archived
 * repos only; private repos (atta, camelus, castor, ci-e2e, delphis,
 * mycena, pachira, project) and archived strigi are skipped. Their
 * CODEOWNERS files are still committed — they take effect if the org
 * upgrades or a repo flips public. Upgrading the org to Team removes
 * this filter automatically (the lists derive from repos.ts).
 *
 * Direct push stays allowed — no pull_request_required rule; these
 * rulesets only block deletion, force-push, and unreviewed code-owner
 * path changes on PRs.
 */

/** Bypass actor shared by every main-protected ruleset: luisfuturist. */
const BYPASS_USER = { actorType: "User", actorId: 91754457, bypassMode: "always" } as const;

/** Repos eligible for rulesets on the free plan: public + not archived. */
const RULESET_REPOS = REPOS.filter((r) => r.visibility === "public" && !r.archived).map(
  (r) => r.name,
);

export const registerRulesets = (opts: pulumi.ResourceOptions): void => {
  for (const name of RULESET_REPOS) {
    new github.RepositoryRuleset(
      `ruleset-${name}-main-protected`,
      {
        repository: name,
        name: "main-protected",
        target: "branch",
        enforcement: "active",
        conditions: {
          refName: { includes: ["~DEFAULT_BRANCH"], excludes: [] },
        },
        rules: {
          deletion: true,
          nonFastForward: true,
        },
        bypassActors: [BYPASS_USER],
      },
      opts,
    );

    new github.RepositoryRuleset(
      `ruleset-${name}-guard-quality-gate-paths`,
      {
        repository: name,
        name: "guard quality-gate paths",
        target: "branch",
        enforcement: "active",
        conditions: {
          refName: { includes: ["refs/heads/main"], excludes: [] },
        },
        rules: {
          pullRequest: {
            requiredApprovingReviewCount: 0,
            dismissStaleReviewsOnPush: false,
            requireCodeOwnerReview: true,
            requireLastPushApproval: false,
            requiredReviewThreadResolution: false,
            requiredReviewers: [],
            allowedMergeMethods: ["squash"],
          },
        },
        bypassActors: [
          { actorType: "Team", actorId: TRUSTED_TEAM_NUMERIC_ID, bypassMode: "always" },
        ],
      },
      opts,
    );
  }
};
