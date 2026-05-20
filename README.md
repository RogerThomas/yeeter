# yeeter

A tiny, typed, signature-driven CLI runner.

> No decorators.
> No command classes.
> No ceremony.
> Just yeet the function.

## Minimal example

```python
def main(thing: int, *, n: float = 0.1) -> None:
    print(thing, n)


if __name__ == "__main__":
    import yeeter
    yeeter.run(main)
```

```
python app.py 5 --n 0.2
```

## Async

```python
async def main(name: str, *, loud: bool = False) -> None:
    ...

yeeter.run(main)
```

```
python app.py Roger --loud
```

If the function is a coroutine, its result is awaited via `asyncio.run`.

## Path

```python
from pathlib import Path


def main(path: Path, *, output: Path | None = None) -> None:
    ...
```

```
python app.py input.pdf --output out.txt
```

## Literal choices

```python
from typing import Literal


def main(*, format: Literal["json", "csv"] = "json") -> None:
    ...
```

```
python app.py --format csv
```

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
python app.py input.pdf -w 8
```

`Arg` accepts `help`, `metavar`, and `min`. `Opt` accepts `alias`, `aliases`,
`help`, and `metavar`. Mixing them (e.g. `Opt` on a positional or `Arg` on a
keyword-only parameter) raises a clear `YeeterError`.

## Variadic positional args (`*args`)

`*args` maps to a trailing variadic positional CLI argument. The annotation
on `*args` is the **element type** (not `list[T]`):

```python
from pathlib import Path


def main(dst: Path, *sources: Path) -> None:
    ...
```

```
python cp.py dst src1 src2 src3
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

## Supported types

`str`, `int`, `float`, `bool`, `pathlib.Path`, `typing.Literal[...]`,
`T | None`, `list[T]`. Anything else raises a clear `YeeterError`.

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

## Testing

`run()` accepts an explicit `argv` for tests:

```python
yeeter.run(main, argv=["5", "--n", "0.2"])
```

## Development

```
uv sync
uv run ruff check
uv run pyright
uv run pytest
```
