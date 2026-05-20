<p align="center">
  <img src="assets/yeeter-logo.png" alt="yeeter" width="420">
</p>

# yeeter

A tiny, typed, signature-driven CLI runner.

> No decorators.
> No command classes.
> No ceremony.
> Just yeet the function.

---

## Minimal example

```python
def main(thing: int, *, n: float = 0.1) -> None:
    print(thing, n)


if __name__ == "__main__":
    import yeeter
    yeeter.run(main)
```

```
uv run app.py 5 --n 0.2
```

Note the bare `*` in the signature: parameters **before** it become
positional CLI args, parameters **after** it become `--options`. That's
the whole mapping — no decorators, no per-parameter annotations needed.

---

## Async

```python
async def main(name: str, *, loud: bool = False) -> None:
    ...


if __name__ == "__main__":
    import yeeter
    yeeter.run(main)
```

```
uv run app.py world --loud
```

If the function is a coroutine, its result is awaited via `asyncio.run`,
or via [`uvloop.run`](https://github.com/MagicStack/uvloop) when the
optional `uvloop` extra is installed:

```
uv add "yeeter[uvloop]"
```

When `uvloop` is importable, yeeter uses it transparently — no code
change required. Otherwise it falls back to the stdlib event loop.

---

## Path

```python
from pathlib import Path


def main(path: Path, *, output: Path | None = None) -> None:
    ...
```

```
uv run app.py input.pdf --output out.txt
```

---

## Literal choices

```python
from typing import Literal


def main(*, format: Literal["json", "csv"] = "json") -> None:
    ...
```

```
uv run app.py --format csv
```

---

## `Arg` and `Opt` metadata

For aliases and help text, use `Arg` (positional) or `Opt` (keyword-only)
inside `Annotated`:

```python
from pathlib import Path
from typing import Annotated
from yeeter import Arg, Opt


def main(
    path: Annotated[Path, Arg(help="Input file")],
    *,
    workers: Annotated[int, Opt(alias="-w", help="Worker count")] = 4,
) -> None:
    ...
```

```
uv run app.py input.pdf -w 8
```

`Arg` accepts `help`, `metavar`, `min`, and the path validators below. `Opt`
accepts `alias`, `aliases`, `help`, `metavar`, `envvar`, `hidden`, and the
path validators below. Mixing them (e.g. `Opt` on a positional or `Arg` on a
keyword-only parameter) raises a clear `YeeterError`.

---

## Environment variable fallback (`Opt(envvar=...)`)

`Opt(envvar="NAME")` falls back to an environment variable when the flag is
not provided on the CLI. Precedence: **explicit CLI > env var > default**.

```python
from typing import Annotated
from yeeter import Opt


def main(*, workers: Annotated[int, Opt(envvar="WORKERS")] = 4) -> None:
    ...
```

```
WORKERS=8 uv run app.py        # workers == 8
uv run app.py --workers 16     # workers == 16 (CLI wins)
uv run app.py                  # workers == 4  (default)
```

Env-var values are type-coerced just like CLI values. `bool` accepts
`1/0/true/false/yes/no` (case-insensitive). `list[T]` splits on `os.pathsep`
(`:` on POSIX, `;` on Windows). `Literal` choices are validated.

---

## Hidden options (`Opt(hidden=True)`)

Hidden options still parse from the CLI but are absent from `--help` (both
the usage line and the options table):

```python
from typing import Annotated
from yeeter import Opt


def main(*, debug: Annotated[bool, Opt(hidden=True)] = False) -> None:
    ...
```

---

## Path validators

`Arg` and `Opt` accept `exists`, `file_okay`, `dir_okay`, `readable`, and
`writable` for `Path` parameters. They run at parse time and fail with a
clear error:

```python
from pathlib import Path
from typing import Annotated
from yeeter import Arg


def main(
    src: Annotated[Path, Arg(exists=True, dir_okay=False, readable=True)],
    dst: Annotated[Path, Arg(writable=True)],
) -> None:
    ...
```

Defaults mirror typer: `file_okay=True`, `dir_okay=True`, others off.
Setting any path-check on a non-`Path` parameter raises `YeeterError` at
parser-build time. Validators also apply to `list[Path]` and to
`*paths: Path`.

---

## Variadic positional args (`*args`)

`*args` maps to a trailing variadic positional CLI argument. The annotation
on `*args` is the **element type** (not `list[T]`):

```python
from pathlib import Path


def main(dst: Path, *sources: Path) -> None:
    ...
```

```
uv run cp.py dst src1 src2 src3
```

By default `*args` accepts zero or more values (argparse `nargs="*"`). Use
`Arg(min=1)` to require at least one:

```python
from typing import Annotated
from yeeter import Arg


def main(*sources: Annotated[Path, Arg(min=1, help="Source paths")]) -> None:
    ...
```

Keyword-only options remain `--flags` after `*args`. `**kwargs` is not
supported.

**Why `Annotated`?** Python's type system only permits call expressions
(`Opt(...)`) inside the metadata slot of `Annotated`. No other syntax is
accepted by Pyright in strict mode. The `Annotated` form is verbose but is
the only way to attach per-parameter metadata that fully type-checks.

---

## Rules

- **Positional** parameters become positional CLI args.
- **Keyword-only** parameters (after `*`) become `--options`.
- Names convert from `snake_case` to `kebab-case` for CLI flags.
- `flag: bool = False` becomes `--flag`.
- `flag: bool = True` becomes `--no-flag`.
- Required `bool` parameters raise a clear error.
- `T | None` / `Optional[T]` are accepted; treated as their inner type with
  `None` as default.
- `list[T]` becomes a repeated option (`--tag a --tag b`).

---

## Supported types

`str`, `int`, `float`, `bool`, `pathlib.Path`, `typing.Literal[...]`,
`T | None`, `list[T]`. Anything else raises a clear `YeeterError`.

---

## Logging

By default, `yeeter.run` installs a Rich-based logging handler before
invoking your function, so you get formatted logs with zero boilerplate:

```python
import logging

import yeeter

logger = logging.getLogger("app")


def main(thing: int) -> None:
    logger.info("thing = %s", thing)


if __name__ == "__main__":
    yeeter.run(main)
```

If your function has a `log_level` parameter (e.g.
`log_level: Literal["debug", "info", "warning", "error"] = "info"`), its
value drives the log level. Otherwise, the default is `INFO`.

Setup is idempotent: if the root logger already has handlers, yeeter does
not touch them. To take full control of logging yourself, opt out:

```python
yeeter.run(main, should_setup_logging=False)
```

---

## Testing

`run()` accepts an explicit `argv` for tests:

```python
yeeter.run(main, argv=["5", "--n", "0.2"])
```

---

## yeeter vs. typer

[Typer](https://github.com/fastapi/typer) is a mature, feature-rich CLI
framework. yeeter is a much smaller library aimed at a narrower slice of
the problem. Quick honest comparison so you can pick the right tool:

| Topic                      | yeeter                                                                 | typer                                                              |
| -------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Style                      | Plain function signature, no decorators                                | Decorators (`@app.command()`) or `typer.run`                       |
| Arg vs. option mapping     | Uses Python's `*` separator: before `*` = positional args, after `*` = `--options` (no per-param annotation needed) | Decide per parameter via `typer.Argument(...)` / `typer.Option(...)` |
| Per-param metadata         | `Annotated[T, Arg(...)]` / `Annotated[T, Opt(...)]`                    | `Annotated[T, typer.Argument(...)]` / `typer.Option(...)`          |
| Variadic positional args   | Native `*args: T` maps to a trailing variadic positional arg           | Use `list[T]` with `typer.Argument(...)`                           |
| Boolean flags              | Default drives the flag: `= False` -> `--flag`, `= True` -> `--no-flag` | Pair of flags declared explicitly: `--flag / --no-flag`            |
| Subcommands                | Not supported (single command per script)                              | First-class subcommands, command groups, nested apps               |
| Async functions            | Native: `async def` is run via `asyncio.run` / `uvloop.run`            | Not built-in; wrap with `asyncio.run(...)` yourself                |
| Shell completion           | Not built-in                                                           | Built-in (bash/zsh/fish/PowerShell)                                |
| Help rendering             | Rich tables for args and options                                       | Rich-formatted help via `rich`                                     |
| Type-checker friendliness  | Designed to be Pyright-strict clean end-to-end                         | Some patterns require `# type: ignore` under strict settings       |
| Logging                    | Rich logging set up by default (opt-out)                               | Not opinionated about logging                                      |
| Dependencies               | `rich`, `rich-argparse` (small footprint)                              | `click`, `rich`, `shellingham`, `typing-extensions`                |
| Maturity / ecosystem       | New and small                                                          | Widely adopted, large ecosystem                                    |
| Best for                   | Single-purpose scripts and tools where the function *is* the CLI       | Multi-command CLIs, distributed apps, anything needing completion  |

If you need subcommands or shell completion, use typer. If you want one
function = one CLI with minimal ceremony and strict typing, yeeter is
designed for that.

---

## Development

```
uv sync
uv run ruff check
uv run pyright
uv run pytest
```
