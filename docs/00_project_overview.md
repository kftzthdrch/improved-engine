# Chapter 00: Project Overview

## Learning Objective

Understand the overall structure and goals of this FastAPI hexagonal architecture learning project: what domain it models, what the application actually does, what it deliberately leaves out, and how the chapters in this documentation guide your learning.

---

## Why an Automotive Domain?

Vehicle telematics is an ideal teaching domain for three reasons:

1. **Rich real-world concepts** — commands, sensors, alerts, trips, and diagnostics give you many different interaction patterns without inventing artificial scenarios.
2. **Natural boundaries** — a vehicle has a distinct identity (`VehicleId`), its own state (telemetry), and external actors (a gateway that sends commands to the physical vehicle). These map cleanly onto ports and adapters.
3. **Obvious business rules** — "do not lock the vehicle while it is moving" is a rule everyone understands immediately, so the teaching value of enforcing it in the domain layer is clear.

This is not a production vehicle platform. It is a deliberately simplified model used to teach software architecture.

---

## What the Application Does

The application manages six domain areas, each served by a set of use cases.

### Vehicle Commands

Send control instructions to a vehicle and record the outcome.

| Command | HTTP Route |
| ------- | ---------- |
| Lock | `POST /vehicles/{id}/commands/lock` |
| Unlock | `POST /vehicles/{id}/commands/unlock` |
| Start climate | `POST /vehicles/{id}/commands/climate/start` |
| Stop climate | `POST /vehicles/{id}/commands/climate/stop` |
| Set cabin temperature | `POST /vehicles/{id}/commands/climate/temperature` |
| Flash lights | `POST /vehicles/{id}/commands/lights/flash` |
| Honk horn | `POST /vehicles/{id}/commands/horn` |
| Open trunk | `POST /vehicles/{id}/commands/trunk/open` |
| Close windows | `POST /vehicles/{id}/commands/windows/close` |

Each command is validated by a policy (e.g., the vehicle must not be moving), dispatched through a gateway, and persisted as a `Command` domain model with a lifecycle: `PENDING → SENT → SUCCEEDED / FAILED / REJECTED`.

### Telemetry

Ingest sensor readings from a vehicle and query them.

- `POST /vehicles/{id}/telemetry` — accept a new snapshot
- `GET /vehicles/{id}/status` — latest snapshot
- `GET /vehicles/{id}/telemetry/history` — up to the last 20 snapshots

A `TelemetrySnapshot` captures: speed (km/h), battery percentage, odometer (km), door lock state, and cabin temperature.

### Alerts

Evaluate whether a vehicle's telemetry triggers any alert conditions.

- `POST /vehicles/{id}/alerts/evaluate` — run rules against latest telemetry
- `GET /vehicles/{id}/alerts` — active alerts
- `DELETE /vehicles/{id}/alerts/{alert_type}` — clear an alert

Alert types: `LOW_BATTERY`, `CABIN_OVERHEAT`, `VEHICLE_MOVING`, `DOOR_UNLOCKED`, `STALE_TELEMETRY`.

### Trips

Track journeys with start/end odometer readings.

- `POST /vehicles/{id}/trips/start`
- `POST /vehicles/{id}/trips/end`
- `GET /vehicles/{id}/trips/current`
- `GET /vehicles/{id}/trips/{trip_id}/summary`

A `TripSession` records start time, start odometer, end time, and end odometer. The `distance_km` property is computed from those values.

### Maintenance

Track service intervals and flag when service is due.

- `GET /vehicles/{id}/maintenance` — current maintenance state
- `POST /vehicles/{id}/maintenance/service-reset` — record a service

A `MaintenanceState` carries last service odometer and last tire check odometer. Service is due after 15,000 km; tire check after 10,000 km.

### Diagnostics

Record and manage OBD-style diagnostic fault codes.

- `POST /vehicles/{id}/diagnostics` — ingest codes
- `GET /vehicles/{id}/diagnostics` — active codes
- `DELETE /vehicles/{id}/diagnostics/{code}` — clear a code

A `DiagnosticCode` has a code string, severity (`INFO`, `WARNING`, `ERROR`, `CRITICAL`), description, and timestamp.

### Command Eligibility

Query which commands are currently allowed given the vehicle's telemetry state.

- `GET /vehicles/{id}/eligibility`

### UI Dashboard

A simple browser interface at `GET /` that renders `app/ui/templates/index.html` and calls the above REST endpoints via `fetch()` in `app/ui/static/app.js`.

---

## What the Application Intentionally Does Not Do

### No Database

All data lives in Python dictionaries in memory. When the process restarts, all data is lost.

**Why?** A database adds operational complexity (connection strings, migrations, Docker Compose, async drivers) that obscures the architectural patterns being taught. The entire point of hexagonal architecture is that you can swap the storage mechanism by changing only the infrastructure layer. A database adapter would implement the same ports the in-memory repositories implement — nothing else would change.

See `app/infrastructure/persistence/` for all six in-memory repositories and `docs/07_in_memory_infrastructure.md` for a full explanation.

### No Authentication or Authorization

There is no token, session, API key, or user concept.

**Why?** Authentication is a cross-cutting concern that FastAPI handles with middleware and dependencies — it never touches the domain or application layers. Adding it now would add noise to the architecture lesson without teaching anything new about hexagonal design.

### No WebSockets or Real-Time Push

All communication is synchronous HTTP request/response.

**Why?** WebSockets would require an event-broadcasting mechanism across the application layer, which is an interesting but advanced topic. This project focuses on the fundamentals.

### No Background Task Queue

There is no Celery, Redis, or background worker.

**Why?** Same reason as above — the focus is architecture patterns, not infrastructure orchestration.

### No Async/Await

All route handlers and use cases are synchronous.

**Why?** `async`/`await` is a Python concurrency mechanism, not an architecture concept. FastAPI supports both; this project uses synchronous code to keep the examples readable.

---

## The No-Database Rule Explained

You will notice that `tests/architecture/test_no_database_dependencies.py` actively enforces this constraint by scanning every `.py` file in `app/` for imports of `sqlalchemy`, `alembic`, `sqlite`, `postgres`, `psycopg`, `asyncpg`, `redis`, and `pymongo`. If you add any of these imports the test suite will fail.

This is intentional. The no-database rule is not laziness — it is a teaching constraint that forces you to experience what hexagonal architecture actually delivers: you can run the entire application and its tests with zero external infrastructure. No Docker. No database server. No environment variables for connection strings.

When you are ready to add a database, see `docs/18_extension_points.md`.

---

## Learning Roadmap

Read these chapters in order:

| Chapter | Topic | Key Question Answered |
| ------- | ----- | --------------------- |
| 01 | Hexagonal Architecture | What is the pattern and why does it matter? |
| 02 | FastAPI Foundations | What FastAPI features does this project use? |
| 03 | Project Structure | Where does each type of code live and why? |
| 04 | Domain Layer | What are pure domain models and value objects? |
| 05 | Application Layer | What are use cases and application services? |
| 06 | Ports and Adapters | How do interfaces decouple layers? |
| 07 | In-Memory Infrastructure | How do the adapters implement the ports? |
| 08 | FastAPI API Layer | How do routes stay thin? |
| 09 | Dependency Injection | How does FastAPI wire everything together? |
| 10 | Error Handling | How do domain errors become HTTP responses? |
| 11 | Pydantic Schemas | What is the role of Pydantic in this architecture? |
| 12 | UI with Templates | How does the browser fit into the adapter model? |
| 13 | Testing Strategy | How do you test each layer in isolation? |
| 14 | Architecture Tests | How do you enforce layer boundaries automatically? |
| 15 | Lifespan and App Factory | How is the app initialized? |
| 16 | OpenAPI and Docs | What does FastAPI generate automatically? |
| 17 | Learning Exercises | Hands-on tasks to practice the concepts |
| 18 | Extension Points | How would you add a database, MQTT, auth, etc.? |
| 19 | Final Review Checklist | How well does this project follow the pattern? |

---

## Review Checklist

- [ ] I can name the six domain areas the application covers.
- [ ] I understand why there is no database and what would change if one were added.
- [ ] I can find the entry point of the application (`app/main.py`).
- [ ] I know where domain models live (`app/domain/models/`).
- [ ] I know where use cases live (`app/application/use_cases/`).
- [ ] I know where the API routes live (`app/api/routes/`).
- [ ] I know where the infrastructure adapters live (`app/infrastructure/`).
