import * as github from "@pulumi/github";

/**
 * `trusted-contributors` — the org's trusted-author team. Campaign
 * gates (workflows/pr-heal + ktbhealth workflows/pr-review
 * trusted_actors check) treat ACTIVE membership here as the
 * allowlist: PRs authored by team members may reach the agent and
 * auto-merge; everyone else is skipped. Membership grants NO repo
 * permissions — it is a policy marker, not an access grant. The same
 * team is the code-owner for policy paths (rulesets.ts + each repo's
 * .github/CODEOWNERS).
 *
 * The team and its memberships PRE-EXIST (created via API before this
 * program). Bootstrap imports them — see README for the `pulumi
 * import` list:
 *   pulumi import github:index/team:Team trusted-contributors 20874639
 *   pulumi import github:index/teamMembership:TeamMembership \
 *     trusted-luisfuturist 20874639:luisfuturist   (etc per member)
 */
const TRUSTED_TEAM_ID = "20874639";

const TRUSTED_CONTRIBUTORS = [
  "luisfuturist",
  "vinicenter",
  "Kruceo",
  "eccarneiro",
] as const;

export function registerTeams(): void {
  const team = new github.Team("trusted-contributors", {
    name: "Trusted Contributors",
    description:
      "Trusted contributors — the only non-admin authors allowed to trigger agent/auto-merge flows, and the code-owner team for policy paths (workflows/, infra/).",
    privacy: "closed",
  });

  for (const username of TRUSTED_CONTRIBUTORS) {
    new github.TeamMembership(`trusted-${username}`, {
      teamId: team.id,
      username,
      role: "member",
    });
  }
}

/** Team id for ruleset bypass actors — kept in sync with the Team above. */
export const TRUSTED_TEAM_NUMERIC_ID = Number(TRUSTED_TEAM_ID);
