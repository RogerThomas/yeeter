"""yeeter: a tiny, typed, signature-driven CLI runner.

Just yeet the function::

    def main(thing: int, *, n: float = 0.1) -> None:
        print(thing, n)

    if __name__ == "__main__":
        import yeeter
        yeeter.run(main)
"""

from ._metadata import Arg, Opt
from ._runner import YeeterError, run

__all__ = ["Arg", "Opt", "YeeterError", "run"]
