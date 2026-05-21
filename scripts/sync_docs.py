"""Synchronize the docs home page and assets from the README."""

from __future__ import annotations

import shutil
from pathlib import Path


def _copy_asset(name: str, source_dir: Path, target_dir: Path) -> None:
    source_path = source_dir / name
    target_path = target_dir / name
    shutil.copyfile(source_path, target_path)


def main() -> int:
    """Copy the README and branding assets into the docs tree."""
    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = repo_root / "docs"
    docs_assets_dir = docs_dir / "assets"
    docs_assets_dir.mkdir(parents=True, exist_ok=True)

    readme_path = repo_root / "README.md"
    docs_index_path = docs_dir / "index.md"
    docs_index_path.write_text(readme_path.read_text())

    assets_dir = repo_root / "assets"
    _copy_asset("yeeter-logo.svg", assets_dir, docs_assets_dir)
    _copy_asset("yeeter-mark.svg", assets_dir, docs_assets_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
