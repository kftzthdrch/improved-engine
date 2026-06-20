# Chapter 02: FastAPI Foundations

## Learning Objective

Map every FastAPI feature used in this project to the file and line where it appears, so you understand both the concept and its concrete location in the codebase.

---

## The FastAPI Instance and App Factory

`app/main.py` defines `create_app()` which returns a configured `FastAPI` instance:

```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="Automotive Vehicle Command & Telematics Service",
        description="A hexagonal architecture learning project using FastAPI",
        version="0.1.0",
        lifespan=lifespan,
    )
    ...
    return app
```

`FastAPI()` accepts metadata that appears in the auto-generated OpenAPI specification at `/docs`. The `lifespan` parameter points to an async context manager that runs startup and shutdown logic.

The factory pattern (a function that creates and returns the app) is used instead of a module-level `app = FastAPI()` so that:

- Tests can call `create_app()` to get a fresh isolated app instance.
- The lifespan runs properly inside `TestClient`.
- Configuration can be injected per-environment in the future.

See `docs/15_lifespan_and_app_factory.md` for the full explanation.

---

## APIRouter

Each domain area has its own router defined at the top of its routes file:

```python
# app/api/routes/commands.py
router = APIRouter(tags=["commands"])

# app/api/routes/telemetry.py
router = APIRouter(tags=["telemetry"])

# app/api/routes/alerts.py
router = APIRouter(tags=["alerts"])
```

All routers are registered on the app in `create_app()`:

```python
app.include_router(commands.router)
app.include_router(telemetry.router)
app.include_router(alerts.router)
# ... and so on for trips, maintenance, diagnostics, eligibility, health, ui
```

`tags` group the routes in the OpenAPI `/docs` UI. `include_router` does not assign URL prefixes here — each route declares its own full path.

---

## Path Operations

A *path operation* is a function decorated with a method decorator from the router.

### POST with 201

```python
# app/api/routes/telemetry.py
@router.post("/vehicles/{vehicle_id}/telemetry", response_model=TelemetryResponse, status_code=201)
def ingest_telemetry(body: TelemetryIngestRequest, vehicle_id: str = Path(...), use_case=Depends(get_ingest_telemetry_use_case)):
    ...
```

`status_code=201` overrides the default 200 for resource-creation endpoints.

### POST with 200 (commands)

```python
# app/api/routes/commands.py
@router.post("/vehicles/{vehicle_id}/commands/lock", response_model=CommandResponse, status_code=200)
def lock_vehicle(vehicle_id: str = Path(...), use_case=Depends(get_lock_vehicle_use_case)):
    ...
```

Commands return 200 because the response includes the full command record; 201 is reserved for newly persisted resources.

### GET

```python
# app/api/routes/telemetry.py
@router.get("/vehicles/{vehicle_id}/status", response_model=VehicleStatusResponse)
def get_vehicle_status(vehicle_id: str = Path(...), use_case=Depends(get_vehicle_status_use_case)):
    ...
```

### DELETE with 204

```python
# app/api/routes/alerts.py
@router.delete("/vehicles/{vehicle_id}/alerts/{alert_type}", status_code=204)
def clear_alert(vehicle_id: str = Path(...), alert_type: str = Path(...), use_case=Depends(get_clear_alert_use_case)):
    ...
```

`status_code=204` means "no content" — the response body is empty.

---

## Path Parameters

`Path(...)` declares a required URL path segment. The `...` is Python's Ellipsis, meaning the parameter has no default value and is required.

```python
# app/api/routes/commands.py
def lock_vehicle(vehicle_id: str = Path(...), ...):
```

FastAPI extracts `vehicle_id` from the URL `/vehicles/VH-001/commands/lock` and passes it to the function as the string `"VH-001"`. The route handler then wraps it in a domain value object: `VehicleId(vehicle_id)`.

---

## Query Parameters

Query parameters are declared as function parameters with default values. One example appears in `HonkHornRequest` as a body field with default `False`. If a query parameter were used instead:

```python
# hypothetical example
def honk_horn(vehicle_id: str = Path(...), quiet_mode: bool = Query(False)):
```

`Query(False)` makes `quiet_mode` optional with a default of `False`, read from `?quiet_mode=true` in the URL.

In this project `quiet_mode` is sent in the request body (`HonkHornRequest`), but the pattern is the same.

---

## Request Body

When a function parameter is typed as a Pydantic `BaseModel`, FastAPI reads it from the JSON request body:

```python
# app/api/routes/commands.py
def set_cabin_temperature(body: SetCabinTemperatureRequest, vehicle_id: str = Path(...), ...):
    cmd = use_case.execute(VehicleId(vehicle_id), body.target_celsius)
```

`SetCabinTemperatureRequest` is defined in `app/api/schemas/command_schemas.py`:

```python
class SetCabinTemperatureRequest(BaseModel):
    target_celsius: float
```

FastAPI parses `{"target_celsius": 22.0}` from the request body and validates it against the schema before calling the handler.

---

## Response Model

`response_model` tells FastAPI which Pydantic schema to use when serializing the return value:

```python
@router.post("/vehicles/{vehicle_id}/commands/lock", response_model=CommandResponse, ...)
def lock_vehicle(...):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)   # returns a CommandResponse instance
```

FastAPI uses the `response_model` to:

- Validate the returned data matches the schema.
- Strip any extra fields not in the schema (security benefit).
- Generate the correct OpenAPI response schema at `/docs`.

---

## Status Codes

FastAPI uses the `status_code` parameter on the decorator. You can also raise `HTTPException` for error cases, but in this project domain errors are raised instead and mapped by exception handlers. See `docs/10_error_handling.md`.

---

## Depends() for Dependency Injection

`Depends()` is FastAPI's dependency injection mechanism. The function passed to `Depends` is called automatically and its return value is injected into the route handler.

```python
# app/api/routes/commands.py
def lock_vehicle(vehicle_id: str = Path(...), use_case=Depends(get_lock_vehicle_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
```

`get_lock_vehicle_use_case` is defined in `app/api/dependencies.py`:

```python
def get_lock_vehicle_use_case(request: Request):
    return request.app.state.container.lock_vehicle
```

It reads the pre-built `LockVehicleUseCase` instance from the container stored on `app.state`. See `docs/09_dependency_injection.md` for the full pattern.

---

## TestClient

FastAPI's `TestClient` wraps the app with `httpx` and lets you make HTTP requests in tests without running a server:

```python
# tests/integration/api/test_commands.py
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
```

Using `with TestClient(app) as c:` triggers the lifespan — the `Container` is created on startup and torn down after the test. If you forget `with`, the lifespan does not run and `app.state.container` will not exist.

---

## StaticFiles

Static assets (JavaScript and CSS) are served from `app/ui/static/` via FastAPI's `StaticFiles` mount:

```python
# app/main.py
from fastapi.staticfiles import StaticFiles

static_dir = os.path.join(os.path.dirname(__file__), "ui", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

The browser requests `/static/app.js` and `/static/styles.css`. FastAPI serves them directly without involving any route handler.

---

## Jinja2Templates

The dashboard UI is rendered server-side using Jinja2:

```python
# app/api/routes/ui.py
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=_templates_dir)

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html")
```

`TemplateResponse` renders `app/ui/templates/index.html` and returns it as HTML. The `request` object must be passed so Jinja2 can build URL helpers. See `docs/12_ui_with_templates_and_static_files.md`.

---

## Lifespan Events

The `lifespan` async context manager handles startup and shutdown:

```python
# app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container()   # startup
    yield
    # shutdown code would go here
```

Everything before `yield` runs at startup. Everything after `yield` runs at shutdown. The `Container()` is created once per app process and stored on `app.state` so all requests share the same repository instances. See `docs/15_lifespan_and_app_factory.md`.

---

## Exception Handlers

Custom exception handlers map domain errors to HTTP responses:

```python
# app/main.py
app.add_exception_handler(DomainError, domain_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

When any route handler raises a `DomainError`, FastAPI calls `domain_exception_handler` instead of returning a 500. See `docs/10_error_handling.md`.

---

## OpenAPI Docs at /docs

FastAPI auto-generates interactive API documentation at:

- `/docs` — Swagger UI (try requests from the browser)
- `/redoc` — ReDoc (read-only, better for reading)
- `/openapi.json` — the raw OpenAPI 3 JSON schema

No extra configuration is needed. The `title`, `description`, and `version` passed to `FastAPI()` appear at the top. `tags` on each router group the endpoints. `response_model` schemas appear in the response section of each endpoint.

---

## FastAPI Concepts Map

| Concept | File | Key Line |
| ------- | ---- | -------- |
| `FastAPI()` instance | `app/main.py` | `app = FastAPI(title=..., lifespan=lifespan)` |
| `create_app()` factory | `app/main.py` | `def create_app() -> FastAPI:` |
| `APIRouter` | `app/api/routes/commands.py` | `router = APIRouter(tags=["commands"])` |
| `@router.post` | `app/api/routes/commands.py` | `@router.post("/vehicles/{vehicle_id}/commands/lock", ...)` |
| `@router.get` | `app/api/routes/telemetry.py` | `@router.get("/vehicles/{vehicle_id}/status", ...)` |
| `@router.delete` | `app/api/routes/alerts.py` | `@router.delete("/vehicles/{vehicle_id}/alerts/{alert_type}", ...)` |
| `Path(...)` | `app/api/routes/commands.py` | `vehicle_id: str = Path(...)` |
| Request body | `app/api/routes/commands.py` | `body: SetCabinTemperatureRequest` |
| `response_model` | `app/api/routes/commands.py` | `response_model=CommandResponse` |
| `status_code` | `app/api/routes/telemetry.py` | `status_code=201` |
| `Depends()` | `app/api/routes/commands.py` | `use_case=Depends(get_lock_vehicle_use_case)` |
| `TestClient` | `tests/integration/api/test_commands.py` | `with TestClient(app) as c:` |
| `StaticFiles` | `app/main.py` | `app.mount("/static", StaticFiles(...))` |
| `Jinja2Templates` | `app/api/routes/ui.py` | `templates = Jinja2Templates(directory=...)` |
| `lifespan` | `app/main.py` | `@asynccontextmanager async def lifespan(app):` |
| Exception handler | `app/main.py` | `app.add_exception_handler(DomainError, ...)` |

---

## Anti-Patterns to Avoid

**Using `app = FastAPI()` at module level.** This makes the app a singleton that is hard to reset between tests. Always use a factory function.

**Putting `Depends()` inside use cases.** Use cases live in the application layer and must not know about FastAPI. Dependencies are resolved only in the API layer.

**Returning domain objects directly from routes.** Domain objects are not Pydantic models. FastAPI cannot serialize them automatically and will not validate the output. Always map domain objects to response schemas before returning.

**Forgetting `with TestClient(app) as c:`.** Without the context manager the lifespan does not run, the container is never created, and every request will raise an `AttributeError`.

---

## Exercises

1. Open `/docs` in your browser while the app is running (`uvicorn app.main:app --reload` from the project root with `app` pointing to `create_app`). Find the lock command endpoint. Use Swagger UI to POST a lock command to vehicle `VH-TEST`. Observe the response JSON.

2. Add a new optional query parameter `dry_run: bool = Query(False)` to the `lock_vehicle` route handler. Run the app and confirm it appears in `/docs`. Revert when done.

3. Change `status_code=200` to `status_code=201` on one command route. Run `pytest tests/integration/` and observe which test fails. Understand why.

---

## Review Checklist

- [ ] I can explain the difference between `Path(...)` and a request body parameter.
- [ ] I know why `create_app()` is a factory rather than a module-level variable.
- [ ] I understand what `response_model` does and why it matters.
- [ ] I can locate `Depends()` usage and trace it back to the container.
- [ ] I know why `with TestClient(app) as c:` is required.
