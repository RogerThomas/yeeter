# Getting Started

## Zero-boilerplate: just yeet it

Installing `yeetr` also installs a `yeet` script that finds and runs a
function in any Python file.

No `if __name__ == "__main__"` block, no `yeetr.run(...)` call — just
the function:

```python
# app.py
def main(thing: int, *, n: float = 0.1) -> None:
    print(thing, n)
```

```bash
yeet app.py 5 -n 0.2
```

If `app.py` does not exist yet, `yeet` will scaffold a runnable Python
script for you, mark it executable, and print the created path. Run the
same command a second time, or call `./app.py` directly, and it will
execute normally.

The default function name is `main`. Pass a different one to pick another
top-level function in the same file:

```python
# app.py
def main(...) -> None: ...
def greet(name: str, *, loud: bool = False) -> None: ...
```

```bash
yeet app.py greet world --loud
```

`yeet app.py --help` prints the **target function's** help, not yeet's.
`yeet` itself only has `yeet FILE [FUNC] [args...]`.

You can still use the explicit `yeetr.run(main)` form when you prefer —
the `yeet` script is just sugar on top of it.

## Explicit `yeetr.run(main)`

```python
def main(thing: int, *, n: float = 0.1) -> None:
    print(thing, n)


if __name__ == "__main__":
    import yeetr
    yeetr.run(main)
```

```bash
yeet app.py 5 -n 0.2
```

Note the bare `*` in the signature: parameters **before** it become
positional CLI args, parameters **after** it become `--options`. That's
the whole mapping — no decorators, no per-parameter annotations needed.

## Script Execution

### Hashbang

For tiny scripts, you can make the file itself executable and let `yeet`
discover `main` directly from the shebang. The short forms are:

```python
#!yeet
```

or:

```python
#!uv run yeet
```

For example:

```python
#!yeet

def main(name: str, *, loud: bool = False) -> None:
    print(name.upper() if loud else name)
```

Then run it directly:

```bash
chmod +x greet.py
./greet.py world --loud
```

If you need a different entry function, keep the shebang simple and call
`uv run yeet app.py other_func ...` explicitly instead.

## Next steps

- [Async Support](async.md) for `async def main`.
- [Parameter Types](parameter-types.md) for everything yeetr can type-check
  and parse.
