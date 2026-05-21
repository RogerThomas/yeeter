# Release Strategy

`yeeter` uses a PR-based release flow. A small local script creates the release branch and PR, and GitHub Actions tags the merged commit and publishes the release.

## Overview

1. Run `task release`.
2. A bash script creates `release/{TAG}`, bumps `pyproject.toml`, runs `task deps-lock`, commits the changes, pushes the branch, and opens the PR.
3. Merge the release PR into `main`.
4. GitHub Actions tags the merge commit and creates the GitHub Release.
5. Publishing the GitHub Release triggers the same workflow again on the `release` event, which publishes to PyPI and deploys docs.

## Why this exists

`main` can stay branch-protected. The release branch is the review gate, and GitHub Actions only needs permission to tag the merged commit and create the release.

## Workflow split

- `scripts/release.sh` creates the release branch and PR.
- `release.yml` handles tagging the merged release PR and creating the GitHub Release.
- `release.yml` also handles PyPI publishing and docs deployment when the GitHub Release is published.
- `main.yml` still runs on normal PRs.

## Operational requirements

- Repository Actions settings must allow GitHub Actions to create tags and releases.
- `task release-version` still exists for manually computing the next CalVer when needed.
- Normal PRs that touch `pyproject.toml` or `uv.lock` do not become releases.

## Expected release path

- `task release`
- wait for the release PR to merge
- wait for GitHub Actions to tag the merge commit and create the release
- wait for the published release job to publish to PyPI and deploy docs
