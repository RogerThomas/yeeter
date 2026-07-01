# Async Support

`yeetr` supports async functions natively. Just make your `main` an `async def` and `yeet`
will run it with `asyncio.run` or `uvloop.run` if [uvloop](https://github.com/MagicStack/uvloop)
is installed.

```python
async def main(name: str, *, loud: bool = False) -> None:
    ...
```

```bash
yeet app.py world --loud
```

If the function is a coroutine, its result is awaited via `asyncio.run`,
or via [`uvloop.run`](https://github.com/MagicStack/uvloop) when the
optional `uvloop` extra is installed:

```bash
uv add "yeetr[uvloop]"
```

When `uvloop` is importable, yeetr uses it transparently — no code
change required. Otherwise it falls back to the stdlib event loop.

## Next steps

[Parameter Types](parameter-types.md) covers every type yeetr understands,
from `Path` to `Enum` to tuples.
