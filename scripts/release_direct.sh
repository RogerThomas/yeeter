#!/usr/bin/env bash

set -euo pipefail

base_branch="main"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

cd "${repo_root}"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree must be clean before creating a direct release." >&2
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
import re
import tomllib
from pathlib import Path


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

git fetch origin "${base_branch}"
git switch "${base_branch}"
git pull --ff-only origin "${base_branch}"

if git rev-parse -q --verify "refs/tags/${version}" >/dev/null; then
  echo "Tag ${version} already exists locally." >&2
  exit 1
fi

if git ls-remote --exit-code --tags origin "refs/tags/${version}" >/dev/null 2>&1; then
  echo "Tag ${version} already exists on origin." >&2
  exit 1
fi

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
  echo "Resolved version ${resolved_version} does not match requested version ${version}." >&2
  exit 1
fi

git add pyproject.toml uv.lock

if git diff --cached --quiet; then
  echo "No release changes to commit." >&2
  exit 1
fi

git commit -m "release ${version}"
git push origin "${base_branch}"
git tag -a "${version}" -m "Release ${version}"
git push origin "${version}"
