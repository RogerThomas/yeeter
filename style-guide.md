# Python Style Guide

> **Note**: This style guide is for esoteric, project-specific conventions that are **not** automatically enforced by tools like [Ruff](https://docs.astral.sh/ruff/) or [Pyright](https://github.com/microsoft/pyright).
> It should be kept **minimal and focused**, and not attempt to duplicate or override existing linting/type-checking policies.

> ⚠️ **Company-wide policy** recommends _against_ project-level style guides, in general:
> [Nitro Engineering - Style Guide Recommendations](https://github.com/Nitro/engineering-documentation/blob/221d0de0498152c95c95a21614e3383daf028628/practices/code/styleguides.md?plain=1#L2)
> However, for this project, we maintain this guide for a few nuanced cases that benefit from shared understanding.

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=2 -->

- [1. Prefer `@dataclass` for Class definitions](#1-prefer-dataclass-for-class-definitions)
- [2. Almost never use dict.get](#2-almost-never-use-dictget)
- [3. Use simple test values, not pseudo-realistic ones](#3-use-simple-test-values-not-pseudo-realistic-ones)
- [4. Place private methods/functions before the methods/functions that use them](#4-place-private-methodsfunctions-before-the-methodsfunctions-that-use-them)
- [5. Almost never test private methods/functions](#5-almost-never-test-private-methodsfunctions)
- [6. Use `@dataclass(slots=True)` for internal DTOs](#6-use-dataclassslotstrue-for-internal-dtos)
- [7. Almost never use globals](#7-almost-never-use-globals)
- [8. Prefer operator forms for primitive containers](#8-prefer-operator-forms-for-primitive-containers)
- [9. Use real type expressions in `typing.cast`](#9-use-real-type-expressions-in-typingcast)

<!-- mdformat-toc end -->

______________________________________________________________________

## 1. Prefer `@dataclass` for Class definitions<a name="1-prefer-dataclass-for-class-definitions"></a>

We acknowledge that this is a **slight abuse** of what `dataclass` was originally intended for (pure data containers), but in practice, the benefits — reduced boilerplate, clear structure, and ease of use — outweigh the downsides.

```Python
from dataclasses import dataclass


@dataclass
class Controller:
    _service1: Service1
    _service2: Service2


# Use positional args when using this pattern to avoid doing _thing=thing
controller = Controller(service1, service2)
```

If an attribute needs to be set after instantiation, use `field(init=False)` and use the `__post_init__` method to set it.

## 2. Almost never use dict.get<a name="2-almost-never-use-dictget"></a>

Dictionary `.get` method should only ever be used when a field in a dictionary is optional and you want to provide a default value.
For example, if some API returns a dictionary with an optional field then `dict.get` can be used to elegantly handle the case where the field is not present.
A slightly contrived example would be, maybe an API returns a person object, if they don't have a middle name the api doesn't return this field,
then we can use `dict.get` to provide a default value of None:

```Python
middle_name = person.get("middleName")
```

But if we expect every person to have a first name, then we **must** use.

```Python
first_name = person["firstName"]
```

If the field is required, and the code block can't continue without it, then simply allow a `KeyError` to be raised.
This makes it clear that the code expects the key to be present, and if it is not, it is a bug that should be fixed.
And, in this case, allowing a default and then raising an error does not provide us with any valable additional information about the error and
actually may hinder us by swallowing the stack trace and making it harder to debug.

For example

**Good**

```Python
value = my_dict["key"]
```

**Bad**

```Python
value = my_dict.get("key")
if value is None:
    raise KeyError("Key 'key' is required in dict")
```

## 3. Use simple test values, not pseudo-realistic ones<a name="3-use-simple-test-values-not-pseudo-realistic-ones"></a>

In tests, use simple, obvious values instead of pseudo-realistic ones. This makes tests more readable and maintainable, while pseudo-realistic values add zero benefit.

**Good**

```Python
create_user("first-name", "last-name")
create_user.assert_called_with("first-name", "last-name")
```

**Bad**

```Python
first_name = "John"
last_name = "Doe"
create_user(first_name, last_name)
create_user.assert_called_with(first_name, last_name)
```

The simple approach is clearer and eliminates unnecessary variables that don't contribute to the test's purpose.

Also, only provide minimal values that are required for the test to pass or for the interface of the function/method.

Given the following function:

```Python
def create_token(token_id: str): ...
```

**Good**

```Python
def test_create_token():
    create_token("token-id")
```

**Bad**

```Python
def test_create_token():
    create_token("00000000-0000-0000-0000-000000000000")
```

There is no added value in using a pseudo-realistic value like a UUID when a simple string suffices, even if in normal operation this value would be a UUID (unless that function does some validation that forces it to be a UUID, but in this case, the type hint should then be a UUID and the test should then also pass a UUID).

As a general convention, use the `kebab-case` version of the variable name as the test value. For example, `first_name` becomes `"first-name"`, `last_name` becomes `"last-name"`, `token_id` becomes `"token-id"`, and so on. This keeps test values predictable and trivially derivable from the variable they represent.

Also, prefer inlining these simple test values directly at the call site rather than extracting them into variables or fixtures. A literal like `"user-id"` is more readable inline than a `user_id` fixture or constant — there is no shared construction cost or duplication being eliminated, just unnecessary indirection. Reserve fixtures for values that are non-trivial to construct or genuinely benefit from being shared (see [Section 7](#7-almost-never-use-globals)).

## 4. Place private methods/functions before the methods/functions that use them<a name="4-place-private-methodsfunctions-before-the-methodsfunctions-that-use-them"></a>

Private methods and functions (those prefixed with `_`) should be defined before the public methods that call them. This improves code readability by following a logical flow where dependencies are defined before their usage.

Note: This differs from languages like Java where private methods are typically placed after public methods. PEP 8 doesn't specify ordering for private vs public methods, so this is a project-specific/Nitro convention for Python development.

**Good**

```Python
class DocumentProcessor:
    def _validate_document(self, doc: bytes) -> bool:
        # Private validation logic
        return True

    def _extract_metadata(self, doc: bytes) -> dict:
        # Private extraction logic
        return {}

    def process_document(self, doc: bytes) -> dict:
        if not self._validate_document(doc):
            raise ValueError("Invalid document")
        return self._extract_metadata(doc)
```

**Bad**

```Python
class DocumentProcessor:
    def process_document(self, doc: bytes) -> dict:
        if not self._validate_document(doc):
            raise ValueError("Invalid document")
        return self._extract_metadata(doc)

    def _validate_document(self, doc: bytes) -> bool:
        # Private validation logic
        return True

    def _extract_metadata(self, doc: bytes) -> dict:
        # Private extraction logic
        return {}
```

## 5. Almost never test private methods/functions<a name="5-almost-never-test-private-methodsfunctions"></a>

Private methods and functions (prefixed with `_`) are implementation details. Testing them directly couples tests to internals, making refactoring harder and tests more fragile.

Instead, test the public interface. If a private method has complex logic worth testing, it is a signal it should be extracted into its own public class or function.

## 6. Use `@dataclass(slots=True)` for internal DTOs<a name="6-use-dataclassslotstrue-for-internal-dtos"></a>

When defining internal data transfer objects (DTOs) — structs that carry data between layers within the application — use `@dataclass(slots=True)` rather than a plain `@dataclass`, `NamedTuple`, or Pydantic `BaseModel`.

Slots eliminate the per-instance `__dict__`, reducing memory usage and improving attribute access speed. Based on benchmarks over 10 million iterations:

| Operation             | `dataclass(slots=True)` | `namedtuple`         | `dataclass`          | `pydantic`           |
| --------------------- | ----------------------- | -------------------- | -------------------- | -------------------- |
| Create                | **1316ms** ✓            | 1771ms (1.3x slower) | 1460ms (1.1x slower) | 7781ms (5.9x slower) |
| Attribute access      | **716ms** ✓             | 1080ms (1.5x slower) | 723ms (1.0x slower)  | 1862ms (2.6x slower) |
| Memory (per instance) | **274 B** ✓             | 290 B (1.1x larger)  | 631 B (2.3x larger)  | 1551 B (5.7x larger) |

`@dataclass(slots=True)` is the fastest across all benchmarks. The memory saving is the most significant benefit — slotted dataclasses use roughly the same memory as a `namedtuple` and 2.3x less than a plain `@dataclass`.

```Python
from dataclasses import dataclass


@dataclass(slots=True)
class ParsedDocument:
    document_id: str
    page_count: int
    text: str
```

## 7. Almost never use globals<a name="7-almost-never-use-globals"></a>

Module-level globals (constants, configuration values, or shared state defined outside of a class) are mostly a design smell. They make code harder to test, harder to reason about, and harder to override in different contexts. Prefer encapsulating these values as class attributes (or dependency-injected settings), so that they live alongside the code that uses them and can be substituted in tests or different runtime contexts.

**Good** — values are encapsulated as class attributes:

```Python
class Client:
    _http_client: httpx.Client
    _base_url: str = "http://url/api"
```

**Bad** — values leak into module scope as globals:

```Python
_BASE_URL: str = "http://url/api"


class Client:
    _http_client: httpx.Client
```

Class-based settings (or similar dependency-injected configuration) are preferred over module-level globals. This keeps related state colocated with the class that owns it, makes the dependency surface explicit, and avoids hidden coupling between modules.

In tests, the same principle applies: prefer pytest fixtures over module-level globals for shared test setup that is non-trivial to construct. Fixtures make dependencies explicit at the test signature level, support scoping (function/module/session), and can be overridden or parametrized — all of which globals cannot. (For trivial values like a single string, inline them at the call site instead — see [Section 3](#3-use-simple-test-values-not-pseudo-realistic-ones).)

**Good** — shared test setup is exposed via a fixture:

```Python
@pytest.fixture(name="parsed_document")
def _parsed_document() -> ParsedDocument:
    return ParsedDocument(document_id="document-id", page_count=1, text="text")


def test_something(parsed_document: ParsedDocument):
    ...
```

**Bad** — shared test setup defined as a module-level global:

```Python
_PARSED_DOCUMENT = ParsedDocument(document_id="document-id", page_count=1, text="text")


def test_something():
    # implicitly depends on _PARSED_DOCUMENT
    ...
```

## 8. Prefer operator forms for primitive containers<a name="8-prefer-operator-forms-for-primitive-containers"></a>

When combining primitive containers such as lists, sets, and dictionaries, prefer the operator form over the method form when the meaning is equivalent.

**Good**

```Python
items += more_items
seen |= new_items
config |= overrides
```

**Bad**

```Python
items.extend(more_items)
seen.update(new_items)
config.update(overrides)
```

This keeps container-combination code compact and visually consistent with Python's literal syntax. Keep using methods when they communicate a different operation more clearly, such as `items.append(item)` for adding one element or `mapping[key] = value` for setting one key.

## 9. Use real type expressions in `typing.cast`<a name="9-use-real-type-expressions-in-typingcast"></a>

When calling `typing.cast`, pass the actual type expression rather than a string literal, unless avoiding a runtime import or a true forward reference is necessary.

**Good**

```Python
value = typing.cast(list[str], raw)
```

**Bad**

```Python
value = typing.cast("list[str]", raw)
```

This keeps casts aligned with normal Python type syntax and avoids hiding misspelled or stale type expressions inside strings.
