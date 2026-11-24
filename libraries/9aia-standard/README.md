# 9aia-standard

The 9aia org's [mimus](https://github.com/9aia/mimus) `standard`
spec set, distributed as a tamias content pack (`type: files` —
pure payload, no driver).

## Layout

- `tamias.yaml` — pack manifest (`name: 9aia-standard`).
- `specs/` — the spec files, flat: `base.toml` (family `9aia/base`,
  the org floor) plus `<repo>.toml` per org repo. **Generated
  copies** — sources of truth are `workspace/specs/` and
  `repos/<name>/specs/`; regenerate with
  `scripts/sync-spec-pack.py --apply` in the same change as any
  spec edit.

## Consume

```bash
tamias install --plan ./libraries/9aia-standard   # dry-run
tamias install ./libraries/9aia-standard
SPEC_DIR="$(tamias info 9aia-standard --json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["dir"])')/specs"
mimus standard --repo <repo-path> --spec "$SPEC_DIR"
```

`mimus standard --spec` takes a file or a directory of specs and
union-matches them against the repo name — one installed pack
covers the floor and every family spec; `match` globs select.

The pack also installs straight from its repo location or a git
ref — no publish step required:

```bash
tamias install ./libraries/9aia-standard
tamias install git:github.com/9aia/workspace//libraries/9aia-standard
# or publish to the org registry once one is configured:
tamias publish ./libraries/9aia-standard
```

The workspace fleet sweep (`scripts/standard.sh`) keeps using the
sibling paths (`specs/` + `repos/<name>/specs/`) — the pack is for
consumers outside the workspace layout (CI, standalone clones).

## Approval gating

`libraries/9aia-standard/specs/` is covered by `spec-guard.py`
(proposal ref required) and `spec-lock.py` (digest pin) exactly
like `specs/` — editing a pack copy without a live proposal fails
the guard. Bump `version:` in `tamias.yaml` when spec content
changes.
