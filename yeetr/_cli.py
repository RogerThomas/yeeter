"""CLI entry point for running callables from Python files."""

import importlib.util
import stat
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.text import Text

from ._runner import run

if TYPE_CHECKING:
    import types


def _logo_text(style: str) -> Text:
    text = Text(style=style)
    text.append("                  _        \n")
    text.append("  _   _  ___  ___| |_ _ __ \n")
    text.append(" | | | |/ _ \\/ _ \\ __| '__|\n")
    text.append(" | |_| |  __/  __/ |_| |   \n")
    text.append("  \\__, |\\___|\\___|\\__|_|   \n")
    text.append("  |___/                    ")
    return text


def _print_error(message: str) -> None:
    console = Console(file=sys.stderr, soft_wrap=True)
    console.print(_logo_text("bold red"))
    console.print(Text(message, style="red"))


def _print_status(message: str) -> None:
    console = Console(file=sys.stdout, soft_wrap=True)
    console.print(_logo_text("bold green"))
    console.print(Text(message, style="green"))


def _script_template() -> str:
    return (
        "#!yeet\n"
        "import logging\n"
        "\n"
        'logger = logging.getLogger("Main")\n'
        "\n"
        "\n"
        "def main() -> None:\n"
        '    logger.info("Hello from yeetr")\n'
    )


def _create_script(path: Path) -> None:
    if path.suffix != ".py":
        _print_error(f"file not found: {path}")
        sys.exit(2)
    if not path.parent.exists():
        _print_error(f"parent directory not found: {path.parent}")
        sys.exit(2)
    try:
        path.write_text(_script_template())
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IXUSR)
    except OSError as exc:
        _print_error(f"could not create {path}: {exc}")
        sys.exit(2)
    _print_status(f"created {path}")


def _load_module(path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        _print_error(f"cannot load {path}")
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
        _create_script(path)
        return

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
        _print_error(f"{path.name} has no callable attribute {func_name!r}")
        sys.exit(2)

    run(func, argv=rest, prog=path.stem)
