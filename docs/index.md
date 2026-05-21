# yeeter

`yeeter` is a tiny, typed, signature-driven CLI runner.

It turns a Python function into a command line interface:

```python
from yeeter import run


def main(name: str, *, loud: bool = False) -> None:
    ...


run(main)
```

Positional parameters become positional CLI args. Keyword-only parameters become `--options`.

## Start Here

- Read the main project README for usage and examples.
- Check the API reference for `run`, `Param`, and `YeeterError`.
