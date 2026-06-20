# Automotive Vehicle Command & Telematics Service

A learning project for **hexagonal architecture** (Ports & Adapters) and **FastAPI** using an
automotive vehicle telematics domain. Every layer — domain, application, infrastructure, API,
and UI — is deliberately separated so the architecture can be studied, tested, and extended
independently.

## Learning Goals

- Hexagonal architecture: ports, adapters, dependency direction
- FastAPI: routers, Pydantic schemas, dependency injection, lifespan, exception handlers
- Use-case-driven design: one class per business action
- In-memory infrastructure: no database, no ORM — all state lives in process memory
- Architecture tests: enforcing layer boundaries with `ast` import scanning

## What the App Does

| Feature | Endpoints |
| --- | --- |
| Vehicle commands | Lock, Unlock, Climate, Temperature, Flash Lights, Horn, Trunk, Windows |
| Telemetry | Ingest sensor data, vehicle status, telemetry history |
| Command eligibility | Which commands are currently allowed and why |
| Alerts | Low battery, cabin overheat, moving vehicle, unlocked door, stale telemetry |
| Trips | Start / end trip, distance calculation |
| Maintenance | Service due / tire check due based on odometer |
| Diagnostics | Ingest and clear OBD-style diagnostic codes |

No database. No authentication. No background tasks. All state is held in process-local
in-memory repositories — by design, for learning.

## Project Structure

```text
app/
  domain/          ← Pure Python: enums, value objects, models, errors
  application/     ← Use cases, ports (Protocol), application services
  infrastructure/  ← In-memory repos, fake gateway, clock, ID generator
  composition/     ← Wires the object graph (Container)
  api/             ← FastAPI routers, Pydantic schemas, dependencies
  ui/              ← Jinja2 template, vanilla JS, CSS
tests/
  unit/            ← Domain and application tests (no FastAPI)
  integration/     ← API tests with TestClient
  architecture/    ← Forbidden import and no-database checks
docs/              ← 21 educational chapters
```

## Setup

**1. Create and activate a virtual environment:**

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

**2. Install dependencies:**

```bash
# Runtime only
pip install -r requirements.txt

# Runtime + dev tools (pytest, httpx)
pip install -r requirements-dev.txt
```

## Run

```bash
uvicorn app.main:create_app --factory --reload
```

Then open:

- `http://localhost:8000` — interactive dashboard UI
- `http://localhost:8000/docs` — Swagger / OpenAPI explorer
- `http://localhost:8000/redoc` — ReDoc API reference
- `http://localhost:8000/health` — health check

## Test

```bash
pytest
```

Expected output: **46 passed** across unit, integration, and architecture tests.

```text
tests/architecture/   8 tests  — layer boundary + no-database enforcement
tests/integration/   27 tests  — API endpoints, error responses, dependency overrides
tests/unit/          11 tests  — value objects, command policy rules
```

## Architecture Summary

```text
Browser / TestClient  (inbound adapters)
         ↓
   FastAPI routes     (app/api/)
         ↓
   Use cases          (app/application/use_cases/)
         ↓
   Domain model       (app/domain/)
         ↑
   Ports (Protocol)   (app/application/ports/)
         ↑
   Adapters           (app/infrastructure/)
```

The **Dependency Rule**: nothing in `domain/` or `application/` imports from `infrastructure/`
or `api/`. This is enforced by `tests/architecture/`.

## No Database

This project intentionally uses no database. All state is held in Python dicts in
`app/infrastructure/persistence/`. Adding a real database later requires only a new
infrastructure adapter — the domain and use cases are unchanged.

Forbidden packages (enforced by tests): `sqlalchemy`, `alembic`, `sqlite`, `postgres`,
`psycopg`, `asyncpg`, `redis`, `pymongo`.

## Documentation

| Chapter | Topic |
| --- | --- |
| [00](docs/00_project_overview.md) | Project overview and learning roadmap |
| [01](docs/01_hexagonal_architecture.md) | Hexagonal architecture — ports, adapters, dependency direction |
| [02](docs/02_fastapi_foundations.md) | FastAPI concepts used in this project |
| [03](docs/03_project_structure.md) | Folder layout and placement rules |
| [04](docs/04_domain_layer.md) | Domain models, value objects, errors |
| [05](docs/05_application_layer.md) | Use cases, services, ports |
| [06](docs/06_ports_and_adapters.md) | Protocol-based ports and adapter swapping |
| [07](docs/07_in_memory_infrastructure.md) | In-memory repositories and fake gateway |
| [08](docs/08_fastapi_api_layer.md) | Thin route handlers and schema mapping |
| [09](docs/09_dependency_injection.md) | FastAPI Depends, composition container, overrides |
| [10](docs/10_error_handling.md) | Domain errors, exception handlers, HTTP mapping |
| [11](docs/11_pydantic_schemas.md) | Pydantic as API boundary only |
| [12](docs/12_ui_with_templates_and_static_files.md) | Jinja2, StaticFiles, vanilla JS |
| [13](docs/13_testing_strategy.md) | Unit, integration, and dependency override tests |
| [14](docs/14_architecture_tests.md) | Enforcing layer boundaries with AST import scanning |
| [15](docs/15_lifespan_and_app_factory.md) | create_app factory, lifespan, app.state |
| [16](docs/16_openapi_and_docs.md) | OpenAPI generation, tags, response models |
| [17](docs/17_learning_exercises.md) | Hands-on exercises for each architectural concept |
| [18](docs/18_extension_points.md) | How to add database, MQTT, auth, WebSockets later |
| [19](docs/19_final_review_checklist.md) | Final architecture compliance checklist |
| [20](docs/20_hexagonal_vs_clean_architecture.md) | Hexagonal vs Clean Architecture — when to use which |
