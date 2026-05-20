#!uv run
"""Kitchen-sink example for yeeter.

Run a few of these to see the CLI behaviour:

    uv run main.py input.pdf --mode a -o out.pdf
    uv run main.py input.pdf --mode b -o out.pdf --workers 8 --tag x --tag y
    uv run main.py input.pdf --mode a -o out.pdf --no-progress --quiet
    uv run main.py input.pdf --mode a -o out.pdf --threshold 0.9 --note "hello"
    uv run main.py input.pdf --mode a -o out.pdf --log-level debug
    uv run main.py --help
"""

import logging
from pathlib import Path
from typing import Annotated, Literal

from rich.logging import RichHandler

import yeeter
from yeeter import Param

logger = logging.getLogger("main")


type Workers = Annotated[int, Param(alias="-w", help="Worker count")]


async def main(
    # --- positional args (no `*` yet) ---
    pdf_path: Path,
    # Positional with help text via `Annotated`.
    out_dir: Annotated[Path, Param(help="Where to write outputs", metavar="OUT")] = Path("output"),
    *,
    # --- required keyword-only options ---
    # Required option with a Literal -> generates `--mode {a,b,c}`.
    mode: Literal["a", "b", "c"],
    # Required option with an alias.
    output: Annotated[Path, Param(alias="-o", help="Output file path")],
    # --- bool flags ---
    # `bool = False` -> `--dry-run` enables it.
    dry_run: bool = False,
    # `bool = True` -> `--no-progress` disables it.
    progress: bool = True,
    # Bool flag with a short alias.
    quiet: Annotated[bool, Param(alias="-q", help="Suppress chatter")] = False,
    # --- numbers ---
    workers: Workers = 4,
    threshold: float = 0.5,
    # --- strings & optionals ---
    note: str | None = None,
    # --- literals as choices with default ---
    log_level: Literal["debug", "info", "warning", "error"] = "info",
    # --- repeated options -> list[T] ---
    tag: Annotated[list[str], Param(alias="-t", help="Repeatable tag")] = [],  # noqa: B006
    # --- multiple aliases ---
    name: Annotated[str, Param(aliases=("-n", "--who"), help="Who to greet")] = "world",
) -> None:
    """Demo command showing every supported parameter style."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        handlers=[RichHandler(show_time=False, show_level=False)],
    )

    if not quiet:
        logger.info("pdf_path     = %s", pdf_path)
        logger.info("out_dir      = %s", out_dir)
        logger.info("mode         = %s", mode)
        logger.info("output       = %s", output)
        logger.info("dry_run      = %s", dry_run)
        logger.info("progress     = %s", progress)
        logger.info("workers      = %d", workers)
        logger.info("threshold    = %.3f", threshold)
        logger.info("note         = %r", note)
        logger.info("log_level    = %s", log_level)
        logger.info("tag          = %s", tag)
        logger.info("name         = %s", name)


if __name__ == "__main__":
    # Both of these work identically:
    import typer

    # typer.run(main)
    yeeter.run(main)
    # yeeter(main)
