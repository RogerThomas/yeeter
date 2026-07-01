#!yeet
"""Build documentation and publish agent-readable Markdown artifacts."""

import importlib
import inspect
import shutil
from collections.abc import Callable
from dataclasses import MISSING, Field, dataclass, fields, is_dataclass
from pathlib import Path
from typing import Annotated, cast

import yeetr
from yeetr import Opt


@dataclass(frozen=True, slots=True)
class _AgentPage:
    title: str
    filename: str
    body: str


def _clean_docstring(value: str | None) -> str:
    if value is None:
        return ""
    return inspect.cleandoc(value)


def _signature_markdown(symbol: object) -> str:
    if not callable(symbol):
        return ""
    try:
        signature = inspect.signature(symbol)
    except (NameError, TypeError, ValueError):
        return ""
    return f"```python\n{signature}\n```"


def _field_markdown(field_info: Field[object]) -> str:
    default = "" if field_info.default is MISSING else f" = {field_info.default!r}"
    return f"- `{field_info.name}: {field_info.type!s}{default}`"


def _symbol_markdown(name: str, symbol: object) -> str:
    lines = [f"## `{name}`", "", _signature_markdown(symbol)]
    docstring = _clean_docstring(getattr(symbol, "__doc__", None))
    if docstring:
        lines.extend(["", docstring])
    if is_dataclass(symbol):
        field_lines = [_field_markdown(field_info) for field_info in fields(symbol)]
        lines.extend(["", "Fields:", "", *field_lines])
    return "\n".join(line for line in lines if line != "")


def _api_markdown() -> str:
    parts = [
        "# API Reference",
        "",
        "Public API exported by `yeetr`.",
        "",
    ]
    for name in yeetr.__all__:
        parts.extend([_symbol_markdown(name, getattr(yeetr, name)), ""])
    return "\n".join(parts).rstrip() + "\n"


def _page_source(root: Path) -> list[_AgentPage]:
    readme = root / "README.md"
    return [
        _AgentPage("Home", "home.md", readme.read_text(encoding="utf-8")),
        _AgentPage("API Reference", "api-reference.md", _api_markdown()),
    ]


def _directory_markdown(pages: list[_AgentPage]) -> str:
    lines = [
        "# yeetr Agent Documentation",
        "",
        "Raw Markdown documentation for agents and other text-first readers.",
        "",
        "- [All documentation](all.md)",
    ]
    lines.extend(f"- [{page.title}]({page.filename})" for page in pages)
    return "\n".join(lines) + "\n"


def _all_markdown(pages: list[_AgentPage]) -> str:
    blocks = ["# yeetr Documentation", ""]
    for page in pages:
        blocks.extend([f"# {page.title}", "", page.body.rstrip(), ""])
    return "\n".join(blocks).rstrip() + "\n"


def _write_agent_docs(root: Path) -> None:
    output_dir = root / "site" / "agents"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    pages = _page_source(root)
    (output_dir / "index.html").write_text(
        (
            '<!doctype html><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="0; url=index.md">'
            '<link rel="canonical" href="index.md"><a href="index.md">index.md</a>\n'
        ),
        encoding="utf-8",
    )
    (output_dir / "index.md").write_text(_directory_markdown(pages), encoding="utf-8")
    (output_dir / "all.md").write_text(_all_markdown(pages), encoding="utf-8")
    for page in pages:
        (output_dir / page.filename).write_text(page.body.rstrip() + "\n", encoding="utf-8")


def main(
    *,
    config_file: Annotated[Path, Opt(alias="f")] = Path("mkdocs.yml"),
    clean: Annotated[bool, Opt(alias="c")] = False,
    strict: Annotated[bool, Opt(alias="s")] = False,
) -> None:
    """Create agent docs"""
    root = Path(__file__).resolve().parent.parent
    zensical_build = cast(
        Callable[[str, dict[str, bool]], None],
        importlib.import_module("zensical").build,
    )
    zensical_build(str(root / config_file), {"clean": clean, "strict": strict})
    _write_agent_docs(root)
