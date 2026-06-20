# Chapter 15: Lifespan and App Factory

## Learning Objective

Understand the `create_app()` factory pattern, the lifespan async context manager, why `app.state.container` exists, and how `TestClient` interacts with the lifespan correctly.

---

## The App Factory Pattern

File: `app/main.py`

```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="Automotive Vehicle Command & Telematics Service",
        description="A hexagonal architecture learning project using FastAPI",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    static_dir = os.path.join(os.path.dirname(__file__), "ui", "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(health.router)
    app.include_router(ui.router)
    app.include_router(commands.router)
    app.include_router(telemetry.router)
    app.include_router(eligibility.router)
    app.include_router(alerts.router)
    app.include_router(trips.router)
    app.include_router(maintenance.router)
    app.include_router(diagnostics.router)

    return app
```

`create_app()` is a function that returns a configured `FastAPI` instance. This is called the "application factory" pattern.

### Why a Factory and Not a Module-Level Variable?

The alternative is:

```python
# Alternative (not used in this project)
app = FastAPI(...)
```

If `app` were a module-level variable, importing `app.main` would immediately create the application and start the lifespan — even in test files. The same `app` instance would be shared across all tests. State (the container, the repositories) would persist between tests.

With `create_app()`:

- Each test calls `create_app()` and gets a fresh `FastAPI` instance with a fresh `Container` and empty repositories.
- Tests are isolated from each other.
- You can call `create_app()` with different configuration in different environments (test, staging, production) by passing parameters.
- The module can be imported without side effects.

---

## The Lifespan Context Manager

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container()   # startup
    yield
    # shutdown code would go here
```

`@asynccontextmanager` turns a generator function into an async context manager. When FastAPI starts the application, it enters the context manager:

1. Everything before `yield` runs at startup.
2. The `yield` suspends the context manager — the app is now running and handling requests.
3. When the app shuts down, everything after `yield` runs.

In this project, startup creates the `Container` and stores it on `app.state`. Shutdown has no explicit work to do (no database connections to close, no background threads to stop).

### Why app.state?

`app.state` is a `starlette.datastructures.State` object — a simple attribute bag provided by FastAPI/Starlette. It is accessible on every request via `request.app.state`.

Any name can be used: `app.state.container`, `app.state.db`, `app.state.cache`. The name `container` is chosen because the object is the dependency injection container.

`app.state` is the idiomatic FastAPI way to share per-application state with request handlers. The alternative — module-level globals — would break test isolation.

---

## Container Creation: Once Per Process

`Container()` is called once, in the lifespan startup. All 25 use cases, 6 repositories, 1 gateway, 1 clock, and 1 ID generator are created at that moment.

This means:

- Repository instances are singletons — all requests share the same in-memory dictionaries.
- A telemetry record saved by one request is immediately visible to the next request.
- This is the correct behavior for an in-memory application.

If you added a database later and needed a per-request database session, you would change the dependency providers (not the lifespan) to create a session per request.

---

## TestClient and the Lifespan

`TestClient` from `fastapi.testclient` is a synchronous HTTP client that calls into the ASGI application directly without starting a network socket.

**Correct usage:**

```python
@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
```

The `with TestClient(app) as c:` context manager:

1. Calls `app.__aenter__()` — triggers the lifespan startup.
2. `app.state.container = Container()` runs.
3. The `yield c` line provides the client to the test.
4. After the test, `app.__aexit__()` runs — triggers the lifespan shutdown.

**Incorrect usage:**

```python
# Wrong — lifespan does not run
client = TestClient(create_app())
```

Without `with`, the `__aenter__` and `__aexit__` are never called. The lifespan never runs. `app.state.container` does not exist. The first request to any route that calls `request.app.state.container` raises `AttributeError: 'State' object has no attribute 'container'`.

---

## Running the Application

For development:

```bash
uvicorn app.main:app --reload --factory
```

Or, since `create_app` returns a FastAPI instance:

```bash
uvicorn "app.main:create_app" --reload --factory
```

The `--factory` flag tells uvicorn that `create_app` is a factory function to call, not an already-instantiated app. The `--reload` flag restarts the server on file changes.

When uvicorn starts, it:

1. Imports `app.main`.
2. Calls `create_app()` to get the `FastAPI` instance.
3. Enters the lifespan — `Container()` is created.
4. Starts serving HTTP requests.

---

## What Goes in Lifespan vs. create_app()

| Concern | Where it goes |
| ------- | ------------- |
| Router registration | `create_app()` |
| Exception handler registration | `create_app()` |
| Static file mounting | `create_app()` |
| Dependency container creation | `lifespan` startup |
| Database connection pool creation | `lifespan` startup (hypothetical) |
| Database connection pool shutdown | `lifespan` shutdown (hypothetical) |
| Background task startup | `lifespan` startup (hypothetical) |

The rule: configuration that defines the application's structure (routers, handlers, mounts) goes in `create_app()`. Resources that need explicit lifecycle management (create on startup, release on shutdown) go in `lifespan`.

---

## Anti-Patterns to Avoid

**Module-level `app = FastAPI()`.** Creates a singleton, breaks test isolation, causes the lifespan to run at import time.

**Creating `Container()` in a route handler.** A new container per request means new repositories per request. Data saved in one request would not be visible in the next.

**Storing per-request data on `app.state`.** `app.state` is shared across all requests. Storing a request ID or user context there would create race conditions. Use `request.state` for per-request data.

**Forgetting `with TestClient(app) as c:`.** The most common mistake in FastAPI testing. Always use the context manager so the lifespan runs.

---

## Exercises

1. Try calling `TestClient(create_app())` without the `with` statement. Make a request and observe the `AttributeError`. Fix it by adding `with`.

2. Add a `print("App starting up")` before the `yield` in `lifespan` and a `print("App shutting down")` after. Run `pytest tests/integration/` and count how many times each message appears. Each test fixture creates a fresh app, so each print should appear once per test.

3. Add a second attribute to `app.state`: `app.state.start_time = datetime.now(timezone.utc)`. Add a route `GET /uptime` that returns `{"uptime_seconds": (datetime.now() - request.app.state.start_time).seconds}`. Test it with `TestClient`.

---

## Review Checklist

- [ ] I can explain why `create_app()` is a factory and not a module-level variable.
- [ ] I know what runs before and after `yield` in the lifespan.
- [ ] I understand why `Container()` is created in the lifespan and not per-request.
- [ ] I can explain the difference between `app.state` and `request.state`.
- [ ] I know why `with TestClient(app) as c:` is required.
