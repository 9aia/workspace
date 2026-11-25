#!/usr/bin/env bash
# add-codeowners.sh — commit a standard .github/CODEOWNERS to every
# 9aia org repo clone (skips archived strigi; clones missing repos
# shallow). Idempotent: skips repos whose CODEOWNERS already matches.
#
# Usage: add-codeowners.sh [--dry-run]
set -uo pipefail

WS="$(cd "$(dirname "$0")/.." && pwd)"
REPOS_DIR="$WS/repos"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

REPOS=".github 9aia.github.io atta bupha camelus castor ci-e2e cicada cuora cypera delphis hypha kuda lampy lasius mimus mycena myco pachira pavo peregrin project scarab sepia slidev-theme-9aia sturn tamias tardigrada tarsi vitepress-theme-9aia workspace"

CODEOWNERS='# Code owners — changes to these paths require owner review before merge.
# Enforced by the "guard quality-gate paths" ruleset (infra/github).
# NOTE: direct pushes bypass review entirely — pair with a ruleset.

# CI definition — workflow changes can weaken or bypass gates.
/.github/workflows/  @9aia/trusted-contributors

# Org policy-as-code — Pulumi programs, infra definitions.
/infra/  @9aia/trusted-contributors
'

for r in $REPOS; do
  d="$REPOS_DIR/$r"
  if [ ! -d "$d/.git" ]; then
    echo "CLONE  $r (missing)"
    [ $DRY = 0 ] && git clone --depth 1 "https://github.com/9aia/$r" "$d" >/dev/null 2>&1
    continue
  fi
  cur="$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null)"
  dirty="$(git -C "$d" status --porcelain | head -1)"
  existing="$(cat "$d/.github/CODEOWNERS" 2>/dev/null)"
  if [ "$existing" = "$(printf '%s' "$CODEOWNERS")" ]; then echo "SKIP   $r (already matches)"; continue; fi
  if [ -n "$dirty" ]; then echo "SKIP   $r (dirty tree: $cur)"; continue; fi
  echo "WRITE  $r ($cur)"
  [ $DRY = 1 ] && continue
  git -C "$d" pull --ff-only -q >/dev/null 2>&1 || { echo "SKIP   $r (pull failed)"; continue; }
  mkdir -p "$d/.github"
  printf '%s' "$CODEOWNERS" > "$d/.github/CODEOWNERS"
  git -C "$d" add .github/CODEOWNERS
  git -C "$d" diff --cached --quiet && { echo "SKIP   $r (no change)"; continue; }
  git -C "$d" -c user.name="Devin" -c user.email="158243242+devin-ai-integration[bot]@users.noreply.github.com" commit -q -m "chore: codeowners for policy paths (workflows/, infra/) -> @9aia/trusted-contributors"
  git -C "$d" push -q origin HEAD 2>&1 | head -2 && echo "PUSHED $r" || echo "PUSH-FAIL $r"
done
