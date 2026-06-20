# Chapter 07: In-Memory Infrastructure

## Learning Objective

Understand every concrete adapter in `app/infrastructure/`: how the in-memory repositories work, why telemetry history is bounded to 20 snapshots, how `FakeVehicleCommandGateway` simulates both success and failure, and what would change if a real database were added.

---

## Why In-Memory Adapters?

In-memory storage is the simplest possible implementation of a repository port. Python dictionaries are fast, require no external processes, and need no configuration.

The in-memory adapters serve four purposes:

1. They let the application run with zero infrastructure setup — no Docker, no connection strings, no migrations.
2. They prove the port contracts work: if a real database repository later replaces them, the same port interface is used.
3. They make tests fast: no I/O, no network, pure RAM.
4. They demonstrate hexagonal architecture: nothing outside `app/infrastructure/` changes when these are swapped.

---

## In-Memory Repositories

### InMemoryCommandRepository

File: `app/infrastructure/persistence/in_memory_command_repository.py`

Stores `Command` objects in a plain `dict[str, Command]` keyed on `command_id.value`. Supports save, get by ID, and list all commands for a vehicle.

### InMemoryTelemetryRepository

File: `app/infrastructure/persistence/in_memory_telemetry_repository.py`

```python
from collections import defaultdict

MAX_HISTORY = 20

class InMemoryTelemetryRepository:
    def __init__(self):
        self._store: dict[str, list[TelemetrySnapshot]] = defaultdict(list)

    def save(self, snapshot: TelemetrySnapshot) -> None:
        history = self._store[snapshot.vehicle_id.value]
        history.append(snapshot)
        if len(history) > MAX_HISTORY:
            self._store[snapshot.vehicle_id.value] = history[-MAX_HISTORY:]

    def get_latest(self, vehicle_id: VehicleId) -> TelemetrySnapshot | None:
        history = self._store.get(vehicle_id.value, [])
        return history[-1] if history else None

    def get_history(self, vehicle_id: VehicleId) -> list[TelemetrySnapshot]:
        return list(self._store.get(vehicle_id.value, []))
```

Key design decisions:

- **`defaultdict(list)`** — accessing a key that does not exist returns an empty list instead of raising `KeyError`. This means no `if vehicle_id not in self._store:` guards throughout the code.
- **Bounded history** — after saving, if the list exceeds `MAX_HISTORY = 20`, it is truncated to the last 20 entries using `history[-MAX_HISTORY:]`. This prevents unbounded memory growth in a long-running process.
- **`list()` copy in `get_history`** — returning `list(...)` gives the caller a copy, not the internal list. If the caller modifies the returned list it does not corrupt the store.

### InMemoryAlertRepository

File: `app/infrastructure/persistence/in_memory_alert_repository.py`

Stores `VehicleAlert` objects keyed by `(vehicle_id.value, alert_type.value)`. When an alert is evaluated and already exists, it is updated in place. Clearing an alert marks it inactive rather than deleting it, so history is preserved.

### InMemoryTripRepository

File: `app/infrastructure/persistence/in_memory_trip_repository.py`

Stores `TripSession` objects. Supports saving, finding the active trip for a vehicle (status = `ACTIVE`), and looking up a trip by ID.

### InMemoryMaintenanceRepository

File: `app/infrastructure/persistence/in_memory_maintenance_repository.py`

Stores one `MaintenanceState` per vehicle. If no state exists for a vehicle yet, returns a default `MaintenanceState` with all zeros.

### InMemoryDiagnosticRepository

File: `app/infrastructure/persistence/in_memory_diagnostic_repository.py`

Stores `DiagnosticCode` objects keyed by `(vehicle_id.value, code)`. Clearing a code removes it from the active set.

---

## FakeVehicleCommandGateway

File: `app/infrastructure/vehicle_gateway/fake_vehicle_gateway.py`

```python
class FakeVehicleCommandGateway:
    def __init__(self, should_fail: bool = False, fail_reason: str = "Simulated gateway failure"):
        self._should_fail = should_fail
        self._fail_reason = fail_reason
        self.sent_commands: list[dict] = []

    def send(self, vehicle_id, command_id, command_type, payload) -> GatewayResult:
        self.sent_commands.append({
            "vehicle_id": vehicle_id.value,
            "command_id": command_id.value,
            "command_type": command_type.value,
            "payload": payload,
        })
        if self._should_fail:
            return GatewayResult(success=False, error_message=self._fail_reason)
        return GatewayResult(success=True)
```

Three design decisions:

- **`should_fail` flag** — by constructing `FakeVehicleCommandGateway(should_fail=True)`, you can simulate a gateway that always rejects commands. This lets you test the failure branch of command use cases without any real hardware or network.
- **`sent_commands` list** — records every command dispatched through the gateway. Tests can assert that the right commands were sent in the right order.
- **Default success** — the default (`should_fail=False`) makes the gateway silently succeed, which is the happy path for integration tests.

In the composition container the default is used: `self.gateway = FakeVehicleCommandGateway()`.

To test failure scenarios, create the gateway with `should_fail=True` and inject it into a use case directly (in a unit test) or override the dependency in an integration test.

---

## SystemClock

File: `app/infrastructure/time/system_clock.py`

```python
from datetime import datetime, timezone

class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
```

This is the simplest possible implementation of the `Clock` port. It always returns the real current UTC time.

In production this is what you want. In tests you want a fake clock so that timestamps are deterministic and comparable.

### Fake Clock Pattern for Tests

```python
from datetime import datetime, timezone

class FakeClock:
    def __init__(self, fixed_time: datetime):
        self._time = fixed_time

    def now(self) -> datetime:
        return self._time
```

`FakeClock` satisfies the `Clock` Protocol structurally (it has `now() -> datetime`). You inject it into a use case at test time:

```python
fixed = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
clock = FakeClock(fixed)
use_case = IngestTelemetryUseCase(
    telemetry_repo=InMemoryTelemetryRepository(),
    clock=clock,
    validation=TelemetryValidation(),
)
snap = use_case.execute(VehicleId("VH-001"), 0, 80, 5000, True, 22.0)
assert snap.timestamp == fixed
```

---

## UuidGenerator

File: `app/infrastructure/ids/uuid_generator.py`

```python
import uuid
from app.domain.value_objects.command_id import CommandId
from app.domain.value_objects.trip_id import TripId

class UuidGenerator:
    def new_command_id(self) -> CommandId:
        return CommandId(value=str(uuid.uuid4()))

    def new_trip_id(self) -> TripId:
        return TripId(value=str(uuid.uuid4()))
```

Wraps `uuid.uuid4()` in the domain value objects. In tests you can substitute a sequential generator:

```python
class SequentialIdGenerator:
    def __init__(self):
        self._counter = 0

    def new_command_id(self) -> CommandId:
        self._counter += 1
        return CommandId(f"cmd-{self._counter:04d}")

    def new_trip_id(self) -> TripId:
        self._counter += 1
        return TripId(f"trip-{self._counter:04d}")
```

---

## What Would Change If a Database Were Added?

Exactly one thing changes: `app/infrastructure/`.

Specifically, you would:

1. Create new files in `app/infrastructure/persistence/`, e.g., `sqlalchemy_command_repository.py` implementing `CommandRepository`.
2. Change `app/composition/container.py` to instantiate the SQLAlchemy repositories instead of the in-memory ones.
3. Add SQLAlchemy to `pyproject.toml`.
4. Add database migrations (Alembic or similar).
5. Update the no-database architecture test if you want to allow the new imports (or remove the test for the infrastructure module while keeping it for domain and application).

What does NOT change:

- `app/domain/` — zero changes.
- `app/application/` — zero changes (use cases, ports, services).
- `app/api/` — zero changes (routes, schemas, dependencies, exception handlers).
- `app/ui/` — zero changes.
- `tests/unit/` — zero changes (unit tests do not use the database).
- `tests/integration/` — the test fixtures might change if `TestClient` needs a database connection, but the test logic (what HTTP calls to make, what to assert) stays the same.

This is hexagonal architecture delivering its promise.

---

## Anti-Patterns to Avoid

**Business logic in a repository.** A repository that validates commands before saving them has violated the separation. Validation belongs in the domain (value objects) or application (policy) layers.

**Returning mutable internal state.** `get_history` returns `list(self._store.get(...))` — a copy. If it returned the internal list directly, a caller could mutate it and corrupt the store.

**Unbounded memory growth.** The telemetry repository truncates to 20 snapshots. Without this bound, a long-running process that receives frequent telemetry updates would eventually exhaust memory.

**Having the gateway raise exceptions on failure.** `FakeVehicleCommandGateway` returns a `GatewayResult` object. Use cases check `result.success`. This allows partial failures (gateway could not deliver, but the command was still recorded) without exception flow control in the use case.

---

## Exercises

1. Change `MAX_HISTORY = 20` to `MAX_HISTORY = 3` in `app/infrastructure/persistence/in_memory_telemetry_repository.py`. Run the tests, then send 5 telemetry readings to vehicle `VH-001` via the API and call `GET /vehicles/VH-001/telemetry/history`. Confirm you get at most 3 results. Revert.

2. Instantiate `FakeVehicleCommandGateway(should_fail=True)` in a Python REPL. Call `send(VehicleId("VH-001"), CommandId("c-001"), CommandType.LOCK, {})`. Inspect `sent_commands`. Confirm the command was recorded even though it "failed."

3. Write a `FakeClock` that advances by 1 second each call to `now()`. Inject it into `IngestTelemetryUseCase`. Call `execute()` three times. Assert that each snapshot's timestamp is 1 second later than the previous.

---

## Review Checklist

- [ ] I understand why `defaultdict(list)` is used in `InMemoryTelemetryRepository`.
- [ ] I can explain why telemetry history is bounded to 20 snapshots.
- [ ] I know how to use `FakeVehicleCommandGateway` to simulate gateway failures.
- [ ] I know the fake clock pattern and why `SystemClock` is an adapter.
- [ ] I can list exactly what would change — and what would not — if a database were added.
