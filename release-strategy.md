# Release Strategy

`yeeter` uses a GitHub Actions-driven release flow that keeps `main` protected and avoids direct bot pushes to the branch.

## Overview

1. Run `task release`.
2. GitHub Actions creates a `release/<version>` branch and pushes it.
3. Open a pull request from that branch into `main`.
4. The release PR runs the normal `main.yml` checks like any other PR.
5. After the PR is merged, a separate workflow tags the merge commit and creates the GitHub Release.
6. The published release triggers the release publish workflow, which publishes to PyPI and deploys docs.

## Why this exists

`main` is branch-protected and requires the `quality` status check. A workflow that tries to push release version bumps directly to `main` will fail under that protection.

The branch-plus-manual-PR flow solves that by making the version bump a normal pull request:

- source changes stay reviewable
- required checks still run before merge
- release automation never bypasses branch protection

## Workflow split

- `release-pr.yml` creates the release branch and bumps `pyproject.toml` and `uv.lock`.
- `main.yml` runs on all normal PRs, including release PRs.
- `release-publish.yml` runs only when a merged PR into `main` came from `release/*`.
- `release-main` runs on the published GitHub Release and handles PyPI publishing plus docs deployment.

## Operational requirements

- Repository Actions settings must allow GitHub Actions to push branches.
- `task release-version` still exists for manually computing the next CalVer when needed.
- Normal PRs that touch `pyproject.toml` or `uv.lock` do not become releases unless they came from a `release/*` branch.

## Expected release path

- `task release`
- open the PR from the pushed `release/*` branch
- merge the release PR
- wait for GitHub Actions to tag and create the release
- wait for the published release workflow to publish to PyPI and deploy docs
