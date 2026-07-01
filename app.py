#!yeet
"""Example yeetr entry point."""

import logging
from typing import Annotated as Ant
from typing import NamedTuple

from yeetr import Opt

logger = logging.getLogger("Main")


class Args(NamedTuple):
    """CLI arguments for the greeting."""

    name: Ant[str, Opt(alias="n", help="The name of the person to greet")] = "World"
    tolerance: Ant[
        float, Opt(aliases=("t", "tol"), help="The tolerance level for the greeting")
    ] = 0.5


def main(args: Args) -> None:
    """Greet someone."""
    logger.info("Hello from yeetr, args: %s", args)
