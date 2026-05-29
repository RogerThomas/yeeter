"""Tests for yeetr's signature-driven CLI runner."""

# pylint: disable=import-outside-toplevel,missing-function-docstring,redefined-builtin

import asyncio
import enum
import logging
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

import pytest
from rich.logging import RichHandler

import yeetr
from yeetr import Arg, Opt, YeetrError

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _reset_root_logger() -> Iterator[None]:  # pyright: ignore[reportUnusedFunction]
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    yield
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in saved_handlers:
        root.addHandler(handler)
    root.setLevel(saved_level)


def test_positional_and_keyword_default() -> None:
    captured: dict[str, object] = {}

    def main(thing: int, *, n: float = 0.1) -> None:
        captured["thing"] = thing
        captured["n"] = n

    yeetr.run(main, argv=["5", "--n", "0.2"])
    assert captured == {"thing": 5, "n": 0.2}


def test_default_used_when_omitted() -> None:
    captured: dict[str, object] = {}

    def main(thing: int, *, n: float = 0.1) -> None:
        captured["thing"] = thing
        captured["n"] = n

    yeetr.run(main, argv=["5"])
    assert captured == {"thing": 5, "n": 0.1}


def test_required_option() -> None:
    def main(*, n: float) -> None:
        del n

    with pytest.raises(SystemExit):
        yeetr.run(main, argv=[])


def test_bool_false_default_flag() -> None:
    captured: dict[str, object] = {}

    def main(*, loud: bool = False) -> None:
        captured["loud"] = loud

    yeetr.run(main, argv=["--loud"])
    assert captured == {"loud": True}

    yeetr.run(main, argv=[])
    assert captured == {"loud": False}


def test_bool_true_default_uses_no_flag() -> None:
    captured: dict[str, object] = {}

    def main(*, loud: bool = True) -> None:
        captured["loud"] = loud

    yeetr.run(main, argv=["--no-loud"])
    assert captured == {"loud": False}

    yeetr.run(main, argv=[])
    assert captured == {"loud": True}


def test_required_bool_rejected() -> None:
    def main(*, flag: bool) -> None:
        del flag

    with pytest.raises(YeetrError):
        yeetr.run(main, argv=[])


def test_path_parsing() -> None:
    captured: dict[str, object] = {}

    def main(path: Path, *, output: Path | None = None) -> None:
        captured["path"] = path
        captured["output"] = output

    yeetr.run(main, argv=["input.pdf", "--output", "out.txt"])
    assert captured == {"path": Path("input.pdf"), "output": Path("out.txt")}


def test_optional_default_none() -> None:
    captured: dict[str, object] = {}

    def main(*, output: Path | None = None) -> None:
        captured["output"] = output

    yeetr.run(main, argv=[])
    assert captured == {"output": None}


def test_literal_choices() -> None:
    captured: dict[str, object] = {}

    def main(*, format: Literal["json", "csv"] = "json") -> None:
        captured["format"] = format

    yeetr.run(main, argv=["--format", "csv"])
    assert captured == {"format": "csv"}


def test_literal_rejects_bad_choice() -> None:
    def main(*, format: Literal["json", "csv"] = "json") -> None:
        del format

    with pytest.raises(SystemExit):
        yeetr.run(main, argv=["--format", "xml"])


class _Format(enum.StrEnum):
    JSON = "json"
    CSV = "csv"


class _Level(enum.IntEnum):
    LOW = 1
    HIGH = 2


def test_enum_option() -> None:
    captured: dict[str, object] = {}

    def main(*, format: _Format = _Format.JSON) -> None:
        captured["format"] = format

    yeetr.run(main, argv=["--format", "csv"])
    assert captured == {"format": _Format.CSV}


def test_enum_positional() -> None:
    captured: dict[str, object] = {}

    def main(level: _Level) -> None:
        captured["level"] = level

    yeetr.run(main, argv=["2"])
    assert captured == {"level": _Level.HIGH}


def test_enum_rejects_bad_choice() -> None:
    def main(*, format: _Format = _Format.JSON) -> None:
        del format

    with pytest.raises(SystemExit):
        yeetr.run(main, argv=["--format", "xml"])


def test_enum_help_shows_choices() -> None:
    from io import StringIO

    from rich.console import Console

    from yeetr._runner import _build_parser  # pyright: ignore[reportPrivateUsage]

    def main(*, format: _Format = _Format.JSON) -> None:
        del format

    parser, _, _ = _build_parser(main, prog="app")
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=200)
    parser.print_help(file=console.file)
    output = buf.getvalue()
    assert "json" in output
    assert "csv" in output


def test_tuple_positional_fixed_width() -> None:
    captured: dict[str, object] = {}

    def main(point: tuple[int, float]) -> None:
        captured["point"] = point

    yeetr.run(main, argv=["1", "2.5"])
    assert captured == {"point": (1, 2.5)}


def test_tuple_option_fixed_width() -> None:
    captured: dict[str, object] = {}

    def main(*, point: tuple[int, float]) -> None:
        captured["point"] = point

    yeetr.run(main, argv=["--point", "1", "2.5"])
    assert captured == {"point": (1, 2.5)}


def test_tuple_option_variable_width() -> None:
    captured: dict[str, object] = {}

    def main(*, values: tuple[int, ...] = ()) -> None:
        captured["values"] = values

    yeetr.run(main, argv=["--values", "1", "2", "3"])
    assert captured == {"values": (1, 2, 3)}


def test_tuple_rejects_bad_value() -> None:
    def main(point: tuple[int, float]) -> None:
        del point

    with pytest.raises(SystemExit):
        yeetr.run(main, argv=["1", "bad"])


def test_envvar_enum(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def main(*, format: Annotated[_Format, Opt(envvar="FMT")] = _Format.JSON) -> None:
        captured["format"] = format

    monkeypatch.setenv("FMT", "csv")
    yeetr.run(main, argv=[])
    assert captured == {"format": _Format.CSV}


def test_envvar_tuple_splits_on_pathsep(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    captured: dict[str, object] = {}

    def main(*, point: Annotated[tuple[int, float], Opt(envvar="POINT")] = (0, 0.0)) -> None:
        captured["point"] = point

    monkeypatch.setenv("POINT", f"1{os.pathsep}2.5")
    yeetr.run(main, argv=[])
    assert captured == {"point": (1, 2.5)}


def test_async_main() -> None:
    captured: dict[str, object] = {}

    async def main(name: str, *, loud: bool = False) -> str:
        await asyncio.sleep(0)
        captured["name"] = name
        captured["loud"] = loud
        return name.upper() if loud else name

    result = yeetr.run(main, argv=["Roger", "--loud"])
    assert captured == {"name": "Roger", "loud": True}
    assert result == "ROGER"


def test_kebab_case_conversion() -> None:
    captured: dict[str, object] = {}

    def main(input_file: Path, *, dry_run: bool = False, max_items: int = 10) -> None:
        captured["input_file"] = input_file
        captured["dry_run"] = dry_run
        captured["max_items"] = max_items

    yeetr.run(main, argv=["./file.pdf", "--dry-run", "--max-items", "20"])
    assert captured == {"input_file": Path("./file.pdf"), "dry_run": True, "max_items": 20}


def test_list_repeated_options() -> None:
    captured: dict[str, object] = {}

    def main(*, tag: list[str] | None = None) -> None:
        if tag is None:
            tag = []
        captured["tag"] = tag

    yeetr.run(main, argv=["--tag", "a", "--tag", "b"])
    assert captured == {"tag": ["a", "b"]}


def test_opt_alias_and_help() -> None:
    captured: dict[str, object] = {}

    def main(*, workers: Annotated[int, Opt(alias="-w", help="Worker count")] = 4) -> None:
        captured["workers"] = workers

    yeetr.run(main, argv=["-w", "8"])
    assert captured == {"workers": 8}

    yeetr.run(main, argv=["--workers", "3"])
    assert captured == {"workers": 3}


def test_opt_no_default_required() -> None:
    captured: dict[str, object] = {}

    def main(*, workers: Annotated[int, Opt(alias="-w", help="Worker count")]) -> None:
        captured["workers"] = workers

    yeetr.run(main, argv=["-w", "8"])
    assert captured == {"workers": 8}

    with pytest.raises(SystemExit):
        yeetr.run(main, argv=[])


def test_arg_on_positional() -> None:
    captured: dict[str, object] = {}

    def main(path: Annotated[Path, Arg(help="Input file")]) -> None:
        captured["path"] = path

    yeetr.run(main, argv=["x.txt"])
    assert captured == {"path": Path("x.txt")}


def test_opt_on_positional_raises() -> None:
    def main(path: Annotated[Path, Opt(alias="-p")]) -> None:
        del path

    with pytest.raises(YeetrError, match="Arg"):
        yeetr.run(main, argv=["x.txt"])


def test_arg_on_keyword_only_raises() -> None:
    def main(*, workers: Annotated[int, Arg(help="nope")] = 4) -> None:
        del workers

    with pytest.raises(YeetrError, match="Opt"):
        yeetr.run(main, argv=[])


def test_missing_annotation_errors() -> None:
    def main(
        thing,  # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]
    ) -> None:
        del thing

    with pytest.raises(YeetrError):
        yeetr.run(main, argv=["5"])  # pyright: ignore[reportUnknownArgumentType]


def test_returns_function_result() -> None:
    def main(thing: int) -> int:
        return thing * 2

    assert yeetr.run(main, argv=["5"]) == 10


type _Workers = Annotated[int, Opt(alias="-w", help="Worker count")]
type _Count = int
type _MaybeInt = int | None
type _AliasChain = _Workers


def test_type_alias_annotated_param() -> None:
    captured: dict[str, object] = {}

    def main(*, workers: _Workers = 4) -> None:
        captured["workers"] = workers

    yeetr.run(main, argv=["-w", "8"])
    assert captured == {"workers": 8}

    yeetr.run(main, argv=["--workers", "3"])
    assert captured == {"workers": 3}

    yeetr.run(main, argv=[])
    assert captured == {"workers": 4}


def test_type_alias_bare_type() -> None:
    captured: dict[str, object] = {}

    def main(count: _Count) -> None:
        captured["count"] = count

    yeetr.run(main, argv=["7"])
    assert captured == {"count": 7}


def test_type_alias_in_optional() -> None:
    captured: dict[str, object] = {}

    def main(*, value: _MaybeInt = None) -> None:
        captured["value"] = value

    yeetr.run(main, argv=["--value", "5"])
    assert captured == {"value": 5}

    yeetr.run(main, argv=[])
    assert captured == {"value": None}


def test_type_alias_transitive() -> None:
    captured: dict[str, object] = {}

    def main(*, workers: _AliasChain = 4) -> None:
        captured["workers"] = workers

    yeetr.run(main, argv=["-w", "8"])
    assert captured == {"workers": 8}


def test_type_alias_help_renders_inner_type() -> None:
    from io import StringIO

    from rich.console import Console

    from yeetr._runner import _build_parser  # pyright: ignore[reportPrivateUsage]

    def main(*, workers: _Workers = 4) -> None:
        del workers

    parser, _, _ = _build_parser(main, prog="app")
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=200)
    parser.print_help(file=console.file)
    output = buf.getvalue()
    assert "int" in output
    assert "Workers" not in output
    assert "-w" in output
    assert "Worker count" in output


def test_type_alias_outer_opt_overrides() -> None:
    captured: dict[str, object] = {}

    def main(
        *,
        workers: Annotated[_Workers, Opt(alias="-x", help="Override")] = 4,
    ) -> None:
        captured["workers"] = workers

    yeetr.run(main, argv=["-x", "9"])
    assert captured == {"workers": 9}

    yeetr.run(main, argv=["--workers", "2"])
    assert captured == {"workers": 2}


def test_var_positional_zero_or_more() -> None:
    captured: dict[str, object] = {}

    def main(dst: Path, *sources: Path) -> None:
        captured["dst"] = dst
        captured["sources"] = sources

    yeetr.run(main, argv=["dst", "a", "b", "c"])
    assert captured == {"dst": Path("dst"), "sources": (Path("a"), Path("b"), Path("c"))}


def test_var_positional_empty_is_tuple() -> None:
    captured: dict[str, object] = {}

    def main(dst: Path, *sources: Path) -> None:
        captured["dst"] = dst
        captured["sources"] = sources

    yeetr.run(main, argv=["dst"])
    assert captured == {"dst": Path("dst"), "sources": ()}


def test_var_positional_with_arg_metadata() -> None:
    captured: dict[str, object] = {}

    def main(*sources: Annotated[Path, Arg(help="Source paths", metavar="SRC")]) -> None:
        captured["sources"] = sources

    yeetr.run(main, argv=["a", "b"])
    assert captured == {"sources": (Path("a"), Path("b"))}


def test_var_positional_min_one_required() -> None:
    def main(*sources: Annotated[Path, Arg(min=1)]) -> None:
        del sources

    with pytest.raises(SystemExit):
        yeetr.run(main, argv=[])


def test_var_positional_min_one_accepts_values() -> None:
    captured: dict[str, object] = {}

    def main(*sources: Annotated[Path, Arg(min=1)]) -> None:
        captured["sources"] = sources

    yeetr.run(main, argv=["a"])
    assert captured == {"sources": (Path("a"),)}


def test_var_positional_with_keyword_only() -> None:
    captured: dict[str, object] = {}

    def main(*sources: str, loud: bool = False) -> None:
        captured["sources"] = sources
        captured["loud"] = loud

    yeetr.run(main, argv=["a", "b", "--loud"])
    assert captured == {"sources": ("a", "b"), "loud": True}


def test_var_positional_list_annotation_rejected() -> None:
    def main(*sources: list[Path]) -> None:
        del sources

    with pytest.raises(YeetrError, match="list"):
        yeetr.run(main, argv=["a"])


def test_var_positional_opt_metadata_rejected() -> None:
    def main(*sources: Annotated[Path, Opt(alias="-s")]) -> None:
        del sources

    with pytest.raises(YeetrError, match="Arg"):
        yeetr.run(main, argv=["a"])


def test_var_keyword_still_rejected() -> None:
    def main(**opts: str) -> None:
        del opts

    with pytest.raises(YeetrError):
        yeetr.run(main, argv=[])


def test_specific_signature_from_spec() -> None:
    captured: dict[str, object] = {}

    def main(thing: int, *, n: float = 0.1) -> None:
        captured["thing"] = thing
        captured["n"] = n

    yeetr.run(main, argv=["5", "--n", "0.2"])
    assert captured == {"thing": 5, "n": 0.2}


def _clear_root_handlers() -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)


def test_logging_setup_on_by_default_no_log_level_param() -> None:
    def main(thing: int) -> None:
        del thing

    _clear_root_handlers()
    yeetr.run(main, argv=["5"])
    handlers = logging.getLogger().handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], RichHandler)
    assert logging.getLogger().level == logging.INFO


def test_logging_setup_honours_log_level_param() -> None:
    def main(*, log_level: Literal["debug", "info", "warning", "error"] = "info") -> None:
        del log_level

    _clear_root_handlers()
    yeetr.run(main, argv=["--log-level", "debug"])
    assert logging.getLogger().level == logging.DEBUG


def test_logging_setup_disabled_by_flag() -> None:
    def main(thing: int) -> None:
        del thing

    _clear_root_handlers()
    before = list(logging.getLogger().handlers)
    yeetr.run(main, argv=["5"], should_setup_logging=False)
    after = list(logging.getLogger().handlers)
    assert before == after


def test_logging_setup_is_idempotent() -> None:
    def main(thing: int) -> None:
        del thing

    _clear_root_handlers()
    yeetr.run(main, argv=["5"])
    handler_count_after_first = len(logging.getLogger().handlers)
    yeetr.run(main, argv=["6"])
    assert len(logging.getLogger().handlers) == handler_count_after_first


def test_envvar_fallback_used_when_flag_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def main(*, workers: Annotated[int, Opt(envvar="WORKERS")] = 4) -> None:
        captured["workers"] = workers

    monkeypatch.setenv("WORKERS", "8")
    yeetr.run(main, argv=[])
    assert captured == {"workers": 8}


def test_envvar_cli_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def main(*, workers: Annotated[int, Opt(envvar="WORKERS")] = 4) -> None:
        captured["workers"] = workers

    monkeypatch.setenv("WORKERS", "8")
    yeetr.run(main, argv=["--workers", "16"])
    assert captured == {"workers": 16}


def test_envvar_default_used_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def main(*, workers: Annotated[int, Opt(envvar="WORKERS")] = 4) -> None:
        captured["workers"] = workers

    monkeypatch.delenv("WORKERS", raising=False)
    yeetr.run(main, argv=[])
    assert captured == {"workers": 4}


def test_envvar_bool_accepts_truthy_strings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def main(*, loud: Annotated[bool, Opt(envvar="LOUD")] = False) -> None:
        captured["loud"] = loud

    for value in ("1", "true", "yes", "TRUE"):
        monkeypatch.setenv("LOUD", value)
        yeetr.run(main, argv=[])
        assert captured == {"loud": True}, value


def test_envvar_bool_accepts_falsy_strings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def main(*, loud: Annotated[bool, Opt(envvar="LOUD")] = True) -> None:
        captured["loud"] = loud

    for value in ("0", "false", "no", "FALSE"):
        monkeypatch.setenv("LOUD", value)
        yeetr.run(main, argv=[])
        assert captured == {"loud": False}, value


def test_envvar_literal_validates_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    def main(*, format: Annotated[Literal["json", "csv"], Opt(envvar="FMT")] = "json") -> None:
        del format

    monkeypatch.setenv("FMT", "xml")
    with pytest.raises(SystemExit):
        yeetr.run(main, argv=[])


def test_envvar_list_splits_on_pathsep(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    captured: dict[str, object] = {}

    def main(*, tag: Annotated[list[str] | None, Opt(envvar="TAGS")] = None) -> None:
        if tag is None:
            tag = []
        captured["tag"] = tag

    monkeypatch.setenv("TAGS", f"a{os.pathsep}b{os.pathsep}c")
    yeetr.run(main, argv=[])
    assert captured == {"tag": ["a", "b", "c"]}


def test_envvar_required_without_default_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def main(*, workers: Annotated[int, Opt(envvar="WORKERS")]) -> None:
        del workers

    monkeypatch.delenv("WORKERS", raising=False)
    with pytest.raises(YeetrError):
        yeetr.run(main, argv=[])


def test_envvar_required_satisfied_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def main(*, workers: Annotated[int, Opt(envvar="WORKERS")]) -> None:
        captured["workers"] = workers

    monkeypatch.setenv("WORKERS", "12")
    yeetr.run(main, argv=[])
    assert captured == {"workers": 12}


def test_envvar_shown_in_help() -> None:
    from io import StringIO

    from rich.console import Console

    from yeetr._runner import _build_parser  # pyright: ignore[reportPrivateUsage]

    def main(*, workers: Annotated[int, Opt(envvar="WORKERS")] = 4) -> None:
        del workers

    parser, _, _ = _build_parser(main, prog="app")
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=200)
    parser.print_help(file=console.file)
    output = buf.getvalue()
    assert "WORKERS" in output


def test_hidden_option_parses() -> None:
    captured: dict[str, object] = {}

    def main(*, debug: Annotated[bool, Opt(hidden=True)] = False) -> None:
        captured["debug"] = debug

    yeetr.run(main, argv=["--debug"])
    assert captured == {"debug": True}


def test_hidden_option_absent_from_help() -> None:
    from io import StringIO

    from rich.console import Console

    from yeetr._runner import _build_parser  # pyright: ignore[reportPrivateUsage]

    def main(*, debug: Annotated[bool, Opt(hidden=True)] = False, workers: int = 4) -> None:
        del debug, workers

    parser, _, _ = _build_parser(main, prog="app")
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=200)
    parser.print_help(file=console.file)
    output = buf.getvalue()
    assert "--debug" not in output
    assert "--workers" in output


def test_path_exists_rejects_missing(tmp_path: Path) -> None:
    def main(path: Annotated[Path, Arg(exists=True)]) -> None:
        del path

    missing = tmp_path / "missing"
    with pytest.raises(SystemExit):
        yeetr.run(main, argv=[str(missing)])


def test_path_exists_accepts_existing(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def main(path: Annotated[Path, Arg(exists=True)]) -> None:
        captured["path"] = path

    existing = tmp_path / "file"
    existing.write_text("x")
    yeetr.run(main, argv=[str(existing)])
    assert captured == {"path": existing}


def test_path_file_okay_false_rejects_file(tmp_path: Path) -> None:
    def main(path: Annotated[Path, Arg(file_okay=False)]) -> None:
        del path

    file = tmp_path / "file"
    file.write_text("x")
    with pytest.raises(SystemExit):
        yeetr.run(main, argv=[str(file)])


def test_path_dir_okay_false_rejects_dir(tmp_path: Path) -> None:
    def main(path: Annotated[Path, Arg(dir_okay=False)]) -> None:
        del path

    with pytest.raises(SystemExit):
        yeetr.run(main, argv=[str(tmp_path)])


def test_path_readable_rejects_unreadable(tmp_path: Path) -> None:
    import os

    def main(path: Annotated[Path, Arg(readable=True)]) -> None:
        del path

    file = tmp_path / "file"
    file.write_text("x")
    file.chmod(0o000)
    try:
        if os.access(file, os.R_OK):
            pytest.skip("running as root; cannot test unreadable file")
        with pytest.raises(SystemExit):
            yeetr.run(main, argv=[str(file)])
    finally:
        file.chmod(0o644)


def test_path_writable_rejects_unwritable(tmp_path: Path) -> None:
    import os

    def main(path: Annotated[Path, Arg(writable=True)]) -> None:
        del path

    file = tmp_path / "file"
    file.write_text("x")
    file.chmod(0o444)
    try:
        if os.access(file, os.W_OK):
            pytest.skip("running as root; cannot test unwritable file")
        with pytest.raises(SystemExit):
            yeetr.run(main, argv=[str(file)])
    finally:
        file.chmod(0o644)


def test_path_checks_on_non_path_raises() -> None:
    def main(value: Annotated[int, Arg(exists=True)]) -> None:
        del value

    with pytest.raises(YeetrError, match="Path"):
        yeetr.run(main, argv=["5"])


def test_path_checks_on_list_path(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def main(*, paths: Annotated[list[Path] | None, Opt(exists=True)] = None) -> None:
        if paths is None:
            paths = []
        captured["paths"] = paths

    file = tmp_path / "file"
    file.write_text("x")
    yeetr.run(main, argv=["--paths", str(file)])
    assert captured == {"paths": [file]}


def test_path_checks_on_var_positional(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def main(*paths: Annotated[Path, Arg(exists=True)]) -> None:
        captured["paths"] = paths

    file = tmp_path / "file"
    file.write_text("x")
    yeetr.run(main, argv=[str(file)])
    assert captured == {"paths": (file,)}


def test_path_checks_on_var_positional_rejects_missing(tmp_path: Path) -> None:
    def main(*paths: Annotated[Path, Arg(exists=True)]) -> None:
        del paths

    missing = tmp_path / "missing"
    with pytest.raises(SystemExit):
        yeetr.run(main, argv=[str(missing)])


def _write_demo(tmp_path: Path) -> Path:
    file = tmp_path / "demo.py"
    file.write_text(
        "def main(thing: int, *, n: float = 0.1) -> None:\n"
        "    print(f'main thing={thing} n={n}')\n"
        "\n"
        "def greet(name: str, *, loud: bool = False) -> None:\n"
        "    msg = f'hello {name}'\n"
        "    print(msg.upper() if loud else msg)\n",
    )
    return file


def test_yeet_cli_defaults_to_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from yeetr._cli import main as yeet_main

    file = _write_demo(tmp_path)
    yeet_main([str(file), "5", "--n", "0.2"])
    out = capsys.readouterr().out
    assert "main thing=5 n=0.2" in out


def test_yeet_cli_explicit_func(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from yeetr._cli import main as yeet_main

    file = _write_demo(tmp_path)
    yeet_main([str(file), "greet", "world", "--loud"])
    out = capsys.readouterr().out
    assert "HELLO WORLD" in out


def test_yeet_cli_missing_python_file_scaffolds(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yeetr._cli import main as yeet_main

    file = tmp_path / "nope.py"
    yeet_main([str(file)])

    out = capsys.readouterr().out
    assert f"created {file.resolve()}" in out
    assert file.read_text() == (
        "#!yeet\n"
        "import logging\n"
        "\n"
        'logger = logging.getLogger("Main")\n'
        "\n"
        "\n"
        "def main() -> None:\n"
        '    logger.info("Hello from yeetr")\n'
    )
    assert file.stat().st_mode & stat.S_IXUSR == stat.S_IXUSR
    assert file.stat().st_mode & stat.S_IXGRP == 0
    assert file.stat().st_mode & stat.S_IXOTH == 0


def test_yeet_cli_missing_non_python_file_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yeetr._cli import main as yeet_main

    with pytest.raises(SystemExit) as exc:
        yeet_main([str(tmp_path / "nope.txt")])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "file not found" in err


def test_yeet_cli_no_args_prints_usage(capsys: pytest.CaptureFixture[str]) -> None:
    from yeetr._cli import main as yeet_main

    with pytest.raises(SystemExit) as exc:
        yeet_main([])
    assert exc.value.code == 2
    out = capsys.readouterr().out
    assert "yeet FILE" in out


def test_yeet_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    from yeetr._cli import main as yeet_main

    with pytest.raises(SystemExit) as exc:
        yeet_main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "yeet FILE" in out


def test_yeet_cli_forwards_help_to_target(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yeetr._cli import main as yeet_main

    file = _write_demo(tmp_path)
    with pytest.raises(SystemExit):
        yeet_main([str(file), "--help"])
    out = capsys.readouterr().out
    assert "THING" in out
    assert "--n" in out


def test_yeet_cli_loads_imports_from_target_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yeetr._cli import main as yeet_main

    package_dir = tmp_path / "project"
    package_dir.mkdir()
    (package_dir / "scraper.py").write_text("VALUE = 'loaded'\n")
    file = package_dir / "demo.py"
    file.write_text(
        "import scraper\n\ndef main() -> None:\n    print(scraper.VALUE)\n",
    )
    monkeypatch.chdir(tmp_path)
    yeet_main([str(file)])
    out = capsys.readouterr().out
    assert "loaded" in out
