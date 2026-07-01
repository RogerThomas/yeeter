#!yeet
"""Example yeetr entry point."""

import logging
from pathlib import Path
from typing import Annotated as Ant
from typing import Literal, NamedTuple

from yeetr import Arg, Opt

logger = logging.getLogger("Main")

type Model = Literal["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]


class Args(NamedTuple):
    """CLI arguments for the greeting."""

    name: Ant[str, Opt(alias="n", help="The name of the person to greet")] = "World"
    tolerance: Ant[
        float, Opt(aliases=("t", "tol"), help="The tolerance level for the greeting")
    ] = 0.5


def main(
    pdf_path: Ant[Path, Arg(help="Path to the PDF file")],
    *,
    model: Ant[Model, Opt(alias="m", help="The LLM model to use for detection")],
    tolerance: Ant[float, Opt(aliases=("t", "tol"), help="The tolerance for detection")] = 0.5,
    verbose: Ant[bool, Opt(alias="v", help="Enable verbose output")] = False,
) -> None:
    """Use an LLM to detect text in a PDF file."""
    logger.info(
        "Using model: %s, pdf-path: %s with tolerance: %s, verbose: %s",
        model,
        pdf_path,
        tolerance,
        verbose,
    )
