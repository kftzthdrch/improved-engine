# Chapter 03: Project Structure

## Learning Objective

Understand the full folder layout of the project, why each folder exists, and the placement rule that tells you where any new file belongs.

---

## The Placement Rule

Before showing the tree, here is the decision rule you use for any new file:

> - If it uses FastAPI, Pydantic, or HTTP concepts → `app/api/`
> - If it makes business decisions or orchestrates domain objects → `app/application/`
> - If it stores, retrieves, or communicates with external systems → `app/infrastructure/`
> - If it is a pure business concept (what, not how) → `app/domain/`
> - If it wires everything together → `app/composition/`
> - If it is a browser template or static asset → `app/ui/`

If a file touches two of these concerns, it is in the wrong layer and needs to be split.

---

## Full Directory Tree

```text
fastapi-hexognal/
├── app/
│   ├── main.py                         # App factory + lifespan
│   │
│   ├── composition/
│   │   └── container.py                # Wires all dependencies together
│   │
│   ├── domain/
│   │   ├── enums.py                    # CommandType, AlertType, TripStatus, ...
│   │   ├── errors.py                   # DomainError hierarchy
│   │   ├── models/
│   │   │   ├── command.py              # Command dataclass + lifecycle methods
│   │   │   ├── telemetry.py            # TelemetrySnapshot (frozen)
│   │   │   ├── alert.py                # VehicleAlert
│   │   │   ├── trip.py                 # TripSession
│   │   │   ├── maintenance.py          # MaintenanceState
│   │   │   └── diagnostic.py          # DiagnosticCode
│   │   └── value_objects/
│   │       ├── vehicle_id.py           # VehicleId (validates + normalises)
│   │       ├── command_id.py           # CommandId
│   │       ├── trip_id.py              # TripId
│   │       ├── temperature.py          # Temperature (range check)
│   │       ├── speed.py                # Speed (non-negative)
│   │       ├── battery_percent.py      # BatteryPercent (0–100)
│   │       └── odometer.py             # Odometer (non-negative)
│   │
│   ├── application/
│   │   ├── ports/
│   │   │   ├── command_repository.py   # Protocol: save / get / list_for_vehicle
│   │   │   ├── telemetry_repository.py # Protocol: save / get_latest / get_history
│   │   │   ├── alert_repository.py     # Protocol: save / get_active / clear
│   │   │   ├── trip_repository.py      # Protocol: save / get_active / get_by_id
│   │   │   ├── maintenance_repository.py
│   │   │   ├── diagnostic_repository.py
│   │   │   ├── vehicle_command_gateway.py  # Protocol: send(...)
│   │   │   ├── clock.py                # Protocol: now() -> datetime
│   │   │   └── id_generator.py         # Protocol: new_command_id / new_trip_id
│   │   ├── services/
│   │   │   ├── command_policy.py       # enforce_not_moving, enforce_battery_...
│   │   │   ├── telemetry_validation.py # validate speed, battery, odometer, temp
│   │   │   ├── alert_rules.py          # evaluate(snapshot, now) -> [AlertType]
│   │   │   └── maintenance_rules.py    # is_service_due, is_tire_check_due
│   │   └── use_cases/
│   │       ├── commands/
│   │       │   ├── lock_vehicle.py
│   │       │   ├── unlock_vehicle.py
│   │       │   ├── start_climate.py
│   │       │   ├── stop_climate.py
│   │       │   ├── set_cabin_temperature.py
│   │       │   ├── flash_lights.py
│   │       │   ├── honk_horn.py
│   │       │   ├── open_trunk.py
│   │       │   └── close_windows.py
│   │       ├── telemetry/
│   │       │   ├── ingest_telemetry.py
│   │       │   ├── get_vehicle_status.py
│   │       │   └── get_telemetry_history.py
│   │       ├── alerts/
│   │       │   ├── evaluate_vehicle_alerts.py
│   │       │   ├── get_active_alerts.py
│   │       │   └── clear_vehicle_alert.py
│   │       ├── trips/
│   │       │   ├── start_trip.py
│   │       │   ├── end_trip.py
│   │       │   ├── get_current_trip.py
│   │       │   └── get_trip_summary.py
│   │       ├── maintenance/
│   │       │   ├── get_maintenance_status.py
│   │       │   └── record_service_reset.py
│   │       ├── diagnostics/
│   │       │   ├── ingest_diagnostic_codes.py
│   │       │   ├── get_active_diagnostic_codes.py
│   │       │   └── clear_diagnostic_code.py
│   │       └── eligibility/
│   │           └── get_command_eligibility.py
│   │
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── in_memory_command_repository.py
│   │   │   ├── in_memory_telemetry_repository.py
│   │   │   ├── in_memory_alert_repository.py
│   │   │   ├── in_memory_trip_repository.py
│   │   │   ├── in_memory_maintenance_repository.py
│   │   │   └── in_memory_diagnostic_repository.py
│   │   ├── vehicle_gateway/
│   │   │   └── fake_vehicle_gateway.py
│   │   ├── time/
│   │   │   └── system_clock.py
│   │   └── ids/
│   │       └── uuid_generator.py
│   │
│   ├── api/
│   │   ├── dependencies.py             # get_X_use_case provider functions
│   │   ├── exception_handlers.py       # DomainError -> HTTP status mapping
│   │   ├── routes/
│   │   │   ├── commands.py
│   │   │   ├── telemetry.py
│   │   │   ├── alerts.py
│   │   │   ├── trips.py
│   │   │   ├── maintenance.py
│   │   │   ├── diagnostics.py
│   │   │   ├── eligibility.py
│   │   │   ├── health.py
│   │   │   └── ui.py
│   │   └── schemas/
│   │       ├── command_schemas.py
│   │       ├── telemetry_schemas.py
│   │       ├── alert_schemas.py
│   │       ├── trip_schemas.py
│   │       ├── maintenance_schemas.py
│   │       ├── diagnostic_schemas.py
│   │       ├── eligibility_schemas.py
│   │       └── error_schemas.py
│   │
│   └── ui/
│       ├── templates/
│       │   └── index.html              # Jinja2 dashboard template
│       └── static/
│           ├── app.js                  # Vanilla JS fetch() calls
│           └── styles.css
│
├── tests/
│   ├── architecture/
│   │   ├── test_forbidden_imports.py
│   │   ├── test_layer_direction.py
│   │   └── test_no_database_dependencies.py
│   ├── integration/
│   │   └── api/
│   │       ├── test_commands.py
│   │       ├── test_telemetry.py
│   │       ├── test_health.py
│   │       └── test_dependency_override.py
│   └── unit/
│       ├── domain/
│       │   └── test_value_objects.py
│       └── application/
│           └── test_command_policy.py
│
├── docs/                               # These chapter files
├── pyproject.toml
└── plan.md
```

---

## Why Each Folder Exists

### `app/domain/`

The heart of the system. No external dependencies. If you deleted every other folder, you could still run the domain logic in a plain Python script.

`models/` contains mutable domain objects with lifecycle methods (e.g., `Command.mark_succeeded()`). `value_objects/` contains immutable, self-validating wrappers around primitives. `errors.py` defines the exception hierarchy. `enums.py` defines the controlled vocabularies.

### `app/application/`

The orchestration layer. It knows *what* the system should do; it delegates *how* to ports.

`use_cases/` is the most important sub-folder. One file per user action. One class per file. Each class has a single `execute()` method. `ports/` defines the interfaces use cases depend on. `services/` holds business rule helpers that are reused across multiple use cases.

### `app/infrastructure/`

The "how" for storage and external communication. Everything here is replaceable. If the in-memory repositories were replaced with SQLAlchemy repositories, nothing in `app/domain/` or `app/application/` would change.

Sub-folders are organized by concern: `persistence/` for data storage, `vehicle_gateway/` for the external command channel, `time/` for the clock, `ids/` for ID generation.

### `app/api/`

The HTTP delivery mechanism. Everything here knows about FastAPI, Pydantic, and HTTP status codes.

`routes/` contains thin handler functions. `schemas/` contains Pydantic request and response models. `dependencies.py` exposes provider functions that `Depends()` calls. `exception_handlers.py` translates domain errors into JSON responses.

### `app/composition/`

The single file `container.py` is the only place in the codebase that instantiates infrastructure classes and passes them into use case constructors. It is the glue between the outer and inner rings. It is the only file that imports from both `app/infrastructure/` and `app/application/`.

### `app/ui/`

Browser assets. `templates/index.html` is the Jinja2 template rendered at `GET /`. `static/app.js` makes `fetch()` calls to the REST API. `static/styles.css` styles the dashboard.

### `tests/`

Organized to mirror the architecture:

- `unit/domain/` — tests that exercise domain classes with no frameworks.
- `unit/application/` — tests that exercise use cases and services with stub dependencies.
- `integration/api/` — tests that exercise the full HTTP stack via `TestClient`.
- `architecture/` — tests that parse Python source files and enforce import rules.

---

## The "Which Folder?" Decision in Practice

You are asked to add a feature: "Record a timestamp when the vehicle last communicated."

Work through the rule:

1. "Last communicated" is a concept about a vehicle. It lives in `app/domain/models/`. Add a field to an existing model or create a new one.
2. The business rule "if no communication in 10 minutes, raise STALE_TELEMETRY" already exists in `app/application/services/alert_rules.py`. The timestamp lookup goes through a port in `app/application/ports/`.
3. Storage of the timestamp goes in a repository in `app/infrastructure/persistence/`.
4. The HTTP endpoint to query it goes in `app/api/routes/`.
5. The Pydantic schema for the response goes in `app/api/schemas/`.

Each concern has a clear home. None of them bleed into each other.

---

## Anti-Patterns to Avoid

**Putting Pydantic models in `app/domain/`.** Domain models use dataclasses, not Pydantic. Pydantic belongs at the HTTP boundary in `app/api/schemas/`.

**Putting business logic in `app/infrastructure/`.** Repositories store and retrieve. They must not make decisions. A repository that checks whether a command is valid before saving it has violated the separation.

**Having `app/api/routes/` import from `app/infrastructure/`.** Routes should only know about use cases and ports, obtained through `Depends()`. Importing a concrete repository class into a route creates a hidden dependency that bypasses the composition root.

**A single giant `services.py` file.** If you find yourself writing `VehicleService` with 20 methods, each method is actually a separate use case. Split them into individual files under `app/application/use_cases/`.

---

## Exercises

1. Read `app/composition/container.py` top to bottom. Count how many imports come from `app/infrastructure/` and how many from `app/application/`. Note that it imports from both — and that this is the *only* file allowed to do so.

2. Create a new file `app/domain/models/fuel_level.py` (just a stub dataclass). Run `pytest tests/architecture/`. Confirm all tests still pass. Delete the file.

3. Try to import `InMemoryCommandRepository` directly in `app/api/routes/commands.py`. Run `pytest tests/architecture/test_layer_direction.py`. Observe the failure. Revert.

---

## Review Checklist

- [ ] I can recite the placement rule for each layer from memory.
- [ ] I understand why `container.py` is in its own `composition/` folder.
- [ ] I know the difference between `app/domain/models/` and `app/domain/value_objects/`.
- [ ] I can navigate to any use case given its action name (e.g., "ingest telemetry" → `app/application/use_cases/telemetry/ingest_telemetry.py`).
- [ ] I understand why tests are split into `unit/`, `integration/`, and `architecture/`.
