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

## Module-callable form

The package itself is callable. `yeeter(main)` is equivalent to `yeeter.run(main)`:

```python
if __name__ == "__main__":
    import yeeter
    yeeter(main)
```

**Limitation:** type checkers (including Pyright in strict mode) do not understand
modules-as-callables. You may need `# pyright: ignore[reportCallIssue]` at the
call site if you rely on this form. The functional form `yeeter.run(main)` has
full type information preserved.

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

## `Param` metadata

For aliases and help text, use `Param` inside `Annotated`:

```python
from typing import Annotated
from yeeter import Param


def main(*, workers: Annotated[int, Param(alias="-w", help="Worker count")] = 4) -> None:
    ...
```

```
python app.py -w 8
```

**Why `Annotated`?** Python's type system only permits call expressions
(`Param(...)`) inside the metadata slot of `Annotated`. No other syntax —
including PEP 695 type aliases like `Arg[T, Param(...)]` — is accepted by
Pyright in strict mode. The `Annotated` form is verbose but is the only way to
attach per-parameter metadata that fully type-checks.

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
