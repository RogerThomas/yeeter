#!yeet
"""Print the next CalVer release version based on the current pyproject version.

Versions are ``YYYY.M.D`` for the first release on a given day, then
``YYYY.M.D.postN`` for subsequent same-day releases.
"""

import datetime as dt
import re
import tomllib
from pathlib import Path

_VERSION_RE = re.compile(
    r"(?P<year>\d{4})\.(?P<month>\d{1,2})\.(?P<day>\d{1,2})(?:\.post(?P<post>\d+))?",
)


def _determine_next_release_version(current_version: str, release_date: dt.date) -> str:
    """Return the next CalVer version for ``release_date`` after ``current_version``."""
    today = f"{release_date.year}.{release_date.month}.{release_date.day}"
    match = _VERSION_RE.fullmatch(current_version)
    if match is None:
        return today

    current_date = dt.date(
        year=int(match["year"]),
        month=int(match["month"]),
        day=int(match["day"]),
    )
    if current_date != release_date:
        return today

    current_post = match["post"]
    if current_post is None:
        return f"{today}.post1"
    return f"{today}.post{int(current_post) + 1}"


def main() -> None:
    """Print the next CalVer version for today's date."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    current_version = pyproject["project"]["version"]
    print(_determine_next_release_version(current_version, dt.datetime.now(tz=dt.UTC).date()))
