#!yeet
"""Example `#!yeet` script that processes a PDF."""

from logging import getLogger
from pathlib import Path
from typing import Annotated, Literal

from yeetr import Arg

logger = getLogger("Tmp")

type PDFPathArg = Annotated[Path, Arg(help="Path to the PDF file")]


def main(
    pdf_path: PDFPathArg = Path("./"),
    *,
    tol: float = 0.002,
    mode: Literal["auto", "text", "vision"] = "auto",
) -> None:
    """Main entrypoint to process the PDF"""
    logger.info("Processing PDF at: %s, tol: %s, mode: %s", pdf_path, tol, mode)
