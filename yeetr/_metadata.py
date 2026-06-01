"""Public metadata objects used to describe CLI parameters."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Arg:
    """CLI metadata attached to a positional parameter via ``Annotated``.

    Usage::

        from typing import Annotated
        from yeetr import Arg

        def main(path: Annotated[Path, Arg(help="Input file")]) -> None: ...

    For variadic positional parameters (``*args``), ``min=1`` requires at
    least one value (argparse ``nargs="+"``); the default ``min=0`` accepts
    zero or more (``nargs="*"``).

    Path validators (``exists``, ``file_okay``, ``dir_okay``, ``readable``,
    ``writable``) apply only when the parameter's effective type is ``Path``
    (or ``list[Path]`` / variadic ``*paths: Path``). Setting any of these on
    a non-``Path`` parameter raises ``YeetrError`` at parser-build time.
    """

    help: str | None = None
    metavar: str | None = None
    min: int = 0
    exists: bool = False
    file_okay: bool = True
    dir_okay: bool = True
    readable: bool = False
    writable: bool = False


@dataclass(frozen=True, slots=True)
class Opt:
    """CLI metadata attached to a keyword-only parameter via ``Annotated``.

    Usage::

        from typing import Annotated
        from yeetr import Opt

        def main(*, workers: Annotated[int, Opt(alias="w", help="Workers")] = 4) -> None: ...

    This is the only Pyright-strict-clean way to attach per-parameter CLI
    metadata in Python's type system: calls are only permitted inside the
    metadata slot of ``Annotated``.

    ``alias`` and ``aliases`` accept either shorthand (``"w"`` / ``"who"``)
    or explicit CLI spelling (``"-w"`` / ``"--who"``).

    ``envvar`` provides a fallback value from the environment when the flag
    is not given on the command line. Precedence: explicit CLI > env var >
    default. For ``list[T]`` opts, the env var is split on ``os.pathsep``.
    For ``bool`` opts, ``1/0/true/false/yes/no`` (case-insensitive) are
    accepted.

    ``hidden=True`` hides the option from the Rich help table and usage
    line; it remains fully functional on the command line.

    Path validators (``exists``, ``file_okay``, ``dir_okay``, ``readable``,
    ``writable``) apply only when the parameter's effective type is ``Path``
    (or ``list[Path]``).
    """

    alias: str | None = None
    aliases: tuple[str, ...] = ()
    help: str | None = None
    metavar: str | None = None
    envvar: str | None = None
    hidden: bool = False
    exists: bool = False
    file_okay: bool = True
    dir_okay: bool = True
    readable: bool = False
    writable: bool = False
