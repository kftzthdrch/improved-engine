# Chapter 01: Hexagonal Architecture

## Learning Objective

Understand the hexagonal architecture pattern (Ports and Adapters) and see exactly how this project implements it: which components are the center, which are inbound adapters, and which are outbound adapters.

---

## The Core Idea

Hexagonal architecture was named by Alistair Cockburn in 2005. The fundamental insight is:

> **Your business logic should not depend on the tools you use to deliver it.**

The "hexagon" represents the application core. Surrounding it are adapters that translate between the outside world and the core. The core never imports from the adapters; adapters always import from the core.

This means:

- Your business rules work the same whether called via HTTP, a CLI, a message queue, or a test.
- You can swap one adapter (e.g., swap the database) without changing the business rules.
- You can test business rules without starting a web server.

---

## The Three Zones

### Zone 1: The Domain (Center)

Pure Python. No frameworks. No database drivers. No HTTP concepts.

Files: `app/domain/`

Contains:

- Value objects: `VehicleId`, `Temperature`, `Speed`, `BatteryPercent`, `Odometer`, `CommandId`, `TripId`
- Domain models: `Command`, `TelemetrySnapshot`, `VehicleAlert`, `TripSession`, `MaintenanceState`
- Enums: `CommandType`, `CommandStatus`, `AlertType`, `TripStatus`, `DiagnosticSeverity`
- Domain errors: `DomainError` and subclasses in `app/domain/errors.py`

The domain has zero dependencies on any layer above it. It does not know FastAPI exists. It does not know there is a database (or a dict). It only knows about Python built-ins and the other things in `app/domain/`.

### Zone 2: The Application (Middle Ring)

Pure Python. No frameworks. Knows about the domain. Defines *ports* (interfaces) that outbound adapters must satisfy.

Files: `app/application/`

Contains:

- **Use cases** in `app/application/use_cases/` — one class per user action, each with an `execute()` method
- **Ports** in `app/application/ports/` — `typing.Protocol` definitions for repositories, the gateway, the clock, and the ID generator
- **Application services** in `app/application/services/` — reusable business rule helpers (`CommandPolicy`, `TelemetryValidation`, `AlertRules`, `MaintenanceRules`)

The application layer imports from the domain. It never imports from `app/infrastructure/` or `app/api/`.

### Zone 3: The Adapters (Outer Ring)

Framework-specific and infrastructure-specific code. Imports from the application and domain; never from each other.

Files: `app/api/`, `app/infrastructure/`, `app/composition/`, `app/ui/`

Adapters come in two directions.

---

## Inbound Adapters (Driving Adapters)

Inbound adapters *call* the application. They translate an external request into a use case call.

In this project there are two inbound adapters:

**FastAPI HTTP API** (`app/api/`)

The FastAPI routers accept HTTP requests, validate input with Pydantic schemas, call the appropriate use case, map the result to a response schema, and return an HTTP response. The routes contain no business logic. See `app/api/routes/commands.py` for a clear example.

**Browser** (`app/ui/`)

The browser loads the dashboard at `GET /` and then issues `fetch()` calls to the HTTP API. From the architecture's point of view the browser is just another caller of the HTTP adapter — it never bypasses the application layer.

---

## Outbound Adapters (Driven Adapters)

Outbound adapters are *called by* the application. They implement the ports defined in `app/application/ports/`.

In this project there are four categories:

**In-memory repositories** (`app/infrastructure/persistence/`)

Six classes — `InMemoryCommandRepository`, `InMemoryTelemetryRepository`, `InMemoryAlertRepository`, `InMemoryTripRepository`, `InMemoryMaintenanceRepository`, `InMemoryDiagnosticRepository` — each implementing the matching port Protocol.

**Fake vehicle gateway** (`app/infrastructure/vehicle_gateway/fake_vehicle_gateway.py`)

`FakeVehicleCommandGateway` implements the `VehicleCommandGateway` port. In a real system this would be replaced by a gateway that communicates with the vehicle over MQTT, cellular, or a proprietary protocol.

**System clock** (`app/infrastructure/time/system_clock.py`)

`SystemClock` implements the `Clock` port by returning `datetime.now(timezone.utc)`. In tests you can substitute a fake clock.

**UUID generator** (`app/infrastructure/ids/uuid_generator.py`)

`UuidGenerator` implements the `IdGenerator` port using `uuid.uuid4()`. In tests you can substitute a deterministic ID generator.

---

## Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                     INBOUND ADAPTERS                        │
│                                                             │
│   Browser (fetch)           FastAPI Routes                  │
│   app/ui/static/app.js      app/api/routes/*.py             │
│          │                        │                         │
│          └──────── HTTP ──────────┘                         │
└──────────────────────────┬──────────────────────────────────┘
                           │  calls use cases
┌──────────────────────────▼──────────────────────────────────┐
│                    APPLICATION LAYER                        │
│                                                             │
│   Use Cases   app/application/use_cases/                    │
│   Services    app/application/services/                     │
│                                                             │
│          │  talks through Ports (interfaces)                │
│          │  app/application/ports/*.py                      │
└──────────┬──────────────────────────────────────────────────┘
           │  depends on
┌──────────▼──────────────────────────────────────────────────┐
│                       DOMAIN LAYER                          │
│                                                             │
│   Models       app/domain/models/                           │
│   Value Objects app/domain/value_objects/                   │
│   Enums        app/domain/enums.py                          │
│   Errors       app/domain/errors.py                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    OUTBOUND ADAPTERS                        │
│  (implement the Ports; injected by app/composition/)        │
│                                                             │
│   InMemory*Repository       FakeVehicleCommandGateway       │
│   app/infrastructure/       app/infrastructure/             │
│   persistence/              vehicle_gateway/                │
│                                                             │
│   SystemClock               UuidGenerator                   │
│   app/infrastructure/       app/infrastructure/             │
│   time/                     ids/                            │
└─────────────────────────────────────────────────────────────┘
```

The composition root (`app/composition/container.py`) is the only place where outbound adapters are instantiated and injected into use cases. It sits outside the hexagon.

---

## The Dependency Direction Rule

The single most important rule in hexagonal architecture:

> **Dependencies point inward. The domain depends on nothing. The application depends only on the domain. Adapters depend on the application and domain.**

Stated as forbidden imports:

- `app/domain/` must never import from `app/application/`, `app/infrastructure/`, or `app/api/`.
- `app/application/` must never import from `app/infrastructure/` or `app/api/`.
- `app/infrastructure/` must never import from `app/api/`.

These rules are enforced by `tests/architecture/test_forbidden_imports.py` and `tests/architecture/test_layer_direction.py`. If you violate a rule, the test suite fails immediately.

---

## Why FastAPI Is an Outer Adapter

FastAPI is a web framework. It knows about HTTP, JSON, request routing, and OpenAPI schemas. None of these concepts belong in business logic.

When you write `from fastapi import FastAPI` you are reaching for a tool that only makes sense in the context of serving HTTP. If you imported FastAPI into a use case, that use case could no longer be called from a CLI, a test, a message queue consumer, or any other driver.

By keeping FastAPI confined to `app/api/`, you preserve the ability to add other inbound adapters without touching the business logic.

Test: `test_application_does_not_import_fastapi` in `tests/architecture/test_forbidden_imports.py` enforces this.

---

## Why In-Memory Repositories Are Adapters

The in-memory repositories store data in Python `dict` and `defaultdict` objects. They know about data structures. They do not know about business rules.

If you replaced `InMemoryTelemetryRepository` with a `SQLAlchemyTelemetryRepository`, the `IngestTelemetryUseCase` in `app/application/use_cases/telemetry/ingest_telemetry.py` would not change at all. The use case depends on the `TelemetryRepository` protocol, not on any concrete implementation. The concrete implementation is an infrastructure detail.

---

## Anti-Patterns to Avoid

**Importing FastAPI or Pydantic in a use case.** Use cases should be callable from any context. The moment they import `fastapi` or `pydantic` they become HTTP-specific.

**Importing a repository class in a use case.** Use cases should depend on the port protocol, not the concrete implementation. If `LockVehicleUseCase` imported `InMemoryCommandRepository` directly, you could never swap it for a database repository without editing the use case.

**Putting business logic in a route handler.** Routes that contain `if` statements making domain decisions are doing the use case's job. The route should delegate all decisions to the use case.

**Having a domain model import from the application layer.** The domain is the innermost layer. If `Command` imported `CommandRepository` it would create a circular dependency.

---

## Exercises

1. Open `app/application/use_cases/commands/lock_vehicle.py`. Identify every port it uses (the type annotations on the dataclass fields). Find the matching Protocol file in `app/application/ports/`. Then find the concrete implementation in `app/infrastructure/`.

2. Add `import fastapi` to `app/domain/models/command.py` and run `pytest tests/architecture/`. Observe the test failure. Remove the import and confirm tests pass again.

3. Draw your own version of the architecture diagram on paper, placing at least three concrete files per zone.

---

## Review Checklist

- [ ] I can explain the difference between inbound and outbound adapters.
- [ ] I can state the dependency direction rule from memory.
- [ ] I know which files are in the domain zone and which are in the adapter zone.
- [ ] I understand why FastAPI is an adapter, not part of the core.
- [ ] I understand what the composition root does and where it lives.
