"""yeeter: a tiny, typed, signature-driven CLI runner.

Just yeet the function::

    def main(thing: int, *, n: float = 0.1) -> None:
        print(thing, n)

    if __name__ == "__main__":
        import yeeter
        yeeter.run(main)

Also supports calling the module directly::

        yeeter(main)
"""

import sys
from types import ModuleType
from typing import TYPE_CHECKING, Any

from ._metadata import Param
from ._runner import YeeterError, run

__all__ = ["Param", "YeeterError", "run"]


class _CallableModule(ModuleType):
    """Module subclass that makes ``yeeter(main)`` work."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return run(*args, **kwargs)


if not TYPE_CHECKING:
    sys.modules[__name__].__class__ = _CallableModule
