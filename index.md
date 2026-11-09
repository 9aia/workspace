---
layout: home
hero:
  name: 9aia workspace
  text: One root for every 9aia repo
  tagline: The org metarepo — config-only, managed by lasius. Clones live in repos/, each an independent repo.
  actions:
    - theme: brand
      text: lasius docs
      link: https://9aia.com/lasius/
    - theme: alt
      text: GitHub
      link: https://github.com/9aia/workspace
features:
  - title: Config-only
    details: lasius.toml is the source of truth — org, private repos, excludes. Everything else is generated.
  - title: 22 repos, one root
    details: repos/ holds independent clones — no submodules, each keeps its own history, branches, and remotes.
  - title: Editor-ready
    details: 9aia.code-workspace is generated on demand — open the whole org as one multi-root workspace.
---

## Quickstart

```bash
cargo install lasius
git clone git@github.com:9aia/workspace.git && cd workspace
lasius init        # clones all org repos + generates the workspace file
lasius open        # open in your editor
```

Day to day: `lasius update` pulls everywhere, `lasius status` shows the
matrix, `lasius doctor` checks drift. See the
[lasius documentation](https://9aia.com/lasius/) for the full command
reference.
