# CLI Rules

- **Positional** parameters become positional CLI args.
- **Keyword-only** parameters (after `*`) become `--options`.
- Names convert from `snake_case` to `kebab-case` for CLI flags.
- One-letter option names become short flags (`n` -> `-n`).
- `flag: bool = False` becomes `--flag`.
- `flag: bool = True` becomes `--no-flag`.
- Required `bool` parameters raise a clear error.
- `T | None` / `Optional[T]` are accepted; treated as their inner type with
  `None` as default.
- `list[T]` becomes a repeated option (`--tag a --tag b`).
- `tuple[T, U]` consumes a fixed number of values.
- `tuple[T, ...]` consumes a variable number of values.
- `Enum` subclasses parse from member values and are rendered as choices.
- `datetime`/`date`/`time` parse ISO 8601 strings; `UUID` and `Decimal`
  parse their standard string forms.
- `*args: T` becomes a trailing variadic positional argument; `Arg(min=1)`
  requires at least one value.
- A single `dataclass`/`NamedTuple` parameter is unpacked into the CLI: its
  `Arg` fields become positional args, everything else becomes `--options`.
- `Opt(envvar="NAME")` falls back to an environment variable when the flag
  is omitted.
- `Opt(hidden=True)` still parses but is hidden from `--help`.
- `exists`/`file_okay`/`dir_okay`/`readable`/`writable` validate `Path`
  parameters (and `Path`-typed lists, tuples, and `*args`) at parse time.
