import asyncio
from pathlib import Path
from typing import Annotated, Literal

import pytest

import yeeter
from yeeter import Param, YeeterError


def test_positional_and_keyword_default() -> None:
    captured: dict[str, object] = {}

    def main(thing: int, *, n: float = 0.1) -> None:
        captured["thing"] = thing
        captured["n"] = n

    yeeter.run(main, argv=["5", "--n", "0.2"])
    assert captured == {"thing": 5, "n": 0.2}


def test_default_used_when_omitted() -> None:
    captured: dict[str, object] = {}

    def main(thing: int, *, n: float = 0.1) -> None:
        captured["thing"] = thing
        captured["n"] = n

    yeeter.run(main, argv=["5"])
    assert captured == {"thing": 5, "n": 0.1}


def test_required_option() -> None:
    def main(*, n: float) -> None:
        del n

    with pytest.raises(SystemExit):
        yeeter.run(main, argv=[])


def test_bool_false_default_flag() -> None:
    captured: dict[str, object] = {}

    def main(*, loud: bool = False) -> None:
        captured["loud"] = loud

    yeeter.run(main, argv=["--loud"])
    assert captured == {"loud": True}

    yeeter.run(main, argv=[])
    assert captured == {"loud": False}


def test_bool_true_default_uses_no_flag() -> None:
    captured: dict[str, object] = {}

    def main(*, loud: bool = True) -> None:
        captured["loud"] = loud

    yeeter.run(main, argv=["--no-loud"])
    assert captured == {"loud": False}

    yeeter.run(main, argv=[])
    assert captured == {"loud": True}


def test_required_bool_rejected() -> None:
    def main(*, flag: bool) -> None:
        del flag

    with pytest.raises(YeeterError):
        yeeter.run(main, argv=[])


def test_path_parsing() -> None:
    captured: dict[str, object] = {}

    def main(path: Path, *, output: Path | None = None) -> None:
        captured["path"] = path
        captured["output"] = output

    yeeter.run(main, argv=["input.pdf", "--output", "out.txt"])
    assert captured == {"path": Path("input.pdf"), "output": Path("out.txt")}


def test_optional_default_none() -> None:
    captured: dict[str, object] = {}

    def main(*, output: Path | None = None) -> None:
        captured["output"] = output

    yeeter.run(main, argv=[])
    assert captured == {"output": None}


def test_literal_choices() -> None:
    captured: dict[str, object] = {}

    def main(*, format: Literal["json", "csv"] = "json") -> None:
        captured["format"] = format

    yeeter.run(main, argv=["--format", "csv"])
    assert captured == {"format": "csv"}


def test_literal_rejects_bad_choice() -> None:
    def main(*, format: Literal["json", "csv"] = "json") -> None:
        del format

    with pytest.raises(SystemExit):
        yeeter.run(main, argv=["--format", "xml"])


def test_async_main() -> None:
    captured: dict[str, object] = {}

    async def main(name: str, *, loud: bool = False) -> str:
        await asyncio.sleep(0)
        captured["name"] = name
        captured["loud"] = loud
        return name.upper() if loud else name

    result = yeeter.run(main, argv=["Roger", "--loud"])
    assert captured == {"name": "Roger", "loud": True}
    assert result == "ROGER"


def test_kebab_case_conversion() -> None:
    captured: dict[str, object] = {}

    def main(input_file: Path, *, dry_run: bool = False, max_items: int = 10) -> None:
        captured["input_file"] = input_file
        captured["dry_run"] = dry_run
        captured["max_items"] = max_items

    yeeter.run(main, argv=["./file.pdf", "--dry-run", "--max-items", "20"])
    assert captured == {"input_file": Path("./file.pdf"), "dry_run": True, "max_items": 20}


def test_list_repeated_options() -> None:
    captured: dict[str, object] = {}

    def main(*, tag: list[str] = []) -> None:
        captured["tag"] = tag

    yeeter.run(main, argv=["--tag", "a", "--tag", "b"])
    assert captured == {"tag": ["a", "b"]}


def test_param_alias_and_help() -> None:
    captured: dict[str, object] = {}

    def main(*, workers: Annotated[int, Param(alias="-w", help="Worker count")] = 4) -> None:
        captured["workers"] = workers

    yeeter.run(main, argv=["-w", "8"])
    assert captured == {"workers": 8}

    yeeter.run(main, argv=["--workers", "3"])
    assert captured == {"workers": 3}


def test_param_no_default_required() -> None:
    captured: dict[str, object] = {}

    def main(*, workers: Annotated[int, Param(alias="-w", help="Worker count")]) -> None:
        captured["workers"] = workers

    yeeter.run(main, argv=["-w", "8"])
    assert captured == {"workers": 8}

    with pytest.raises(SystemExit):
        yeeter.run(main, argv=[])


def test_param_on_positional() -> None:
    captured: dict[str, object] = {}

    def main(path: Annotated[Path, Param(help="Input file")]) -> None:
        captured["path"] = path

    yeeter.run(main, argv=["x.txt"])
    assert captured == {"path": Path("x.txt")}


def test_missing_annotation_errors() -> None:
    def main(thing) -> None:  # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]
        del thing

    with pytest.raises(YeeterError):
        yeeter.run(main, argv=["5"])  # pyright: ignore[reportUnknownArgumentType]


def test_returns_function_result() -> None:
    def main(thing: int) -> int:
        return thing * 2

    assert yeeter.run(main, argv=["5"]) == 10


def test_module_is_callable() -> None:
    captured: dict[str, object] = {}

    def main(thing: int, *, n: float = 0.1) -> None:
        captured["thing"] = thing
        captured["n"] = n

    yeeter(main, argv=["5", "--n", "0.2"])  # pyright: ignore[reportCallIssue]
    assert captured == {"thing": 5, "n": 0.2}


def test_specific_signature_from_spec() -> None:
    captured: dict[str, object] = {}

    def main(thing: int, *, n: float = 0.1) -> None:
        captured["thing"] = thing
        captured["n"] = n

    yeeter.run(main, argv=["5", "--n", "0.2"])
    assert captured == {"thing": 5, "n": 0.2}
