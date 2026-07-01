# Bundled Args

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

## Rules

- The bundled parameter itself must **not** be keyword-only — `def main(*, args: Args)`
  raises a clear `YeetrError`. Bundling only makes sense as a positional
  parameter.
- Every field must be part of `__init__`. A `dataclass` field declared with
  `field(init=False)` is skipped, and a dataclass with no init fields at all
  raises `YeetrError` — there would be nothing left to expose on the CLI.

## Next steps

[Path Validators](path-validators.md) covers `exists`/`file_okay`/`dir_okay`/
`readable`/`writable` checks, which work the same way on `Path` fields inside
a bundled `dataclass` or `NamedTuple` as they do on a plain parameter.
