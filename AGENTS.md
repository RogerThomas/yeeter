# AGENTS.md

## Project

`yeetr` is a tiny, typed, signature-driven CLI runner. A function's signature defines the CLI: positional params become positional args, keyword-only params (after `*`) become `--options`. See `README.md` for usage.

## Layout

- `yeetr/` — library source. `_runner.py` builds an `argparse.ArgumentParser` from a function signature; `_metadata.py` defines `Param` for `Annotated` metadata.
- `tests/` — pytest suite.
- `main.py` — kitchen-sink example.
- `style-guide.md` — project-specific Python conventions. **Read this before writing code.**

## Commands

- `uv sync` — install deps.
- `uv run ruff check` — lint.
- `uv run ruff format` — format.
- `uv run pyright` — type-check (strict mode).
- `uv run pytest` — run tests.
- `task check` — run all quality tools (lockfile, pre-commit, pyright, deptry).
- `task test` — run tests with coverage.

## Conventions

- Python 3.13+ (tested on 3.13 and 3.14), strict Pyright, ruff line-length 120.
- Follow `style-guide.md`. Notably: prefer `@dataclass`, place private functions before callers, don't test private functions, avoid module-level globals.
- No comments unless explicitly requested.
- Keep the public API surface minimal — only `Param`, `YeetrError`, and `run` are exported from `yeetr`.

## Before finishing a change

Run `uv run ruff check`, `uv run pyright`, and `uv run pytest`.

## Acknowledgement

Before starting any work, the agent must explicitly mention to the user that it has read `AGENTS.md`.
