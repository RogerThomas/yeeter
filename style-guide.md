# Python Style Guide

> **Note**: This style guide is for esoteric, project-specific conventions that are **not** automatically enforced by tools like [Ruff](https://docs.astral.sh/ruff/) or [Pyright](https://github.com/microsoft/pyright).
> It should be kept **minimal and focused**, and not attempt to duplicate or override existing linting/type-checking policies.

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=2 -->

- [1. Prefer `@dataclass` for Class definitions](#1-prefer-dataclass-for-class-definitions)
- [2. Almost never use dict.get](#2-almost-never-use-dictget)
- [3. On tests, prefer passing fixture name instead of file bytes](#3-on-tests-prefer-passing-fixture-name-instead-of-file-bytes)
- [4. Use simple test values, not pseudo-realistic ones](#4-use-simple-test-values-not-pseudo-realistic-ones)
- [5. Place private methods/functions before the methods/functions that use them](#5-place-private-methodsfunctions-before-the-methodsfunctions-that-use-them)
- [6. Configuration and service settings](#6-configuration-and-service-settings)
  - [When to use configuration vs. service settings](#when-to-use-configuration-vs-service-settings)
- [7. Almost never test private methods/functions](#7-almost-never-test-private-methodsfunctions)
- [8. Use `@dataclass(slots=True)` for internal DTOs](#8-use-dataclassslotstrue-for-internal-dtos)
- [9. Use `create_autospec` for mocking in tests](#9-use-create_autospec-for-mocking-in-tests)
- [10. Almost never use globals](#10-almost-never-use-globals)
- [11. Prefer operators over mutating method calls](#11-prefer-operators-over-mutating-method-calls)
- [12. Almost never use nested functions or classes](#12-almost-never-use-nested-functions-or-classes)

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

## 3. On tests, prefer passing fixture name instead of file bytes<a name="3-on-tests-prefer-passing-fixture-name-instead-of-file-bytes"></a>

When a test fails with a bytes parameter, using actual file bytes, the resulting pytest logs become hard to read.
Instead, pass the name of the fixture itself then load the fixture value inside the test function.

For example

**Good**

```Python
def test_example(fixture_name: str, request: pytest.FixtureRequest):
    # Instead of using file_bytes directly, use the fixture name
    file_bytes = request.getfixturevalue(fixture_name)
    #...
    assert file_bytes == b"expected bytes"
```

**Bad**

```Python
def test_example(file_bytes: bytes):
    # Using file_bytes directly
    assert file_bytes == b"expected bytes"
```

## 4. Use simple test values, not pseudo-realistic ones<a name="4-use-simple-test-values-not-pseudo-realistic-ones"></a>

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

Also, prefer inlining these simple test values directly at the call site rather than extracting them into variables or fixtures. A literal like `"user-id"` is more readable inline than a `user_id` fixture or constant — there is no shared construction cost or duplication being eliminated, just unnecessary indirection. Reserve fixtures for values that are non-trivial to construct or genuinely benefit from being shared (see [Section 10](#10-almost-never-use-globals)).

## 5. Place private methods/functions before the methods/functions that use them<a name="5-place-private-methodsfunctions-before-the-methodsfunctions-that-use-them"></a>

Private methods and functions (those prefixed with `_`) should be defined before the public methods that call them. This improves code readability by following a logical flow where dependencies are defined before their usage.

Note: This differs from languages like Java where private methods are typically placed after public methods. PEP 8 doesn't specify ordering for private vs public methods, so this is a project-specific convention for Python development.

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

## 6. Configuration and service settings<a name="6-configuration-and-service-settings"></a>

Configuration should be decoupled from service settings. This separation provides several key benefits:

- **Testability**: Services can be tested in isolation with explicit settings instances, without requiring a full configuration system or environment variables
- **Flexibility**: Services can have sensible hardcoded defaults while still allowing environment-specific overrides when needed
- **Clarity**: The distinction between service-level behavior and environment-specific configuration becomes explicit
- **Maintainability**: Changes to service defaults don't require touching configuration files, and vice versa

### When to use configuration vs. service settings<a name="when-to-use-configuration-vs-service-settings"></a>

Settings should only be pulled from the central configuration system **if and when** those values need to vary between environments (local-dev, dev, prod).

For all other settings, it is perfectly acceptable—and preferred—to define sensible defaults directly in the service's settings class. These defaults can be overridden from configuration if the need arises in the future.

**Good**

```Python
@dataclass
class MyServiceSettings:
    """Settings for MyService"""

    # Environment-specific: varies between local/dev/prod
    max_file_size_mb: float

    # Service-specific: sensible default, same across all environments
    chunk_size: int = 1000
    chunk_overlap: int = 100
    temperature: float = 0.0
```

```Python
class Settings(BaseModel):
    my_service: MyServiceSettings
    # ... other settings

typed_settings = Settings(
    my_service=MyServiceSettings(
        max_file_size_mb=_get_float_setting("my_service.max_file_size_mb"),
        # chunk_size, chunk_overlap, temperature use their defaults
    ),
)
```

**Bad**

```Python
# Putting everything in config when most values never change
@dataclass
class MyServiceSettings:
    max_file_size_mb: float
    chunk_size: int  # Same in all environments
    chunk_overlap: int  # Same in all environments
    temperature: float  # Same in all environments

# api/config/settings.yaml - unnecessary duplication across environments
default:
  my_service:
    max_file_size_mb: 100
    chunk_size: 1000
    chunk_overlap: 100
    temperature: 0.0

dev:
  my_service:
    max_file_size_mb: 250
    chunk_size: 1000  # Duplicated
    chunk_overlap: 100  # Duplicated
    temperature: 0.0  # Duplicated
```

This approach keeps configuration files focused on what actually varies between environments, while keeping service logic and its sensible defaults colocated in the service code.

## 7. Almost never test private methods/functions<a name="7-almost-never-test-private-methodsfunctions"></a>

Private methods and functions (prefixed with `_`) are implementation details. Testing them directly couples tests to internals, making refactoring harder and tests more fragile.

Instead, test the public interface. If a private method has complex logic worth testing, it is a signal it should be extracted into its own public class or function.

We use dependency injection throughout the codebase, which makes this straightforward. Dependencies are injected via the constructor and replaced with mocks in tests. Use mock assertions (e.g. `assert_called_once_with`) to verify a component interacts with its dependencies correctly, without reaching into private implementation details.

**Good** — inject the mock handler as a fixture, assert on its interactions:

```Python
@pytest.fixture(name="handler_mock")
def _handler_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.create_autospec(Handler)

@pytest.fixture(name="service")
def _service(handler_mock: MagicMock) -> Service:
    return Service(handler_mock)

def test_service_calls_handler_with_correct_args(
    service: Service,
    handler_mock: MagicMock,
):
    service.process("input")

    handler_mock.handle.assert_called_once_with("input")
```

**Bad** — accessing the private dependency directly instead of using the injected mock:

```Python
def test_service_calls_handler_with_correct_args(service: Service):
    service.process("input")

    service._handler.handle.assert_called_once_with("input")  # Accessing internals
```

## 8. Use `@dataclass(slots=True)` for internal DTOs<a name="8-use-dataclassslotstrue-for-internal-dtos"></a>

When defining internal data transfer objects (DTOs) — structs that carry data between layers within the application — use `@dataclass(slots=True)` rather than a plain `@dataclass`, `NamedTuple`, or Pydantic `BaseModel`.

Slots eliminate the per-instance `__dict__`, reducing memory usage and improving attribute access speed. Based on benchmarks over 10 million iterations:

| Operation             | `dataclass(slots=True)` | `namedtuple`         | `dataclass`          | `pydantic`           |
| --------------------- | ----------------------- | -------------------- | -------------------- | -------------------- |
| Create                | **1316ms** ✓            | 1771ms (1.3x slower) | 1460ms (1.1x slower) | 7781ms (5.9x slower) |
| Attribute access      | **716ms** ✓             | 1080ms (1.5x slower) | 723ms (1.0x slower)  | 1862ms (2.6x slower) |
| Memory (per instance) | **274 B** ✓             | 290 B (1.1x larger)  | 631 B (2.3x larger)  | 1551 B (5.7x larger) |

`@dataclass(slots=True)` is the fastest across all benchmarks. The memory saving is the most significant benefit — slotted dataclasses use roughly the same memory as a `namedtuple` and 2.3x less than a plain `@dataclass`.

**Pydantic should still be used at I/O boundaries** (router request/response models, external API payloads, config deserialization) where validation, serialization, and schema generation are needed. For everything in between — data passed between services, controllers, and internal helpers — prefer `@dataclass(slots=True)`.

```Python
from dataclasses import dataclass


@dataclass(slots=True)
class ParsedDocument:
    document_id: str
    page_count: int
    text: str
```

## 9. Use `create_autospec` for mocking in tests<a name="9-use-create_autospec-for-mocking-in-tests"></a>

Always use `create_autospec(Thing, spec_set=True, instance=True)` when creating mocks, rather than `MagicMock()` or `mocker.MagicMock()`.

- **`spec_set=True`**: Raises `AttributeError` if you access or set an attribute that doesn't exist on the real class — catches typos in attribute/method names at test time rather than silently passing.
- **`instance=True`**: Creates a mock that behaves like an _instance_ of the class, not the class itself (correct `isinstance` checks, correct method signatures).
- **Auto-specced methods**: All method mocks automatically enforce the real method's signature, so calls with wrong arguments fail immediately.

```Python
@pytest.fixture(name="handler_mock")
def _handler_mock() -> MagicMock:
    return create_autospec(Handler, spec_set=True, instance=True)
```

**Bad** — `MagicMock()` silently accepts any attribute or call signature:

```Python
@pytest.fixture(name="handler_mock")
def _handler_mock() -> MagicMock:
    return MagicMock()  # typos in method names go undetected
```

## 10. Almost never use globals<a name="10-almost-never-use-globals"></a>

Module-level globals (constants, configuration values, or shared state defined outside of a class) are mostly a design smell. They make code harder to test, harder to reason about, and harder to override in different contexts. Prefer encapsulating these values as class attributes (or dependency-injected settings), so that they live alongside the code that uses them and can be substituted in tests or different runtime contexts.

**Exception — infrastructure singletons.** Stateless, process-wide infrastructure objects are fine at module level: a rich `Console()`, a `logger = logging.getLogger(__name__)`, and similar. These are write-only sinks with no behavior worth substituting per-instance, and threading them through every constructor adds noise without improving testability.

```Python
# Fine at module level
console = Console()
logger = logging.getLogger(__name__)
```

The rule targets *data and configuration* globals (URLs, lookup tables, default values, mutable state) — not logging/output plumbing.

**Good** — values are encapsulated as class attributes:

```Python
class Client:
    _http_client: niquests.Session
    _base_url: str = "http://url/api"
```

**Bad** — values leak into module scope as globals:

```Python
_BASE_URL: str = "http://url/api"


class Client:
    _http_client: niquests.Session
```

Class-based settings (or similar dependency-injected configuration) are preferred over module-level globals. This keeps related state colocated with the class that owns it, makes the dependency surface explicit, and avoids hidden coupling between modules.

In tests, the same principle applies: prefer pytest fixtures over module-level globals for shared test setup that is non-trivial to construct. Fixtures make dependencies explicit at the test signature level, support scoping (function/module/session), and can be overridden or parametrized — all of which globals cannot. (For trivial values like a single string, inline them at the call site instead — see [Section 4](#4-use-simple-test-values-not-pseudo-realistic-ones).)

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

## 11. Prefer operators over mutating method calls<a name="11-prefer-operators-over-mutating-method-calls"></a>

When extending or merging built-in collections, prefer the operator form over the equivalent method call: `+=` over `list.extend`, `|=` over `dict.update` and `set.update`, and `|` over `{**a, **b}` or copy-then-update when building a new dict/set.

Operators are more concise, read as a single expression, and make the intent (combine these collections) immediately visible without scanning for a method name. The semantics are equivalent for these cases.

**Good**

```Python
items += extra_items

settings |= overrides

merged = defaults | overrides
```

**Bad**

```Python
items.extend(extra_items)

settings.update(overrides)

merged = {**defaults, **overrides}
```

Note that the augmented forms (`+=`, `|=`) accept any iterable/mapping on the right-hand side, exactly like `extend`/`update`, so they are drop-in replacements. Only the binary forms (`a + b`, `a | b`) require both operands to be the same built-in type — convert the operand first if needed.

## 12. Almost never use nested functions or classes<a name="12-almost-never-use-nested-functions-or-classes"></a>

Avoid defining `def`, `class`, or `lambda` inside another function. They are harder to test (you cannot import or call them directly), they hide their captured state in closure cells instead of explicit attributes (so tracebacks show opaque `<locals>` frames and the dependencies of the inner callable are invisible at a glance), and they push function bodies toward being long and hard to scan.

Prefer a module-level function, or — when the thing needs to capture state and be invoked later — a small class that holds that state as explicit attributes and exposes a `__call__` (or named methods). The state becomes inspectable, the unit is testable in isolation, and the "factory + specialized callable" pattern reads as ordinary OO.

This is especially the shape to reach for when a factory builds a configured callable once and invokes it many times: resolve the configuration in `__init__`, do the work in `__call__`.

**Bad** — a factory returning a closure; the captured `prefix`/`suffix` live in invisible cells:

```Python
def make_wrapper(prefix: str, suffix: str) -> Callable[[str], str]:
    def wrap(value: str) -> str:
        return f"{prefix}{value}{suffix}"

    return wrap
```

**Good** — the captured state is explicit and the unit is testable on its own:

```Python
@dataclass(slots=True)
class Wrapper:
    prefix: str
    suffix: str

    def __call__(self, value: str) -> str:
        return f"{self.prefix}{value}{self.suffix}"
```

The "almost" covers the genuinely trivial, single-use, local callable where promotion adds only noise — most commonly a `key=`/`predicate` passed inline to a builtin:

```Python
names.sort(key=lambda person: person.age)
```

If the inner callable closes over state, is reused, is more than a line or two, or would benefit from a test, promote it. Note this rule is about `def`/`class`/`lambda` nesting — comprehensions and generator expressions are not "nested functions" and are unaffected.
