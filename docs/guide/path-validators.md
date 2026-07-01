# Path Validators

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
parser-build time.

## Beyond a single `Path`

Validators also apply wherever `Path` is the element type of a container —
`list[Path]`, `tuple[Path, ...]`, `tuple[Path, Path]`, and variadic
`*paths: Path` all run the same checks against every value:

```python
from pathlib import Path
from typing import Annotated
from yeetr import Arg


def main(*paths: Annotated[Path, Arg(exists=True, dir_okay=False)]) -> None:
    ...
```

```bash
yeet app.py a.txt b.txt  # both must exist and not be directories
```
