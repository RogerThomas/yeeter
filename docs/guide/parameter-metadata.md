# Parameter Metadata

## `Arg` and `Opt`

For aliases and help text, use `Arg` (positional) or `Opt` (keyword-only)
inside `Annotated`:

```python
from pathlib import Path
from typing import Annotated
from yeetr import Arg, Opt


def main(
    path: Annotated[Path, Arg(help="Input file")],
    *,
    workers: Annotated[int, Opt(alias="w", help="Worker count")] = 4,
) -> None:
    ...
```

```bash
yeet app.py input.pdf -w 8
```

`Arg` accepts `help`, `metavar`, `min` (only meaningful on [variadic `*args`](parameter-types.md#variadic-positional-args-args)),
`parser`, and the [path validators](path-validators.md). `Opt` accepts
`alias`, `aliases`, `help`, `metavar`, `envvar`, `hidden`, `parser`, and the
[path validators](path-validators.md) too. Mixing them (e.g. `Opt` on a
positional or `Arg` on a keyword-only parameter) raises a clear `YeetrError`.

You can also define aliases once and reuse them:

```python
from pathlib import Path
from typing import Annotated
from yeetr import Arg, Opt


type InputPath = Annotated[Path, Arg(help="Input file")]
type WorkerCount = Annotated[int, Opt(alias="w", help="Worker count")]


def main(path: InputPath, *, workers: WorkerCount = 4) -> None:
    ...
```

**Why `Annotated`?** Python's type system only permits call expressions
(`Opt(...)`) inside the metadata slot of `Annotated`. No other syntax is
accepted by Pyright in strict mode. The `Annotated` form is verbose but is
the only way to attach per-parameter metadata that fully type-checks.
Put `Arg(...)` or `Opt(...)` on the parameter's outer `Annotated[...]`, not
on a `list` or `tuple` element.

## Environment variable fallback (`Opt(envvar=...)`)

`Opt(envvar="NAME")` falls back to an environment variable when the flag is
not provided on the CLI. Precedence: **explicit CLI > env var > default**.

```python
from typing import Annotated
from yeetr import Opt


def main(*, workers: Annotated[int, Opt(envvar="WORKERS")] = 4) -> None:
    ...
```

```bash
WORKERS=8 yeet app.py         # workers == 8
yeet app.py --workers 16      # workers == 16 (CLI wins)
yeet app.py                   # workers == 4  (default)
```

Env-var values are type-coerced just like CLI values. `bool` accepts
`1/0/true/false/yes/no` (case-insensitive). `list[T]` splits on `os.pathsep`
(`:` on POSIX, `;` on Windows). `tuple[...]` also splits on `os.pathsep`.
`Literal` and enum choices are validated.

## Custom parsers (`parser=`)

`parser=` supplies your own converter for a parameter, so yeetr can handle
domain types it doesn't build in. yeetr inspects the parser's single
(annotated) parameter, coerces the raw CLI string to *that* type with its
normal machinery, then calls the parser to produce the value passed to the
function:

```python
from pathlib import Path
from typing import Annotated
from yeetr import Opt


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def main(*, pdf_bytes: Annotated[bytes, Opt(parser=read_bytes)]) -> None:
    ...
```

```bash
yeet app.py --pdf-bytes input.pdf
```

Here yeetr sees `read_bytes` takes a `Path`, coerces `"input.pdf"` to a
`Path`, and calls `read_bytes` with it. The outer annotation (`bytes`) is
only the function-facing type — yeetr never coerces to it; the parser is
trusted for the output.

The parser's input type drives everything user-facing: `--help` shows the
input type, and the [path validators](path-validators.md) compose —
`Opt(parser=read_bytes, exists=True)` validates the intermediate `Path`
before the parser runs. If the parser raises `ValueError` or `TypeError`,
the failure is reported as a normal argument error.

The parser must be a callable taking exactly one type-annotated parameter;
anything else raises `YeetrError` at parser-build time. `parser=` is not
supported on `list`/`tuple` parameters or variadic `*args`, and `bool`,
`list`, and `tuple` parser input types are rejected.

## Hidden options (`Opt(hidden=True)`)

Hidden options still parse from the CLI but are absent from `--help` (both
the usage line and the options table):

```python
from typing import Annotated
from yeetr import Opt


def main(*, debug: Annotated[bool, Opt(hidden=True)] = False) -> None:
    ...
```

## Next steps

- [Bundled Args](bundled-args.md) — group related parameters into a
  `dataclass` or `NamedTuple` instead of a long argument list.
- [Path Validators](path-validators.md) — `exists`, `file_okay`, `dir_okay`,
  `readable`, and `writable` checks for `Path` parameters.
