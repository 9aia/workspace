/**
 * Desired state for every 9aia org repository.
 *
 * Explicit list — NOT auto-discovered — so adding a repo to the org is a
 * deliberate act: either add it here (managed by Pulumi) or it stays
 * unmanaged until someone decides.
 *
 * Current-state notes (verified via `gh api` 2026-11-25):
 * - Visibility is pinned per repo — the org intentionally mixes public
 *   and private; Pulumi must never flip it.
 * - Merge settings are NOT uniform today: newer tooling repos are
 *   already squash-only, most older repos still allow merge/rebase.
 *   This codifies the ktbhealth baseline (squash-only +
 *   delete-branch-on-merge) org-wide.
 * - strigi is ARCHIVED — rulesets can't be applied while archived;
 *   bootstrap unarchives it, applies, then re-archives (see README).
 * - has_issues/has_wiki/has_projects are pinned to their current
 *   values so `pulumi import` produces no drift; only the policy
 *   fields are managed, everything else is left to GitHub defaults.
 */
export interface RepoSpec {
  readonly name: string;
  readonly visibility: "public" | "private";
  readonly hasIssues: boolean;
  readonly hasWiki: boolean;
  readonly hasProjects: boolean;
  /** Archived repos are managed as archived — Pulumi must never
   *  silently unarchive (or archive) a repo. */
  readonly archived: boolean;
}

export const REPOS: readonly RepoSpec[] = [
  { name: ".github", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "9aia.github.io", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "atta", visibility: "private", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "bupha", visibility: "public", hasIssues: false, hasWiki: false, hasProjects: false, archived: false },
  { name: "camelus", visibility: "private", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "castor", visibility: "private", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "ci-e2e", visibility: "private", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "cicada", visibility: "public", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "cuora", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "cypera", visibility: "public", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "delphis", visibility: "private", hasIssues: false, hasWiki: false, hasProjects: false, archived: false },
  { name: "hypha", visibility: "public", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "kuda", visibility: "public", hasIssues: false, hasWiki: false, hasProjects: false, archived: false },
  { name: "lampy", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "lasius", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "mimus", visibility: "public", hasIssues: false, hasWiki: false, hasProjects: false, archived: false },
  { name: "mycena", visibility: "private", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "myco", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "pachira", visibility: "private", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "pavo", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "peregrin", visibility: "public", hasIssues: false, hasWiki: false, hasProjects: false, archived: false },
  { name: "project", visibility: "private", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "scarab", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "sepia", visibility: "public", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "slidev-theme-9aia", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "strigi", visibility: "public", hasIssues: false, hasWiki: false, hasProjects: false, archived: true },
  { name: "sturn", visibility: "public", hasIssues: false, hasWiki: false, hasProjects: false, archived: false },
  { name: "tamias", visibility: "public", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "tardigrada", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "tarsi", visibility: "public", hasIssues: true, hasWiki: false, hasProjects: true, archived: false },
  { name: "vitepress-theme-9aia", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
  { name: "workspace", visibility: "public", hasIssues: true, hasWiki: true, hasProjects: true, archived: false },
];
