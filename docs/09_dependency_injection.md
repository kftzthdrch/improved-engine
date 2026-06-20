# Chapter 09: Dependency Injection

## Learning Objective

Understand FastAPI's `Depends()` system, how `app/api/dependencies.py` bridges the HTTP layer and the composition container, and how dependency overrides enable isolated testing.

---

## What Dependency Injection Is

Dependency injection means that a function or class declares *what it needs* rather than creating it internally. Something external provides the dependencies.

In FastAPI, dependency injection happens via `Depends()`. A route handler declares `use_case=Depends(get_lock_vehicle_use_case)` instead of constructing the use case itself. FastAPI calls `get_lock_vehicle_use_case` and passes the result as `use_case`.

This gives you three benefits:

1. **Testability** — you can replace any dependency with a stub or mock.
2. **Separation** — routes do not know how use cases are constructed.
3. **Consistency** — the same use case instance is used for every request (constructed once at startup in the container).

---

## The Container on app.state

The `Container` is created once during app startup by the lifespan function:

```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container()
    yield
```

`app.state` is a simple attribute bag that FastAPI makes available on every request via `request.app`. The container instance lives for the entire lifetime of the process — it is not created per request.

---

## Provider Functions in dependencies.py

File: `app/api/dependencies.py`

Provider functions extract use cases from the container. Each function takes a `Request`, reads `app.state.container`, and returns the appropriate use case instance:

```python
from fastapi import Request
from app.composition.container import Container

def get_container(request: Request) -> Container:
    return request.app.state.container

def get_lock_vehicle_use_case(request: Request):
    return get_container(request).lock_vehicle

def get_unlock_vehicle_use_case(request: Request):
    return get_container(request).unlock_vehicle

def get_ingest_telemetry_use_case(request: Request):
    return get_container(request).ingest_telemetry

# ... 20+ more provider functions
```

These functions are the glue between the HTTP layer and the composition root. They are the only code in `app/api/` that touches `Container`.

---

## How Depends() Resolves the Chain

When FastAPI sees `use_case=Depends(get_lock_vehicle_use_case)` in a route signature, it:

1. Inspects the signature of `get_lock_vehicle_use_case`.
2. Sees it takes `request: Request`.
3. Injects the current HTTP `Request` automatically.
4. Calls the function and receives the `LockVehicleUseCase` instance.
5. Passes it to the route handler as `use_case`.

The route handler never sees `Request`, `Container`, or `InMemoryCommandRepository`. It only sees the use case.

```python
# Route handler — only knows about the use case
@router.post("/vehicles/{vehicle_id}/commands/lock", response_model=CommandResponse, status_code=200)
def lock_vehicle(vehicle_id: str = Path(...), use_case=Depends(get_lock_vehicle_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)
```

---

## Why Routes Depend on Use Cases, Not Repositories

Route handlers receive use cases via `Depends()`. They do not receive repositories directly.

This is important because:

- A use case encapsulates a business operation including policy checks, gateway calls, and persistence. A repository only stores and retrieves.
- If a route depended on a repository directly, it would need to know which repository methods to call and in which order — that is business logic leaking into the API layer.
- Swapping the repository implementation (e.g., from in-memory to SQLAlchemy) requires no change to routes because routes only depend on use cases, which depend on port protocols.

The one exception is `get_command_by_id_use_case` in `app/api/dependencies.py`:

```python
def get_command_by_id_use_case(request: Request):
    return get_container(request).command_repo
```

This returns the repository directly. The `get_command` route uses it to look up a command by ID without a dedicated use case class. This is a pragmatic simplification — a read-only lookup with no business logic. In a stricter design you would have a `GetCommandByIdUseCase`.

---

## Dependency Override in Tests

FastAPI's `app.dependency_overrides` dictionary lets you replace any provider function with a stub for a specific test:

```python
# tests/integration/api/test_dependency_override.py

from fastapi.testclient import TestClient
from app.main import create_app
from app.api.dependencies import get_lock_vehicle_use_case

def test_dependency_override():
    app = create_app()

    class StubLockUseCase:
        def execute(self, vehicle_id):
            return make_stub_command()

    app.dependency_overrides[get_lock_vehicle_use_case] = lambda: StubLockUseCase()

    with TestClient(app) as client:
        r = client.post("/vehicles/VH-TEST/commands/lock")

    assert r.status_code == 200
    assert r.json()["id"] == "stub-id"
    assert r.json()["status"] == "SUCCEEDED"
```

`dependency_overrides` is a dict mapping a provider function to a replacement callable. When FastAPI resolves `Depends(get_lock_vehicle_use_case)`, it checks this dict first. If an override exists, it calls the override instead.

This lets you test the HTTP layer (routing, schema serialization, response codes) in isolation from the business logic.

After the `with TestClient(app)` block the overrides apply to that app instance only. If you call `create_app()` in a new test, the overrides are not present.

---

## Dependency Scope and Lifecycle

In this project, use cases are created once at startup (inside `Container.__init__`) and reused for every request. They are not created per request.

This works because the use cases are stateless — they hold references to repositories and services but do not store request-specific data. The repositories hold state (the in-memory dicts), but those are also singletons shared across all requests. This is correct for an in-memory application where the data lives for the life of the process.

If you added a database with connection pooling, you would likely want the session/connection to be created per request. That would require changing the dependency providers to create a new session each time, while keeping the use case instantiation approach or creating use cases per request too.

---

## Visualizing the Dependency Chain

```text
HTTP Request
     │
     ▼
FastAPI resolves Depends(get_lock_vehicle_use_case)
     │
     ▼
get_lock_vehicle_use_case(request) reads request.app.state.container
     │
     ▼
container.lock_vehicle  (LockVehicleUseCase instance, created at startup)
     │
     ▼
route handler receives use_case
     │
     ▼
use_case.execute(VehicleId(vehicle_id))
     │
     ▼
LockVehicleUseCase calls:
  command_repo (InMemoryCommandRepository)
  telemetry_repo (InMemoryTelemetryRepository)
  gateway (FakeVehicleCommandGateway)
  clock (SystemClock)
  id_gen (UuidGenerator)
  policy (CommandPolicy)
```

---

## Anti-Patterns to Avoid

**Creating use cases inside route handlers.** If a route called `LockVehicleUseCase(...)` directly, it would import infrastructure classes into the API layer, violating the architecture rules, and create a new use case instance per request.

**Using global module-level variables for use cases.** The composition container on `app.state` is the right place. Module-level globals cannot be replaced per-test and create hidden coupling between modules.

**Bypassing `Depends()` by calling provider functions directly.** Provider functions require a `Request` object. Calling them outside of a route context (e.g., in a background task) requires passing a mock request, which is fragile.

**Not clearing `dependency_overrides` between tests.** If tests share an `app` instance, overrides from one test can bleed into another. Always use a fresh `create_app()` per test, or clear `app.dependency_overrides` explicitly.

---

## Exercises

1. Add a new provider function `get_health_use_case` to `app/api/dependencies.py` that returns a simple object with an `execute()` method returning `{"status": "ok"}`. Wire it into `app/api/routes/health.py` using `Depends()`. Confirm the health endpoint still works.

2. Write a test using `dependency_overrides` that replaces `get_ingest_telemetry_use_case` with a stub that always raises `InvalidCommandError("speed cannot be negative")`. Assert the HTTP response is 400 with the correct error body.

3. Set a breakpoint (or add a print) inside `get_lock_vehicle_use_case`. Run `pytest tests/integration/api/test_commands.py -k test_lock_succeeds_when_stopped`. Confirm the provider function is called exactly once per request.

---

## Review Checklist

- [ ] I understand what `Depends()` does and when FastAPI calls the provider function.
- [ ] I know where `app.state.container` is set and why it is done in the lifespan.
- [ ] I can write a `dependency_overrides` test for any route in the project.
- [ ] I understand why routes depend on use cases rather than repositories directly.
- [ ] I can trace the full dependency chain from HTTP request to repository call.
