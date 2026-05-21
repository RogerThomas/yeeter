"""Release-version helper for CalVer bumps."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


class ProjectVersionError(TypeError):
    """Raised when the project version is missing or invalid."""


@dataclass(slots=True)
class ReleaseVersion:
    """A CalVer release identifier with an optional same-day post suffix."""

    release_date: dt.date
    post: int | None = None

    def format(self) -> str:
        """Return the canonical PEP 440 version string."""
        base = f"{self.release_date.year}.{self.release_date.month}.{self.release_date.day}"
        if self.post is None:
            return base
        return f"{base}.post{self.post}"


def _read_current_version(pyproject_path: Path) -> str:
    pyproject = tomllib.loads(pyproject_path.read_text())
    project = pyproject["project"]
    version = project["version"]
    if not isinstance(version, str):
        raise ProjectVersionError
    return version


def _parse_release_version(version: str) -> ReleaseVersion | None:
    match = re.fullmatch(
        r"(?P<year>\d{4})\.(?P<month>\d{1,2})\.(?P<day>\d{1,2})(?:\.post(?P<post>\d+))?",
        version,
    )
    if match is None:
        return None
    return ReleaseVersion(
        release_date=dt.date(
            year=int(match["year"]),
            month=int(match["month"]),
            day=int(match["day"]),
        ),
        post=int(match["post"]) if match["post"] is not None else None,
    )


def next_release_version(current_version: str, release_date: dt.date) -> str:
    """Compute the next release version for the given release date."""
    current = _parse_release_version(current_version)
    if current is None or current.release_date != release_date:
        return ReleaseVersion(release_date=release_date).format()
    next_post = 1 if current.post is None else current.post + 1
    return ReleaseVersion(release_date=release_date, post=next_post).format()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        default=None,
        help="Explicit version to apply instead of computing the next CalVer.",
    )
    parser.add_argument(
        "--date",
        type=dt.date.fromisoformat,
        default=None,
        help="Release date in ISO format (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the next version without updating pyproject.toml.",
    )
    return parser


def main() -> int:
    """Apply an explicit or computed release version via ``uv version``."""
    args = _build_parser().parse_args()
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if args.version is None:
        current_version = _read_current_version(pyproject_path)
        release_date = args.date or dt.datetime.now(tz=dt.UTC).date()
        next_version = next_release_version(
            current_version=current_version,
            release_date=release_date,
        )
    else:
        next_version = args.version

    command = ["uv", "version", next_version]
    if args.dry_run:
        command.append("--dry-run")

    with contextlib.chdir(pyproject_path.parent):
        return os.spawnvp(os.P_WAIT, "uv", command)


if __name__ == "__main__":
    raise SystemExit(main())
