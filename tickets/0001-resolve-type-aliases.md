# Ticket 0001: Resolve PEP 695 / `TypeAliasType` aliases in parameter annotations

## Status

Open

## Summary

Yeeter does not resolve PEP 695 `type` statement aliases (a.k.a.
`typing.TypeAliasType`) when introspecting a function signature. As a result,
declaring a parameter using a `type` alias breaks both the CLI help rendering
and runtime argument parsing.

## Reproduction

`main.py`:

```python
from typing import Annotated
from pathlib import Path
from yeeter import Param
import yeeter

type Workers = Annotated[int, Param(alias="-w", help="Worker count")]

async def main(
    pdf_path: Path,
    *,
    workers: Workers = 4,
) -> None:
    ...

if __name__ == "__main__":
    yeeter.run(main)
```

Running:

```
uv run main.py input.pdf --workers 2
```

Fails with:

```
yeeter._runner.YeeterError: Unsupported type Workers for parameter 'workers'.
```

The help table also shows `Workers` as the `Type` column value and loses the
`-w` alias and "Worker count" description, because the `Annotated[...]`
metadata is never unwrapped.

## Root cause

In `yeeter/_runner.py`:

- `_unwrap_annotated` only handles `typing.Annotated` whose `get_origin` is
  `typing.Annotated`. It does not handle `typing.TypeAliasType` instances
  produced by the PEP 695 `type Foo = ...` statement.
- `_add_parameter` therefore sees the alias object itself (`Workers`) as the
  effective type. `_coerce_value` does not know how to coerce strings into
  that, and raises `YeeterError`.

## Proposed fix

Add an unwrap step that detects `typing.TypeAliasType` and replaces the
annotation with `alias.__value__` before further processing. This should run
recursively (an alias may resolve to another alias or to `Annotated[...]`).

Sketch:

```python
def _resolve_type_alias(annotation: Any) -> Any:
    while isinstance(annotation, typing.TypeAliasType):
        annotation = annotation.__value__
    return annotation
```

Call this at the top of `_unwrap_annotated` (and again on the inner type after
unwrapping `Annotated`, to support aliases nested inside `Annotated` or
`Optional`).

Also merge `Param` metadata correctly: if the alias resolves to
`Annotated[int, Param(...)]` and the call site has its own `Annotated[Workers, Param(...)]`,
the outer `Param` should win for fields it sets, but inherit unset fields
from the inner one. Decide on precedence and document it.

## Acceptance criteria

- [ ] `type Workers = Annotated[int, Param(alias="-w", help="Worker count")]`
      used as a parameter annotation produces the same CLI as inlining the
      `Annotated[...]` directly: `--workers`/`-w` flag, int type, help text.
- [ ] The Rich help `Type` column shows `int`, not `Workers`.
- [ ] Aliases that resolve to bare types (`type Count = int`) also work.
- [ ] Aliases nested inside `Optional` / unions are resolved
      (e.g. `type MaybeInt = int | None`).
- [ ] Aliases pointing to other aliases are resolved transitively.
- [ ] Existing tests continue to pass; new tests cover each case above.

## Out of scope

- Forward references / stringified annotations (`from __future__ import annotations`).
  Track separately if needed.
- `typing.NewType` support.
