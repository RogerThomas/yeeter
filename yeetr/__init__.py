"""yeetr: a tiny, typed, signature-driven CLI runner.

Just yeet the function::

    def main(thing: int, *, n: float = 0.1) -> None:
        print(thing, n)

    if __name__ == "__main__":
        import yeetr
        yeetr.run(main)
"""

from ._metadata import Arg, Opt
from ._runner import YeetrError, run

__all__ = ["Arg", "Opt", "YeetrError", "run"]
