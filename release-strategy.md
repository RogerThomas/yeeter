# Release Strategy

`yeetr` releases run entirely in CI. Nothing mutating happens on a developer
machine — a single dispatchable GitHub Actions workflow bumps the version,
tags, publishes to PyPI, and deploys the docs. The GitHub repository is
`RogerThomas/yeetr`, the published PyPI distribution is `yeetr`, and the
import package remains `yeetr`.

## Overview

1. Run `task release` (or dispatch the **release** workflow from the Actions tab).
   `task release` only calls `gh workflow run release.yml` — it performs no
   local git operations.
2. The `release` workflow, on a GitHub runner:
   - computes the next CalVer version (or uses the `version` input),
   - bumps `pyproject.toml`, updates `uv.lock`, commits, and pushes `main`,
   - creates the matching GitHub Release (and tag),
   - verifies the resolved version, builds, and publishes to PyPI via Trusted
     Publishing (OIDC), and
   - builds and deploys the documentation to GitHub Pages.

To release a specific version instead of the auto-computed one:

```bash
task release -- 2026.5.21.post1
```

## Publishing to PyPI (Trusted Publishing / OIDC)

There is no PyPI API token to store or rotate. PyPI is configured to trust
the `release` workflow directly:

- **PyPI Trusted Publisher** — configured on the `yeetr` project with owner
  `RogerThomas`, repository `yeetr`, workflow **`release.yml`**, and
  environment `pypi`.
- **GitHub environment** — an environment named `pypi` gates the publish job.

At publish time the workflow requests a short-lived OIDC token
(`id-token: write`), exchanges it for a temporary PyPI upload token, and
publishes. Nothing long-lived is stored.

## Workflow split

- `release.yml` (`workflow_dispatch`) cuts the release and publishes + deploys.
- `main.yml` runs on normal PRs.

## Operational requirements

- Repository Actions settings must allow GitHub Actions to create and approve
  deployments, and to push to `main` (the `release` job pushes the version-bump
  commit; `main`'s branch protection must permit the `github-actions` bot to
  push, or the release job will fail at that step).
- A PyPI Trusted Publisher and a GitHub `pypi` environment must be configured
  (see above).

## Expected release path

- `task release`
- wait for the `release` workflow to bump, publish to PyPI, and deploy docs
