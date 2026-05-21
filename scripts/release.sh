#!/usr/bin/env bash

set -euo pipefail

base_branch="main"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

cd "${repo_root}"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree must be clean before creating a release PR." >&2
  exit 1
fi

if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [VERSION]" >&2
  exit 1
fi

if [[ $# -eq 1 ]]; then
  version="$1"
else
  version="$(uv run python - <<'PY'
import datetime as dt
import tomllib
from pathlib import Path

import re


def next_release_version(current_version: str, release_date: dt.date) -> str:
    match = re.fullmatch(
        r"(?P<year>\d{4})\.(?P<month>\d{1,2})\.(?P<day>\d{1,2})(?:\.post(?P<post>\d+))?",
        current_version,
    )
    if match is None:
        return f"{release_date.year}.{release_date.month}.{release_date.day}"

    current_date = dt.date(
        year=int(match["year"]),
        month=int(match["month"]),
        day=int(match["day"]),
    )
    if current_date != release_date:
        return f"{release_date.year}.{release_date.month}.{release_date.day}"

    current_post = match["post"]
    if current_post is None:
        return f"{release_date.year}.{release_date.month}.{release_date.day}.post1"
    return f"{release_date.year}.{release_date.month}.{release_date.day}.post{int(current_post) + 1}"

pyproject = tomllib.loads(Path("pyproject.toml").read_text())
current_version = pyproject["project"]["version"]
print(next_release_version(current_version, dt.datetime.now(tz=dt.UTC).date()))
PY
)"
fi

branch="release/${version}"

git fetch origin "${base_branch}"
git switch -C "${branch}" "origin/${base_branch}"

uv version "${version}"

task deps-lock

resolved_version="$(uv run python - <<'PY'
import tomllib
from pathlib import Path

pyproject = tomllib.loads(Path("pyproject.toml").read_text())
print(pyproject["project"]["version"])
PY
)"

if [[ "${resolved_version}" != "${version}" ]]; then
  echo "Resolved version ${resolved_version} does not match branch version ${version}." >&2
  exit 1
fi

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

git add pyproject.toml uv.lock

if git diff --cached --quiet; then
  echo "No release changes to commit." >&2
  exit 1
fi

git commit -m "release ${version}"
git push --set-upstream origin "${branch}"

pr_title="chore: release ${version}"
pr_body="Automated release PR for ${version}."

existing_pr="$(gh pr list --head "${branch}" --state open --json number --jq '.[0].number // empty')"
if [[ -n "${existing_pr}" ]]; then
  gh pr edit "${existing_pr}" --title "${pr_title}" --body "${pr_body}"
  gh pr view "${existing_pr}" --json url --jq '.url'
else
  gh pr create \
    --base "${base_branch}" \
    --head "${branch}" \
    --title "${pr_title}" \
    --body "${pr_body}"
fi

git switch "${base_branch}"
