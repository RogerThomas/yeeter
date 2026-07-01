# yeetr vs. typer

[Typer](https://github.com/fastapi/typer) is a mature, feature-rich CLI
framework and a direct inspiration for yeetr — the `Annotated[..., Arg/Opt]`
metadata pattern, path validators, and envvar fallback all take cues from
typer. yeetr is a much smaller library aimed at a narrower slice of the
problem. Quick honest comparison so you can pick the right tool:

| Topic                      | yeetr                                                                 | typer                                                              |
| --------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| Style                      | Plain function signature, no decorators                                | Decorators (`@app.command()`) or `typer.run`                       |
| Zero-boilerplate runner    | `yeet main.py [func] [args...]` script — no `if __name__ == "__main__"` / `yeetr.run(...)` block needed | Always need a `typer.run(...)` call or a decorated `@app.command()` entry point |
| Executable shebang         | `#!yeet` or `#!uv run yeet` can make the script itself executable without extra wrapper code | No equivalent single-line signature-driven runner; still need a `typer.run(...)` or app entry point |
| Arg vs. option mapping     | Uses Python's `*` separator: before `*` = positional args, after `*` = `--options` (no per-param annotation needed) | Decide per parameter via `typer.Argument(...)` / `typer.Option(...)` |
| Per-param metadata         | `Annotated[T, Arg(...)]` / `Annotated[T, Opt(...)]`                    | `Annotated[T, typer.Argument(...)]` / `typer.Option(...)`          |
| Structured arg object      | Accept one `dataclass` or `NamedTuple`; fields become the CLI and the function receives the object | Declare command params individually, then construct your object inside the command |
| Variadic positional args   | Native `*args: T` maps to a trailing variadic positional arg           | Use `list[T]` with `typer.Argument(...)`                           |
| Boolean flags              | Default drives the flag: `= False` -> `--flag`, `= True` -> `--no-flag` | Pair of flags declared explicitly: `--flag / --no-flag`            |
| Subcommands                | Not supported (single command per script)                              | First-class subcommands, command groups, nested apps               |
| Async functions            | Native: `async def` is run via `asyncio.run` / `uvloop.run`            | Not built-in; wrap with `asyncio.run(...)` yourself                |
| Shell completion           | Not built-in                                                           | Built-in (bash/zsh/fish/PowerShell)                                |
| Help rendering             | Rich tables for args and options                                       | Rich-formatted help via `rich`                                     |
| Type-checker friendliness  | Designed to be Pyright-strict clean end-to-end                         | Some patterns require `# type: ignore` under strict settings       |
| Logging                    | Rich logging set up by default (opt-out)                               | Not opinionated about logging                                      |
| Dependencies               | `rich`, `rich-argparse` (small footprint)                              | `click`, `rich`, `shellingham`, `typing-extensions`                |
| Maturity / ecosystem       | New and small                                                          | Widely adopted, large ecosystem                                    |
| Best for                   | Single-purpose scripts and tools where the function *is* the CLI       | Multi-command CLIs, distributed apps, anything needing completion  |

If you need subcommands or shell completion, use typer. If you want one
function = one CLI with minimal ceremony and strict typing, yeetr is
designed for that.
