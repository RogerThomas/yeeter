from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Param:
    """CLI metadata attached to a parameter via ``Annotated``.

    Usage::

        from typing import Annotated
        from yeeter import Param

        def main(*, workers: Annotated[int, Param(alias="-w", help="Workers")] = 4) -> None: ...

    This is the only Pyright-strict-clean way to attach per-parameter CLI
    metadata in Python's type system: calls are only permitted inside the
    metadata slot of ``Annotated``.
    """

    alias: str | None = None
    aliases: tuple[str, ...] = ()
    help: str | None = None
    metavar: str | None = None
