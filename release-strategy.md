# Release Strategy

`yeeter` uses a PR-based preparation flow with tag-driven releases. A small local script creates the release branch and PR, and GitHub Actions creates the GitHub Release when a matching CalVer tag is pushed.

## Overview

1. Run `task release`.
2. A bash script creates `release/{TAG}`, bumps `pyproject.toml`, runs `task deps-lock`, commits the changes, pushes the branch, and opens the PR.
3. Merge the release PR into `main`.
4. Create and push the release tag, for example `git tag 2026.5.21.post1 && git push origin 2026.5.21.post1`.
5. GitHub Actions validates the tag, checks that it matches `project.version`, and creates the GitHub Release.
5. The published release triggers a separate workflow that deploys docs.

## Why this exists

`main` can stay branch-protected. The release branch is the review gate, and the pushed tag is the explicit release trigger.

## Workflow split

- `scripts/release.sh` creates the release branch and PR.
- `release.yml` handles pushed CalVer tags and creates the GitHub Release.
- `release-publish.yml` handles docs deployment after the GitHub Release is published.
- `main.yml` still runs on normal PRs.

## Operational requirements

- Repository Actions settings must allow GitHub Actions to create releases.
- A repository secret named `GH_RELEASE_TOKEN` must contain a token with permission to create GitHub Releases.
- Normal PRs that touch `pyproject.toml` or `uv.lock` do not become releases.

## Expected release path

- `task release`
- merge the release PR
- create and push the release tag
- wait for GitHub Actions to create the release
- wait for the published-release workflow to deploy docs
