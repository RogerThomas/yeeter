"""Synchronize the docs home page and assets from the README."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    """Copy the README and branding assets into the docs tree."""
    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = repo_root / "docs"
    docs_assets_dir = docs_dir / "assets"
    docs_assets_dir.mkdir(parents=True, exist_ok=True)

    readme_path = repo_root / "README.md"
    docs_index_path = docs_dir / "index.md"
    docs_index_path.write_text(readme_path.read_text())

    docs_logo_path = docs_assets_dir / "yeeter.png"
    docs_logo_path.write_bytes((repo_root / "assets" / "yeeter.png").read_bytes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
