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

`Arg` accepts `help`, `metavar`, `min`, and the path validators below. `Opt`
accepts `alias`, `aliases`, `help`, `metavar`, `envvar`, `hidden`, and the
path validators below. Mixing them (e.g. `Opt` on a positional or `Arg` on a
keyword-only parameter) raises a clear `YeetrError`.

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

## Bundled args

Sometimes you want to bundle all your args into a single neat object. For
that, use a `dataclass` or `NamedTuple` and make your function accept one
parameter:

```python
from dataclasses import dataclass
from typing import Annotated
from yeetr import Opt


@dataclass(slots=True)
class Args:
    name: Annotated[str, Opt(alias="n", help="The name to greet")] = "World"
    tolerance: Annotated[float, Opt(alias="t", help="Tolerance level")] = 0.5


def main(args: Args) -> None:
    print(args)
```

```bash
yeet app.py -n Alice -t 0.75
```

The same pattern works with `NamedTuple`:

```python
from typing import Annotated, NamedTuple
from yeetr import Opt


class Args(NamedTuple):
    name: Annotated[str, Opt(alias="n", help="The name to greet")] = "World"
    tolerance: Annotated[float, Opt(alias="t", help="Tolerance level")] = 0.5


def main(args: Args) -> None:
    print(args)
```

Fields annotated with `Arg` become positional CLI args. Fields annotated with
`Opt`, and fields without yeetr metadata, become `--options`.

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

## Hidden options (`Opt(hidden=True)`)

Hidden options still parse from the CLI but are absent from `--help` (both
the usage line and the options table):

```python
from typing import Annotated
from yeetr import Opt


def main(*, debug: Annotated[bool, Opt(hidden=True)] = False) -> None:
    ...
```

## Path validators

`Arg` and `Opt` accept `exists`, `file_okay`, `dir_okay`, `readable`, and
`writable` for `Path` parameters. They run at parse time and fail with a
clear error:

```python
from pathlib import Path
from typing import Annotated
from yeetr import Arg


def main(
    src: Annotated[Path, Arg(exists=True, dir_okay=False, readable=True)],
    dst: Annotated[Path, Arg(writable=True)],
) -> None:
    ...
```

Defaults mirror typer: `file_okay=True`, `dir_okay=True`, others off.
Setting any path-check on a non-`Path` parameter raises `YeetrError` at
parser-build time. Validators also apply to `list[Path]` and to
`*paths: Path`.

## Variadic positional args (`*args`)

`*args` maps to a trailing variadic positional CLI argument. The annotation
on `*args` is the **element type** (not `list[T]`):

```python
from pathlib import Path


def main(dst: Path, *sources: Path) -> None:
    ...
```

```bash
yeet app.py dst src1 src2 src3
```

By default `*args` accepts zero or more values (argparse `nargs="*"`). Use
`Arg(min=1)` to require at least one:

```python
from typing import Annotated
from yeetr import Arg


def main(*sources: Annotated[Path, Arg(min=1, help="Source paths")]) -> None:
    ...
```

Keyword-only options remain `--flags` after `*args`. `**kwargs` is not
supported.

**Why `Annotated`?** Python's type system only permits call expressions
(`Opt(...)`) inside the metadata slot of `Annotated`. No other syntax is
accepted by Pyright in strict mode. The `Annotated` form is verbose but is
the only way to attach per-parameter metadata that fully type-checks.
