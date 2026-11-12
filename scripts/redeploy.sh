#!/usr/bin/env bash
# redeploy.sh <repo> [pack] — rebuild a repo's tamias pack payload,
# reinstall it, redeploy its provider services, and restart the
# rendered systemd units. The loop we ran by hand all night:
#
#   cargo xtask pack → tamias install --allow-drivers ./libraries/<pack>
#   → tamias deploy <name>@<version> → systemctl --user restart <units>
#
# Examples:
#   scripts/redeploy.sh peregrin          # pack = repo name
#   scripts/redeploy.sh bupha ci-gate     # pack dir differs from repo
#   scripts/redeploy.sh sepia --no-deploy # engine-only pack, skip deploy
#
# Notes:
# - Run from anywhere; paths resolve against the workspace root.
# - `tamias deploy` regenerates serve/config YAML — hand-applied
#   `config:` blocks are wiped (T-026). Re-apply after deploy.
# - Units restart only when the pack's tamias.yaml declares
#   provider.services; engine packs (bins[] only) skip deploy.
set -euo pipefail

REPO="${1:?usage: redeploy.sh <repo> [pack] [--no-deploy] [--no-restart]}"
shift
PACK="$REPO"
DEPLOY=1
RESTART=1
for arg in "$@"; do
  case "$arg" in
    --no-deploy) DEPLOY=0 ;;
    --no-restart) RESTART=0 ;;
    *) PACK="$arg" ;;
  esac
done

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$WS/repos/$REPO"
LIB="$REPO_DIR/libraries/$PACK"
MANIFEST="$LIB/tamias.yaml"
[ -f "$MANIFEST" ] || { echo "redeploy: no $MANIFEST" >&2; exit 1; }

NAME=$(awk '/^name:/{print $2; exit}' "$MANIFEST" | tr -d '"')
VERSION=$(awk '/^version:/{print $2; exit}' "$MANIFEST" | tr -d '"')
PROVIDER=$(awk '/^  name:/{print $2; exit}' "$MANIFEST" | tr -d '"')

echo "== pack: $REPO/libraries/$PACK ($NAME@$VERSION, provider=${PROVIDER:-none})"

(cd "$REPO_DIR" && cargo xtask pack)
tamias install --allow-drivers "$LIB"

if [ "$DEPLOY" = 1 ] && grep -q '^provider:' "$MANIFEST"; then
  SPEC="$NAME"
  [ -n "$VERSION" ] && SPEC="$NAME@$VERSION"
  echo "== deploy: $SPEC"
  tamias deploy "$SPEC"
fi

if [ "$RESTART" = 1 ] && grep -q '^provider:' "$MANIFEST"; then
  # Unit names render as <provider>-<service> (peregrin-campaign,
  # bupha-worker, …). Only restart units that exist.
  UNITS=$(awk '/^  services:/{f=1;next} f&&/^  [a-z]/{f=0} f&&/- name:/{print $3}' "$MANIFEST" \
    | while read -r svc; do
        for cand in "${PROVIDER:-$NAME}-$svc" "$NAME-$svc" "$svc"; do
          systemctl --user list-unit-files "${cand}.service" --no-legend 2>/dev/null | grep -q . && { echo "$cand"; break; }
        done
      done | sort -u)
  if [ -n "$UNITS" ]; then
    echo "== restart: $UNITS"
    # shellcheck disable=SC2086
    systemctl --user restart $UNITS
    sleep 2
    systemctl --user is-active $UNITS || true
  else
    echo "== restart: no matching units found"
  fi
fi

echo "== done: $NAME@$VERSION"
