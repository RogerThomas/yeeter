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
