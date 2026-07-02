#!yeet
"""Print the next CalVer release tag, based on the existing git tags.

Versions are ``YYYY.M.D`` for the first release on a given day, then
``YYYY.M.D.postN`` for subsequent same-day releases. The git tag is the
single source of truth for the version, so the next release is derived from
the tags that already exist rather than from any committed version field.
"""

import datetime as dt
import re
import subprocess

_TAG_RE = re.compile(r"^(\d{4})\.(\d{1,2})\.(\d{1,2})(?:\.post(\d+))?$")


def _existing_tags() -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--list"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()


def _determine_next_release_version(tags: list[str], release_date: dt.date) -> str:
    """Return the next CalVer version for ``release_date`` given existing ``tags``."""
    today = f"{release_date.year}.{release_date.month}.{release_date.day}"
    today_parts = (release_date.year, release_date.month, release_date.day)
    posts: list[int] = []
    base_exists = False
    for tag in tags:
        match = _TAG_RE.match(tag)
        if match is None:
            continue
        year, month, day, post = match.groups()
        if (int(year), int(month), int(day)) != today_parts:
            continue
        if post is None:
            base_exists = True
        else:
            posts.append(int(post))

    if not base_exists and not posts:
        return today
    next_post = max(posts) + 1 if posts else 1
    return f"{today}.post{next_post}"


def main() -> None:
    """Print the next CalVer version for today's date."""
    print(_determine_next_release_version(_existing_tags(), dt.datetime.now(tz=dt.UTC).date()))
