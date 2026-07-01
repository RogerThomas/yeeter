# Parameter Types

## Path

```python
from pathlib import Path


def main(path: Path, *, output: Path | None = None) -> None:
    ...
```

```bash
yeet app.py input.pdf --output out.txt
```

## Literal choices

```python
from typing import Literal


def main(*, format: Literal["json", "csv"] = "json") -> None:
    ...
```

```bash
yeet app.py --format csv
```

## Enum choices

```python
from enum import StrEnum


class Format(StrEnum):
    JSON = "json"
    CSV = "csv"


def main(*, format: Format = Format.JSON) -> None:
    ...
```

```bash
yeet app.py --format csv
```

Enums parse from their member values and the function receives the enum
member (`Format.CSV` in the example above). Choice values are shown in
help output and invalid values fail during argument parsing.

## Tuples

```python
def main(point: tuple[int, float], *, values: tuple[int, ...] = ()) -> None:
    ...
```

```bash
yeet app.py 1 2.5 --values 3 4 5
```

Fixed-width tuples such as `tuple[int, float]` consume exactly one CLI value
per element and coerce each element according to its annotation. Variable
tuples such as `tuple[int, ...]` consume one or more values unless they have
a default, in which case zero values are allowed.

## Supported Primitives

`str`, `int`, `float`, `bool`, `pathlib.Path`, `typing.Literal[...]`,
`enum.Enum` subclasses, `T | None`, `list[T]`, `tuple[T, U]`, and
`tuple[T, ...]`. Anything else raises a clear `YeetrError`.

## Next steps

[Parameter Metadata](parameter-metadata.md) covers attaching help text,
aliases, env var fallback, and validators to any of these types.
