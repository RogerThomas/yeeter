"""Create a release branch, push it, and open a pull request."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import subprocess
import sys
from pathlib import Path

from git import GitCommandError, Repo

from scripts.release_version import next_release_version, read_current_version


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
    return parser


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, check=True, cwd=cwd)  # noqa: S603


def _run_output(command: list[str], *, cwd: Path) -> str:
    result = subprocess.run(  # noqa: S603
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout.strip()


def main() -> int:
    """Create a release branch, push it, and open the release PR."""

    args = _build_parser().parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    repo = Repo(repo_root)
    pyproject_path = repo_root / "pyproject.toml"

    if repo.is_dirty(untracked_files=True):
        print("Working tree must be clean before creating a release.", file=sys.stderr)
        return 1

    current_version = read_current_version(pyproject_path)
    release_date = args.date or dt.datetime.now(tz=dt.UTC).date()
    target_version = args.version or next_release_version(
        current_version=current_version,
        release_date=release_date,
    )
    branch_name = f"release/{target_version}"

    repo.git.checkout("-B", branch_name)
    _run(["uv", "run", "./scripts/release_version.py", "--version", target_version], cwd=repo_root)

    resolved_version = read_current_version(pyproject_path)
    if resolved_version != target_version:
        raise RuntimeError

    repo.index.add(["pyproject.toml", "uv.lock"])
    if not repo.index.diff("HEAD"):
        print("No version file changes to commit.")
        return 0

    repo.git.config("user.name", "github-actions[bot]")
    repo.git.config("user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    repo.index.commit(f"chore: release {target_version}")

    with contextlib.suppress(GitCommandError):
        repo.remote("origin").fetch(branch_name)

    repo.git.push("--force-with-lease", "--set-upstream", "origin", branch_name)

    title = f"chore: release {target_version}"
    body = f"Automated release version bump for {target_version}."
    existing = _run_output(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch_name,
            "--state",
            "open",
            "--json",
            "number",
            "--jq",
            ".[0].number // empty",
        ],
        cwd=repo_root,
    )
    if existing:
        _run(["gh", "pr", "edit", existing, "--title", title, "--body", body], cwd=repo_root)
        url = _run_output(
            ["gh", "pr", "view", existing, "--json", "url", "--jq", ".url"],
            cwd=repo_root,
        )
    else:
        url = _run_output(
            [
                "gh",
                "pr",
                "create",
                "--base",
                "main",
                "--head",
                branch_name,
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=repo_root,
        )
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
