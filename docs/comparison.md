# yeetr vs. typer

[Typer](https://github.com/fastapi/typer) is a mature, feature-rich CLI
framework and a direct inspiration for yeetr — the `Annotated[..., Arg/Opt]`
metadata pattern, path validators, and envvar fallback all take cues from
typer. yeetr is a much smaller library aimed at a narrower slice of the
problem. Quick honest comparison so you can pick the right tool:

| Topic                      | yeetr                                                                 | typer                                                              |
| --------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| Style                      | Plain function signature, no decorators                                | Decorators (`@app.command()`) or `typer.run`                       |
| Zero-boilerplate runner    | `yeet main.py [func] [args...]` script — no `if __name__ == "__main__"` / `yeetr.run(...)` block needed | Similar: `typer main.py run [args...]` runs scripts, even ones that don't import typer; in code you need `typer.run(...)` or an `@app.command()` entry point |
| Executable shebang         | `#!yeet` or `#!uv run yeet` can make the script itself executable without extra wrapper code; `#!yeet FUNC` dispatches to a specific function | No shebang equivalent: the `typer` command needs its `run` subcommand between the file and the args, which a shebang can't inject |
| Arg vs. option mapping     | Python's `*` separator decides: before `*` = positional args, after `*` = `--options` | Presence of a default decides: no default = positional arg, default = `--option`; override per parameter via `typer.Argument(...)` / `typer.Option(...)` |
| Per-param metadata         | `Annotated[T, Arg(...)]` / `Annotated[T, Opt(...)]`                    | `Annotated[T, typer.Argument(...)]` / `typer.Option(...)`          |
| Custom parsers             | `Arg/Opt(parser=...)` — the CLI string is first coerced to the parser's annotated input type (path validators compose), then the parser runs | `typer.Argument/Option(parser=...)` — the parser receives the raw string |
| Structured arg object      | Accept one `dataclass` or `NamedTuple`; fields become the CLI and the function receives the object | Declare command params individually, then construct your object inside the command |
| Variadic positional args   | Native `*args: T` maps to a trailing variadic positional arg           | Use `list[T]` with `typer.Argument(...)`                           |
| Boolean flags              | One flag, driven by the default: `= False` -> `--flag`, `= True` -> `--no-flag` | Auto-generates the pair `--flag / --no-flag`; explicit declaration only to customize the names |
| Subcommands                | Subcommand-style dispatch via the runner: `yeet main.py FUNC [args...]` picks any public function by name (also `yeet FILE:FUNC` and `#!yeet FUNC` shebangs); no command groups, nesting, or function listing in `--help` | First-class subcommands, command groups, nested apps               |
| Async functions            | Native: `async def` is run via `asyncio.run` / `uvloop.run`            | Not built-in; an `async def` command is silently never awaited — wrap with `asyncio.run(...)` yourself |
| Shell completion           | Not built-in                                                           | Built-in (bash/zsh/fish/PowerShell)                                |
| Help rendering             | Rich tables for args and options                                       | Rich-formatted help via `rich`                                     |
| Type-checker friendliness  | Pyright-strict clean end-to-end; `Arg`/`Opt` are plain, precisely-typed dataclasses | Also clean under strict Pyright; `typer.Argument()`/`typer.Option()` return `Any`, which relaxes checking at the parameter site |
| Logging                    | Rich logging set up by default (opt-out)                               | Not opinionated about logging                                      |
| Dependencies               | `rich`, `rich-argparse` (small footprint)                              | `click`, `rich`, `shellingham`, `typing-extensions`                |
| Maturity / ecosystem       | New and small                                                          | Widely adopted, large ecosystem                                    |
| Best for                   | Single-purpose scripts and tools where the function *is* the CLI       | Multi-command CLIs, distributed apps, anything needing completion  |

If you need nested command groups or shell completion, use typer. If you
want one function = one CLI with minimal ceremony and strict typing — with
`yeet FILE FUNC` covering the simple multi-command case — yeetr is designed
for that.
