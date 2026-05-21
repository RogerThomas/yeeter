"""CLI entry point for running callables from Python files."""

import importlib.util
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from ._runner import run

if TYPE_CHECKING:
    import types


def _load_module(path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        sys.stderr.write(f"yeet: cannot load {path}\n")
        sys.exit(2)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    except Exception:
        with suppress(KeyError):
            del sys.modules[spec.name]
        raise
    finally:
        del sys.path[0]
    return module


def main(argv: list[str] | None = None) -> None:
    """Run the ``yeet`` command-line interface."""
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw or raw[0] in {"-h", "--help"}:
        sys.stdout.write(
            "Usage: yeet FILE [FUNC] [args...]\n"
            "\n"
            "Run a function from a Python file as a CLI.\n"
            "FUNC defaults to `main`. Anything after FILE/FUNC is forwarded\n"
            "to the function's own CLI (try `yeet FILE --help`).\n",
        )
        sys.exit(0 if raw else 2)

    file_arg, *rest = raw
    path = Path(file_arg).resolve()
    if not path.is_file():
        sys.stderr.write(f"yeet: file not found: {path}\n")
        sys.exit(2)

    module = _load_module(path)

    func_name = "main"
    if rest and not rest[0].startswith("-"):
        candidate = rest[0]
        attr = getattr(module, candidate, None)
        if callable(attr):
            func_name = candidate
            rest = rest[1:]

    func = getattr(module, func_name, None)
    if func is None or not callable(func):
        sys.stderr.write(f"yeet: {path.name} has no callable attribute {func_name!r}\n")
        sys.exit(2)

    run(func, argv=rest, prog=path.stem)
