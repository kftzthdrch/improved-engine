# Chapter 14: Architecture Tests

## Learning Objective

Understand the three architecture test files in `tests/architecture/`, how they use Python's `ast` module to enforce import rules without running the code, and why automated architecture enforcement is valuable.

---

## Why Architecture Tests?

Architecture rules are easy to state and easy to violate accidentally. "The domain layer must not import FastAPI" is a clear rule, but nothing in Python prevents you from writing `from fastapi import FastAPI` anywhere — the interpreter will happily run it.

Code review can catch violations, but:

- Code review is manual and error-prone.
- A reviewer might not notice a deeply nested import.
- In a team, different reviewers may apply the rules inconsistently.
- In a learning project, a beginner might not know the rules yet.

Architecture tests make the rules machine-checkable. When the test suite runs in CI, any violation causes an immediate, explicit failure with the name of the offending file.

---

## How the Tests Work

All three architecture test files share the same `ast`-based scanning approach:

```python
import ast
import os

def get_python_files(base_dir: str) -> list[str]:
    files = []
    for root, _, filenames in os.walk(base_dir):
        for f in filenames:
            if f.endswith('.py'):
                files.append(os.path.join(root, f))
    return files

def get_imports(filepath: str) -> list[str]:
    with open(filepath, encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports
```

`ast.parse()` builds an Abstract Syntax Tree from the source text — it parses Python without executing it. `ast.walk()` visits every node in the tree. `ast.Import` matches `import fastapi`. `ast.ImportFrom` matches `from fastapi import FastAPI` (the `node.module` would be `"fastapi"`).

The result is a flat list of all imported module names for a given file.

---

## test_forbidden_imports.py

File: `tests/architecture/test_forbidden_imports.py`

This is the most important architecture test. It enforces the core hexagonal architecture rule: the inner layers must not import from the outer layers or from frameworks.

```python
DOMAIN_DIR = os.path.join(BASE, 'app', 'domain')
APP_DIR = os.path.join(BASE, 'app', 'application')

def test_domain_does_not_import_fastapi():
    for fp in get_python_files(DOMAIN_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('fastapi'), f"{fp} imports fastapi"

def test_domain_does_not_import_pydantic():
    for fp in get_python_files(DOMAIN_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('pydantic'), f"{fp} imports pydantic"

def test_domain_does_not_import_infrastructure():
    for fp in get_python_files(DOMAIN_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.infrastructure'), f"{fp} imports infrastructure"

def test_domain_does_not_import_api():
    for fp in get_python_files(DOMAIN_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.api'), f"{fp} imports api"

def test_application_does_not_import_fastapi():
    for fp in get_python_files(APP_DIR):
        ...

def test_application_does_not_import_pydantic():
    for fp in get_python_files(APP_DIR):
        ...

def test_application_does_not_import_infrastructure():
    for fp in get_python_files(APP_DIR):
        ...

def test_application_does_not_import_api():
    for fp in get_python_files(APP_DIR):
        ...
```

Eight tests covering two layers (domain, application) and four forbidden import categories (fastapi, pydantic, infrastructure, api). If any file in either layer imports any of the forbidden modules, the test fails with the full file path in the error message.

---

## test_no_database_dependencies.py

File: `tests/architecture/test_no_database_dependencies.py`

```python
FORBIDDEN = ['sqlalchemy', 'alembic', 'sqlite', 'postgres', 'psycopg', 'asyncpg', 'redis', 'pymongo']

BASE = os.path.join(os.path.dirname(__file__), '..', '..')
APP_DIR = os.path.join(BASE, 'app')

@pytest.mark.parametrize("forbidden", FORBIDDEN)
def test_no_database_imports(forbidden):
    for fp in get_python_files(APP_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert forbidden not in imp, f"{fp} imports forbidden package: {forbidden}"
```

This test scans the entire `app/` directory (not just domain and application). Even `app/infrastructure/` is included — the project's constraint is that no database is used anywhere, not just in the core layers.

`@pytest.mark.parametrize("forbidden", FORBIDDEN)` generates eight separate test cases, one per forbidden package. When you run `pytest tests/architecture/`, you see each as a separate pass or fail:

```text
PASSED tests/architecture/test_no_database_dependencies.py::test_no_database_imports[sqlalchemy]
PASSED tests/architecture/test_no_database_dependencies.py::test_no_database_imports[alembic]
...
```

Note that `get_imports` lowercases all module names before checking. This catches imports like `import SQLAlchemy` (unusual but possible).

---

## test_layer_direction.py

File: `tests/architecture/test_layer_direction.py`

```python
INFRA_DIR = os.path.join(BASE, 'app', 'infrastructure')

def test_infrastructure_does_not_import_api():
    for fp in get_python_files(INFRA_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.api'), f"{fp} imports api from infrastructure"

def test_infrastructure_does_not_import_composition():
    for fp in get_python_files(INFRA_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.composition'), f"{fp} imports composition from infrastructure"
```

This enforces that infrastructure adapters do not reach into the API layer or the composition root. Infrastructure adapters implement ports; they should not know about routers, schemas, or the container.

---

## The Full Rule Set Enforced

| Rule | Test file | Test function |
| ---- | --------- | ------------- |
| Domain does not import fastapi | `test_forbidden_imports.py` | `test_domain_does_not_import_fastapi` |
| Domain does not import pydantic | `test_forbidden_imports.py` | `test_domain_does_not_import_pydantic` |
| Domain does not import infrastructure | `test_forbidden_imports.py` | `test_domain_does_not_import_infrastructure` |
| Domain does not import api | `test_forbidden_imports.py` | `test_domain_does_not_import_api` |
| Application does not import fastapi | `test_forbidden_imports.py` | `test_application_does_not_import_fastapi` |
| Application does not import pydantic | `test_forbidden_imports.py` | `test_application_does_not_import_pydantic` |
| Application does not import infrastructure | `test_forbidden_imports.py` | `test_application_does_not_import_infrastructure` |
| Application does not import api | `test_forbidden_imports.py` | `test_application_does_not_import_api` |
| No database imports anywhere in app/ | `test_no_database_dependencies.py` | `test_no_database_imports[sqlalchemy]` (×8) |
| Infrastructure does not import api | `test_layer_direction.py` | `test_infrastructure_does_not_import_api` |
| Infrastructure does not import composition | `test_layer_direction.py` | `test_infrastructure_does_not_import_composition` |

---

## Limitations of ast-Based Scanning

The `ast` approach has a few known limitations:

**Dynamic imports are not caught.** `importlib.import_module("fastapi")` would not be detected because the `fastapi` string is not an AST import node — it is a string literal passed to a function.

**Relative imports within the same package** are collapsed to their full module path by Python at runtime, but `ast.parse` sees them as relative. The tests check for absolute module names like `app.infrastructure`, so intra-domain relative imports (e.g., `from .errors import DomainError`) are not flagged.

**Re-exports are not tracked.** If `app/domain/__init__.py` re-exported something from `app/infrastructure/`, the test would catch the import in `__init__.py` but not in files that import from `app/domain` (they see it as a domain import).

For this project's learning purposes, these limitations are acceptable. In production systems, tools like `import-linter`, `pydeps`, or `pylint` plugins provide more robust import analysis.

---

## Adding a New Architecture Rule

To add a rule that the `app/api/` layer must not import from `app/composition/` directly:

```python
# tests/architecture/test_layer_direction.py

API_DIR = os.path.join(BASE, 'app', 'api')

def test_api_does_not_import_composition_directly():
    for fp in get_python_files(API_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.composition'), \
                f"{fp} imports composition — use Depends() instead"
```

Adding this rule makes `app/api/dependencies.py` fail immediately (it imports `Container` from `app.composition.container`). You would need to decide whether to allow that one file (by adding an exception) or restructure so that `dependencies.py` does not need to import `Container` by name.

---

## Anti-Patterns to Avoid

**Skipping architecture tests in CI.** These tests are only valuable if they run on every commit. Skipping them in CI means violations accumulate silently.

**Hardcoding file paths in tests.** The tests use `os.path.join` and `os.path.dirname(__file__)` to build paths relative to the test file. This makes them portable across operating systems and project locations.

**Only checking top-level imports.** `ast.walk` traverses the entire tree, including imports inside functions and `if` blocks. An `import fastapi` inside a function is still caught.

---

## Exercises

1. Add `import fastapi` to `app/domain/errors.py`. Run `pytest tests/architecture/test_forbidden_imports.py`. Read the failure message carefully — it includes the file path. Remove the import and confirm tests pass.

2. Add a new architecture test: `test_domain_does_not_import_application`. Scan `app/domain/` and assert no file imports `app.application`. Run it. Confirm it passes (the domain does not import from the application layer).

3. Extend `test_no_database_dependencies.py` to also forbid `motor` (async MongoDB driver) and `tortoise` (async ORM). Add them to the `FORBIDDEN` list and run the tests.

---

## Review Checklist

- [ ] I can explain how `ast.parse()` and `ast.walk()` are used to scan imports.
- [ ] I can state all 11 rules currently enforced by the architecture tests.
- [ ] I understand the limitation: dynamic imports via `importlib` are not caught.
- [ ] I can add a new architecture test rule by following the existing pattern.
- [ ] I know why these tests are valuable even when code review exists.
