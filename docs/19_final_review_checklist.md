# Chapter 19: Final Review Checklist

## Learning Objective

Consolidate everything covered in the previous 19 chapters by evaluating how well this project follows hexagonal architecture, answering 15 self-review questions, and identifying what you should be able to do independently after completing this learning project.

---

## Architecture Compliance Checklist

| Criterion | Answer | Evidence |
| --------- | ------ | -------- |
| Layer dependencies point inward | YES | `tests/architecture/test_forbidden_imports.py` passes |
| Domain imports no frameworks | YES | `test_domain_does_not_import_fastapi`, `test_domain_does_not_import_pydantic` |
| Application imports no frameworks | YES | `test_application_does_not_import_fastapi`, `test_application_does_not_import_pydantic` |
| Application imports no infrastructure | YES | `test_application_does_not_import_infrastructure` |
| Infrastructure imports no API layer | YES | `test_infrastructure_does_not_import_api` |
| No database anywhere | YES | `test_no_database_dependencies.py` (8 parametrized cases) |
| Routes are thin (no business logic) | YES | Each route handler is 2–4 lines; all logic in use cases |
| One class per use case | YES | 25 use case files, one class each |
| Use cases tested without FastAPI | YES | `tests/unit/application/test_command_policy.py` |
| Domain tested without FastAPI | YES | `tests/unit/domain/test_value_objects.py` |
| Application framework-free | YES | No FastAPI/Pydantic imports in `app/application/` |
| UI communicates via HTTP only | YES | `app/ui/static/app.js` uses `fetch()` only |
| Consistent error response shape | YES | All errors use `{"error": {"code": "...", "message": "..."}}` |
| Composition root wires all dependencies | YES | `app/composition/container.py` is the only file importing both infrastructure and application |
| Architecture rules machine-enforced | YES | `tests/architecture/` runs in CI with the rest of the suite |
| Docs complete | YES | 20 chapter files covering every concept |

---

## 15 Self-Review Questions

The following questions test whether you have understood the architecture, not just memorised it. Work through each one and check your answers against the referenced chapters.

---

**1. Where would you put a new business rule — "a vehicle cannot be unlocked remotely if a trip is active"?**

Answer: In `CommandPolicy` in `app/application/services/command_policy.py`. Add a method `enforce_no_active_trip(trip_repo: TripRepository, vehicle_id: VehicleId) -> None` that raises `CommandRejectedError` if an active trip is found. Call it from `UnlockVehicleUseCase`. Do not put this check in the route handler.

Reference: Chapter 05 (Application Layer), Chapter 10 (Error Handling).

---

**2. You need to store data persistently. Which files change and which do not?**

Answer: Create new repository classes in `app/infrastructure/persistence/` and edit `app/composition/container.py` to instantiate them. Nothing in `app/domain/`, `app/application/`, `app/api/`, or `app/ui/` changes.

Reference: Chapter 07 (In-Memory Infrastructure), Chapter 18 (Extension Points).

---

**3. A new developer adds `from fastapi import HTTPException` to `app/domain/errors.py`. How is this caught?**

Answer: `pytest tests/architecture/test_forbidden_imports.py::test_domain_does_not_import_fastapi` fails on the next test run. The test scans every `.py` file in `app/domain/` using `ast.parse` and asserts no import starts with `fastapi`.

Reference: Chapter 14 (Architecture Tests).

---

**4. Why is `LockVehicleUseCase` a dataclass rather than a class with a regular `__init__`?**

Answer: `@dataclass` generates `__init__` automatically from the field annotations. All six dependencies (`command_repo`, `telemetry_repo`, `gateway`, `clock`, `id_gen`, `policy`) appear as constructor parameters with their types, making them explicit and injectable. There is no magic, no IoC container scanning, and no hidden wiring.

Reference: Chapter 05 (Application Layer).

---

**5. A test calls `client.post("/vehicles/VH-001/commands/lock")` and gets `AttributeError: 'State' object has no attribute 'container'`. What is wrong?**

Answer: The `TestClient` was not used as a context manager. The lifespan never ran, so `app.state.container = Container()` was never executed. Fix: `with TestClient(app) as client:`.

Reference: Chapter 15 (Lifespan and App Factory), Chapter 13 (Testing Strategy).

---

**6. What is the difference between `app/domain/models/command.py` and `app/api/schemas/command_schemas.py`?**

Answer: `Command` in the domain is a mutable Python dataclass that represents the business concept of a vehicle command. It has lifecycle methods (`mark_succeeded`, `mark_failed`). `CommandResponse` in the schemas is an immutable Pydantic `BaseModel` designed solely to serialize a command record to JSON for an HTTP response. They serve different layers and can evolve independently.

Reference: Chapter 04 (Domain Layer), Chapter 11 (Pydantic Schemas).

---

**7. How would you test that `FakeVehicleCommandGateway` received exactly one LOCK command during a test?**

Answer: After the test, inspect `gateway.sent_commands`. It is a list of dicts appended by every `send()` call. Assert `len(gateway.sent_commands) == 1` and `gateway.sent_commands[0]["command_type"] == "LOCK"`. To access the gateway in an integration test, you would need a dependency override that injects a known `FakeVehicleCommandGateway` instance.

Reference: Chapter 07 (In-Memory Infrastructure), Chapter 13 (Testing Strategy).

---

**8. Why does `VehicleId.__post_init__` call `object.__setattr__` instead of `self.value = ...`?**

Answer: `@dataclass(frozen=True)` makes the instance immutable — normal attribute assignment raises `FrozenInstanceError`. To set `value` during initialization (inside `__post_init__`, which runs after `__init__`), you must bypass the frozen constraint using `object.__setattr__(self, "value", ...)`.

Reference: Chapter 04 (Domain Layer).

---

**9. What happens if you raise `HTTPException(status_code=409)` from inside a use case?**

Answer: It works technically (FastAPI catches `HTTPException` and returns the status) but it violates the architecture. The use case would import `fastapi`, breaking `test_application_does_not_import_fastapi`. Use cases must raise `DomainError` subclasses. The exception handler in `app/api/exception_handlers.py` maps them to HTTP status codes.

Reference: Chapter 10 (Error Handling), Chapter 14 (Architecture Tests).

---

**10. The browser sends `fetch("/vehicles/VH-001/commands/lock", {method: "POST"})`. Trace every file that handles this request, in order.**

Answer:

1. `app/ui/static/app.js` — initiates the fetch.
2. FastAPI routing in `app/main.py` — matches the URL to the lock route.
3. `app/api/routes/commands.py` — `lock_vehicle` handler.
4. `app/api/dependencies.py` — `get_lock_vehicle_use_case` provider.
5. `app/composition/container.py` — `container.lock_vehicle`.
6. `app/application/use_cases/commands/lock_vehicle.py` — `LockVehicleUseCase.execute()`.
7. `app/application/services/command_policy.py` — `enforce_not_moving`.
8. `app/infrastructure/persistence/in_memory_telemetry_repository.py` — `get_latest`.
9. `app/infrastructure/vehicle_gateway/fake_vehicle_gateway.py` — `send`.
10. `app/infrastructure/persistence/in_memory_command_repository.py` — `save`.
11. `app/api/routes/commands.py` — `_to_response(cmd)`.
12. `app/api/schemas/command_schemas.py` — `CommandResponse` serialised to JSON.

Reference: Chapters 01, 08, 09, 05, 07.

---

**11. Why are there separate `TelemetryResponse` and `VehicleStatusResponse` schemas when they have the same fields?**

Answer: They represent different semantic concepts — a history entry vs. the current status — and may diverge in the future (e.g., `VehicleStatusResponse` could add a `connection_status` field while `TelemetryResponse` keeps its historical shape). Sharing one schema would couple two distinct API concepts. See `app/api/schemas/telemetry_schemas.py`.

Reference: Chapter 11 (Pydantic Schemas).

---

**12. How do you make a test that always gets the same command ID?**

Answer: Create a stub `IdGenerator` that always returns `CommandId("fixed-id")`. Inject it into the use case constructor. Because `IdGenerator` is a `typing.Protocol`, any object with `new_command_id()` and `new_trip_id()` methods satisfies it — no imports from `app/application/ports/` are required in the test.

Reference: Chapter 06 (Ports and Adapters), Chapter 13 (Testing Strategy).

---

**13. What is the only file allowed to import from both `app/infrastructure/` and `app/application/`?**

Answer: `app/composition/container.py`. It is the composition root — its job is precisely to connect outbound adapters (infrastructure) to use cases (application). Every other file in `app/api/`, `app/application/`, and `app/infrastructure/` imports from at most one of these.

Reference: Chapter 03 (Project Structure), Chapter 01 (Hexagonal Architecture).

---

**14. A product manager asks for a CLI tool that can lock a vehicle without an HTTP request. What do you build?**

Answer: Write a new CLI script (e.g., `scripts/lock_vehicle.py`) that:

1. Calls `create_app()` to get the container (or instantiates `Container()` directly).
2. Calls `container.lock_vehicle.execute(VehicleId("VH-001"))`.
3. Prints the result.

No changes to the domain, application, or API layers. The CLI is a new inbound adapter that calls the same use case the HTTP route calls.

Reference: Chapter 01 (Hexagonal Architecture).

---

**15. What would you do differently if you were building this as a production system rather than a learning project?**

Reasonable answers include:

- Replace in-memory repositories with SQLAlchemy or another ORM backed by a real database.
- Add authentication (JWT or API key middleware).
- Add structured logging (use case entry/exit, errors).
- Add observability (Prometheus metrics, OpenTelemetry traces).
- Replace `FakeVehicleCommandGateway` with a real MQTT or cellular gateway.
- Add async/await throughout for better I/O concurrency.
- Add input validation at the API boundary using Pydantic `Field` constraints.
- Add an environment configuration system (Pydantic Settings).
- Set up CI/CD with the test suite as a gate.
- Add integration tests against a real (test) database in CI.

All of these are additive or infrastructure-level changes. The core hexagonal structure — domain models, value objects, use cases, ports — would remain valid and unchanged.

Reference: Chapter 18 (Extension Points).

---

## What You Should Be Able to Do After This Project

Having read all 20 chapters and completed the exercises, you should be able to:

- Explain hexagonal architecture, ports, and adapters to a colleague from memory.
- Add a new command, alert rule, or repository without violating any architectural rules.
- Write unit tests for business rules without starting an HTTP server.
- Write integration tests with `TestClient` and dependency overrides.
- Write architecture tests using `ast.parse` to enforce import rules.
- Trace any HTTP request through all layers of the codebase.
- Explain why Pydantic belongs at the HTTP boundary but not in the domain.
- Explain why `datetime.now()` and `uuid.uuid4()` are injected as ports rather than called directly.
- Describe the steps to add a database adapter, an MQTT gateway, or authentication without touching the core.
- Run `pytest tests/architecture/` with confidence and understand every test it contains.

---

## Next Steps

- Work through all six exercises in `docs/17_learning_exercises.md`.
- Attempt `docs/18_extension_points.md` Extension 1: add a SQLite adapter using Python's built-in `sqlite3` module.
- Explore FastAPI's async support by converting the synchronous routes to `async def`.
- Read the `user-skills:ros2` skill to see how the ROS 2 adapter extension would work in practice.
- Read the `user-skills:software-architecture` skill for broader architectural patterns beyond hexagonal.
