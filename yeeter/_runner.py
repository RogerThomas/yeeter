import argparse
import asyncio
import inspect
import sys
import types
import typing
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from inspect import Parameter, Signature
from pathlib import Path
from typing import Any, Literal, get_args, get_origin

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich_argparse import RichHelpFormatter

from ._metadata import Param


@dataclass
class _ParamInfo:
    name: str
    is_positional: bool
    long_flag: str | None = None
    aliases: list[str] = field(default_factory=list[str])
    type_label: str = ""
    default_label: str = ""
    required: bool = False
    choices: list[str] = field(default_factory=list[str])
    help_text: str = ""
    metavar: str | None = None


def _type_label(effective: Any, is_list: bool, is_literal: bool) -> str:
    if effective is bool:
        return "flag"
    if is_literal:
        return "choice"
    if is_list:
        (inner_t,) = get_args(effective)
        return f"list[{getattr(inner_t, '__name__', str(inner_t))}]"
    return getattr(effective, "__name__", str(effective))


def _default_label(has_default: bool, default: Any, effective: Any) -> str:
    if not has_default:
        return ""
    if effective is bool:
        return repr(default)
    return _format_default(default)


class YeeterError(Exception):
    """Raised when the function signature is not convertible into a CLI."""


def _snake_to_kebab(name: str) -> str:
    return name.replace("_", "-")


def _format_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return f"[{', '.join(map(repr, value))}]" if value else "[]"  # pyright: ignore[reportUnknownArgumentType]
    return repr(value)


def _with_default_suffix(help_text: str | None, default: Any) -> str:
    base = help_text or ""
    suffix = f"(default: {_format_default(default)})"
    if not base:
        return suffix
    return f"{base} {suffix}"


def _is_optional(annotation: Any) -> tuple[bool, Any]:
    origin = get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1 and len(get_args(annotation)) == 2:
            return True, args[0]
    return False, annotation


def _unwrap_annotated(annotation: Any) -> tuple[Any, Param]:
    metadata = Param()
    if get_origin(annotation) is typing.Annotated:
        args = get_args(annotation)
        base = args[0]
        for extra in args[1:]:
            if isinstance(extra, Param):
                metadata = extra
        return base, metadata
    return annotation, metadata


def _coerce_value(raw: str, target: Any, param_name: str) -> Any:
    if target is str:
        return raw
    if target is int:
        try:
            return int(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid int value for {param_name!r}: {raw!r}") from exc
    if target is float:
        try:
            return float(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid float value for {param_name!r}: {raw!r}") from exc
    if target is Path:
        return Path(raw)
    if target is bool:
        lowered = raw.lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
        raise argparse.ArgumentTypeError(f"invalid bool value for {param_name!r}: {raw!r}")
    raise YeeterError(f"Unsupported type {target!r} for parameter {param_name!r}.")


def _type_caster(target: Any, param_name: str) -> Callable[[str], Any]:
    def cast(raw: str) -> Any:
        return _coerce_value(raw, target, param_name)

    cast.__name__ = getattr(target, "__name__", "value")
    return cast


def _literal_caster(choices: tuple[Any, ...], param_name: str) -> Callable[[str], Any]:
    str_choices = {str(c): c for c in choices}

    def cast(raw: str) -> Any:
        if raw in str_choices:
            return str_choices[raw]
        raise argparse.ArgumentTypeError(
            f"invalid choice {raw!r} for {param_name!r}; choose from {sorted(str_choices)!r}",
        )

    cast.__name__ = "choice"
    return cast


def _add_parameter(parser: argparse.ArgumentParser, param: Parameter) -> _ParamInfo:
    annotation = param.annotation
    if annotation is Parameter.empty:
        raise YeeterError(f"Parameter {param.name!r} is missing a type annotation.")

    base, metadata = _unwrap_annotated(annotation)
    is_optional, inner = _is_optional(base)
    effective = inner if is_optional else base

    is_keyword_only = param.kind is Parameter.KEYWORD_ONLY
    has_default = param.default is not Parameter.empty
    default = param.default if has_default else None

    origin = get_origin(effective)
    is_list = origin is list
    is_literal = origin is Literal

    help_text = metadata.help
    metavar = metadata.metavar

    info = _ParamInfo(
        name=param.name,
        is_positional=not is_keyword_only,
        type_label=_type_label(effective, is_list, is_literal),
        default_label=_default_label(has_default, default, effective),
        required=not has_default,
        choices=[str(c) for c in get_args(effective)] if is_literal else [],
        help_text=help_text or "",
        metavar=metavar,
    )

    if is_keyword_only:
        flags = _build_flags(param.name, metadata)
        _add_option(
            parser=parser,
            param_name=param.name,
            flags=flags,
            effective=effective,
            is_list=is_list,
            is_literal=is_literal,
            has_default=has_default,
            default=default,
            help_text=help_text,
            metavar=metavar,
        )
        long_flag, aliases = _split_flags_for_display(param.name, flags, effective, default)
        info.long_flag = long_flag
        info.aliases = aliases
    else:
        _add_positional(
            parser=parser,
            param_name=param.name,
            effective=effective,
            is_list=is_list,
            is_literal=is_literal,
            has_default=has_default,
            default=default,
            help_text=help_text,
            metavar=metavar,
        )
    return info


def _split_flags_for_display(
    param_name: str,
    flags: list[str],
    effective: Any,
    default: Any,
) -> tuple[str, list[str]]:
    if effective is bool and default is True:
        return f"--no-{_snake_to_kebab(param_name)}", []
    primary = f"--{_snake_to_kebab(param_name)}"
    others = [f for f in flags if f != primary]
    return primary, others


def _build_flags(param_name: str, metadata: Param) -> list[str]:
    long_flag = f"--{_snake_to_kebab(param_name)}"
    extras: list[str] = []
    if metadata.alias:
        extras.append(metadata.alias)
    extras.extend(metadata.aliases)
    shorts = [f for f in extras if f.startswith("-") and not f.startswith("--")]
    longs = [f for f in extras if f.startswith("--")]
    return [*shorts, long_flag, *longs]


def _add_option(
    *,
    parser: argparse.ArgumentParser,
    param_name: str,
    flags: list[str],
    effective: Any,
    is_list: bool,
    is_literal: bool,
    has_default: bool,
    default: Any,
    help_text: str | None,
    metavar: str | None,
) -> None:
    if effective is bool:
        if not has_default:
            raise YeeterError(
                f"Boolean option {param_name!r} must have a default (use `= False` or `= True`).",
            )
        if default is False:
            parser.add_argument(
                *flags,
                dest=param_name,
                action="store_true",
                default=False,
                help=help_text,
            )
        elif default is True:
            no_flag = f"--no-{_snake_to_kebab(param_name)}"
            parser.add_argument(
                no_flag,
                dest=param_name,
                action="store_false",
                default=True,
                help=help_text,
            )
        else:
            raise YeeterError(f"Boolean option {param_name!r} has a non-bool default.")
        return

    rendered_help = _with_default_suffix(help_text, default) if has_default else help_text

    if is_literal:
        choices = get_args(effective)
        parser.add_argument(
            *flags,
            dest=param_name,
            type=_literal_caster(choices, param_name),
            choices=list(choices),
            default=default if has_default else None,
            required=not has_default,
            help=rendered_help,
            metavar=metavar,
        )
        return

    if is_list:
        (inner_t,) = get_args(effective)
        list_default = list(default) if has_default and default is not None else ([] if has_default else None)
        parser.add_argument(
            *flags,
            dest=param_name,
            type=_type_caster(inner_t, param_name),
            action="append",
            default=list_default,
            required=not has_default,
            help=rendered_help,
            metavar=metavar,
        )
        return

    parser.add_argument(
        *flags,
        dest=param_name,
        type=_type_caster(effective, param_name),
        default=default if has_default else None,
        required=not has_default,
        help=rendered_help,
        metavar=metavar,
    )


def _add_positional(
    *,
    parser: argparse.ArgumentParser,
    param_name: str,
    effective: Any,
    is_list: bool,
    is_literal: bool,
    has_default: bool,
    default: Any,
    help_text: str | None,
    metavar: str | None,
) -> None:
    dest = param_name
    display_metavar = metavar or _snake_to_kebab(param_name).upper()
    nargs: str | None = None
    if has_default:
        nargs = "?"

    if effective is bool:
        raise YeeterError(
            f"Positional boolean parameter {param_name!r} is not supported. "
            f"Make it keyword-only (after `*`) to expose as a --flag.",
        )

    rendered_help = _with_default_suffix(help_text, default) if has_default else help_text

    if is_literal:
        choices = get_args(effective)
        kwargs: dict[str, Any] = {
            "type": _literal_caster(choices, param_name),
            "choices": list(choices),
            "help": rendered_help,
            "metavar": display_metavar,
        }
        if has_default:
            kwargs["nargs"] = "?"
            kwargs["default"] = default
        parser.add_argument(dest, **kwargs)
        return

    if is_list:
        (inner_t,) = get_args(effective)
        kwargs = {
            "type": _type_caster(inner_t, param_name),
            "nargs": "*" if has_default else "+",
            "help": rendered_help,
            "metavar": display_metavar,
        }
        if has_default:
            kwargs["default"] = list(default) if default is not None else []
        parser.add_argument(dest, **kwargs)
        return

    kwargs = {
        "type": _type_caster(effective, param_name),
        "help": rendered_help,
        "metavar": display_metavar,
    }
    if nargs is not None:
        kwargs["nargs"] = nargs
    if has_default:
        kwargs["default"] = default
    parser.add_argument(dest, **kwargs)


def _build_parser(func: Callable[..., Any], prog: str | None = None) -> tuple[argparse.ArgumentParser, Signature]:
    sig = inspect.signature(func)
    doc = inspect.getdoc(func)
    resolved_prog = prog or _default_prog()
    parser = argparse.ArgumentParser(
        prog=resolved_prog,
        description=doc,
        add_help=True,
        formatter_class=RichHelpFormatter,
    )
    infos: list[_ParamInfo] = []
    for param in sig.parameters.values():
        if param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            raise YeeterError(
                f"Variadic parameter {param.name!r} is not supported.",
            )
        infos.append(_add_parameter(parser, param))
    _install_rich_help(parser, resolved_prog, doc, infos)
    return parser, sig


def _install_rich_help(
    parser: argparse.ArgumentParser,
    prog: str,
    doc: str | None,
    infos: list[_ParamInfo],
) -> None:
    def print_help(file: Any = None) -> None:
        _render_rich_help(prog, doc, infos, file=file)

    parser.print_help = print_help  # type: ignore[method-assign]


def _build_usage(prog: str, infos: list[_ParamInfo]) -> str:
    parts: list[str] = [prog, "[-h]"]
    for info in infos:
        if info.is_positional:
            continue
        flag = info.long_flag or f"--{_snake_to_kebab(info.name)}"
        if info.type_label == "flag":
            token = flag
        else:
            metavar = info.metavar or info.name.upper()
            token = f"{flag} {metavar}"
        parts.append(token if info.required else f"[{token}]")
    for info in infos:
        if info.is_positional:
            display = info.metavar or _snake_to_kebab(info.name).upper()
            parts.append(display if info.required else f"[{display}]")
    return " ".join(parts)


def _render_rich_help(
    prog: str,
    doc: str | None,
    infos: list[_ParamInfo],
    *,
    file: Any = None,
) -> None:
    console = Console(file=file) if file is not None else Console()

    usage = _build_usage(prog, infos)
    console.print(Text("Usage: ", style="bold yellow"), end="")
    console.print(usage)
    if doc:
        console.print()
        console.print(doc)

    positional = [i for i in infos if i.is_positional]
    options = [i for i in infos if not i.is_positional]

    if positional:
        console.print()
        console.print(_arguments_table(positional))

    console.print()
    console.print(_options_table(options))


def _required_text(required: bool) -> Text:
    return Text("yes", style="bold red") if required else Text("no", style="dim")


def _arguments_table(infos: list[_ParamInfo]) -> Table:
    table = Table(title="Arguments", title_style="bold cyan", title_justify="left", show_lines=False)
    table.add_column("Name", style="bold green", no_wrap=True)
    table.add_column("Type", style="magenta", no_wrap=True)
    table.add_column("Required", no_wrap=True)
    table.add_column("Default", style="yellow", no_wrap=True)
    table.add_column("Choices", style="blue")
    table.add_column("Description", style="white")
    for info in infos:
        display = info.metavar or _snake_to_kebab(info.name).upper()
        table.add_row(
            display,
            info.type_label,
            _required_text(info.required),
            info.default_label or "-",
            ", ".join(info.choices) if info.choices else "-",
            info.help_text or "-",
        )
    return table


def _options_table(infos: list[_ParamInfo]) -> Table:
    table = Table(title="Options", title_style="bold cyan", title_justify="left", show_lines=False)
    table.add_column("Name", style="bold green", no_wrap=True)
    table.add_column("Alias(es)", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta", no_wrap=True)
    table.add_column("Required", no_wrap=True)
    table.add_column("Default", style="yellow", no_wrap=True)
    table.add_column("Choices", style="blue")
    table.add_column("Description", style="white")

    table.add_row(
        "--help",
        "-h",
        "flag",
        _required_text(False),
        "-",
        "-",
        "show this help message and exit",
    )

    for info in infos:
        table.add_row(
            info.long_flag or f"--{_snake_to_kebab(info.name)}",
            ", ".join(info.aliases) if info.aliases else "-",
            info.type_label,
            _required_text(info.required),
            info.default_label or "-",
            ", ".join(info.choices) if info.choices else "-",
            info.help_text or "-",
        )
    return table


def _default_prog() -> str:
    argv0 = sys.argv[0] if sys.argv else "app"
    return Path(argv0).name or "app"


def _build_call_kwargs(sig: Signature, namespace: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    for name in sig.parameters:
        kwargs[name] = getattr(namespace, name)
    return kwargs


def run[T](
    func: Callable[..., T] | Callable[..., Awaitable[T]],
    argv: Sequence[str] | None = None,
    *,
    prog: str | None = None,
) -> T:
    """Run ``func`` as a CLI.

    The function signature defines the CLI:
    - positional parameters become positional CLI args
    - keyword-only parameters (after ``*``) become options

    If ``func`` is async, the coroutine is executed via ``asyncio.run``.

    Pass ``argv`` to bypass ``sys.argv`` (useful for tests).
    """
    parser, sig = _build_parser(func, prog=prog)
    raw_argv = list(sys.argv[1:]) if argv is None else list(argv)
    namespace = parser.parse_args(raw_argv)
    call_kwargs = _build_call_kwargs(sig, namespace)
    result = func(**call_kwargs)
    if inspect.iscoroutine(result):
        return typing.cast(T, asyncio.run(result))
    return typing.cast(T, result)
