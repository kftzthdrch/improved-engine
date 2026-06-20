# Chapter 13: Testing Strategy

## Learning Objective

Understand the three-tier testing approach in this project — unit tests for domain and application, integration tests with TestClient, and architecture tests — and learn the patterns for fake clocks, deterministic IDs, and dependency overrides.

---

## Three Tiers of Tests

### Tier 1: Unit Tests

Directory: `tests/unit/`

Unit tests exercise a single class or function in complete isolation. No FastAPI. No HTTP. No databases. Dependencies are injected as stubs.

**What they test:**

- Domain value object validation (`tests/unit/domain/test_value_objects.py`)
- Application service rules (`tests/unit/application/test_command_policy.py`)

**Why they are fast:** No I/O, no network, no process startup. A typical unit test suite runs in under a second.

**When to write them:** For any business rule — a value that should be rejected, a policy that should raise an error, a model method that should compute a result.

### Tier 2: Integration Tests

Directory: `tests/integration/api/`

Integration tests exercise the full HTTP stack using `TestClient`. They call real routes, which call real use cases, which call real repositories (in-memory).

**What they test:**

- HTTP routing (does the right route match the URL?)
- Request body parsing (does Pydantic reject invalid input?)
- Response shape (does the route return the right JSON fields?)
- End-to-end behavior (lock fails when moving, telemetry history has a limit)
- Dependency overrides (does replacing a use case stub work correctly?)

**Why they are still fast:** `TestClient` does not start a real HTTP server. It calls into FastAPI's ASGI application directly. No network socket, no port binding.

### Tier 3: Architecture Tests

Directory: `tests/architecture/`

Architecture tests parse Python source files using `ast` and assert that forbidden imports do not exist. See `docs/14_architecture_tests.md` for the full explanation.

---

## Unit Test: Value Objects

File: `tests/unit/domain/test_value_objects.py`

```python
import pytest
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.speed import Speed
from app.domain.value_objects.battery_percent import BatteryPercent
from app.domain.value_objects.temperature import Temperature
from app.domain.value_objects.odometer import Odometer
from app.domain.errors import InvalidVehicleIdError, InvalidCommandError

def test_vehicle_id_normalizes_to_uppercase():
    vid = VehicleId("vh-001")
    assert vid.value == "VH-001"

def test_vehicle_id_rejects_empty():
    with pytest.raises(InvalidVehicleIdError):
        VehicleId("")

def test_speed_rejects_negative():
    with pytest.raises(InvalidCommandError):
        Speed(-1)

def test_battery_rejects_over_100():
    with pytest.raises(InvalidCommandError):
        BatteryPercent(101)

def test_temperature_rejects_extreme():
    with pytest.raises(InvalidCommandError):
        Temperature(200)

def test_odometer_rejects_negative():
    with pytest.raises(InvalidCommandError):
        Odometer(-1)
```

No fixtures, no TestClient, no app factory. Pure Python class instantiation and assertion.

---

## Unit Test: Application Service

File: `tests/unit/application/test_command_policy.py`

```python
import pytest
from datetime import datetime, timezone
from app.application.services.command_policy import CommandPolicy
from app.domain.errors import CommandRejectedError
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId

def make_snapshot(speed=0.0, battery=80.0):
    return TelemetrySnapshot(
        vehicle_id=VehicleId("VH-001"),
        speed_kph=speed,
        battery_percent=battery,
        odometer_km=1000,
        door_locked=True,
        cabin_temperature_c=22.0,
        timestamp=datetime.now(timezone.utc),
    )

policy = CommandPolicy()

def test_enforce_not_moving_passes_when_stopped():
    policy.enforce_not_moving(make_snapshot(speed=0))

def test_enforce_not_moving_raises_when_moving():
    with pytest.raises(CommandRejectedError):
        policy.enforce_not_moving(make_snapshot(speed=10))
```

`CommandPolicy` requires only a `TelemetrySnapshot` to test. No repositories, no gateway, no clock. The snapshot is constructed directly from domain classes.

---

## Integration Test: Full HTTP Stack

File: `tests/integration/api/test_commands.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

@pytest.fixture()
def client_with_telemetry(client):
    client.post("/vehicles/VH-001/telemetry", json={
        "speed_kph": 0, "battery_percent": 80, "odometer_km": 5000,
        "door_locked": True, "cabin_temperature_c": 22,
    })
    return client

def test_lock_succeeds_when_stopped(client_with_telemetry):
    r = client_with_telemetry.post("/vehicles/VH-001/commands/lock")
    assert r.status_code == 200
    assert r.json()["status"] == "SUCCEEDED"

def test_lock_rejected_when_moving(client):
    client.post("/vehicles/VH-001/telemetry", json={
        "speed_kph": 60, "battery_percent": 80, "odometer_km": 5000,
        "door_locked": True, "cabin_temperature_c": 22,
    })
    r = client.post("/vehicles/VH-001/commands/lock")
    assert r.status_code == 409

def test_invalid_vehicle_id_returns_400():
    app = create_app()
    with TestClient(app) as c:
        r = c.post("/vehicles/%20/commands/lock")
        assert r.status_code == 400
```

Key patterns:

- `client` fixture calls `create_app()` fresh for each test — no shared state.
- `with TestClient(app) as c:` triggers the lifespan, creating the `Container`.
- `client_with_telemetry` is a fixture that depends on `client` and seeds telemetry data so the lock policy has data to evaluate.
- Fixtures yield inside `with TestClient(...)` so the lifespan teardown happens after the test.

---

## Integration Test: Dependency Override

File: `tests/integration/api/test_dependency_override.py`

```python
from fastapi.testclient import TestClient
from app.main import create_app
from app.api.dependencies import get_lock_vehicle_use_case
from app.domain.models.command import Command
from app.domain.enums import CommandType, CommandStatus
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.command_id import CommandId
from datetime import datetime, timezone

def make_stub_command():
    return Command(
        id=CommandId("stub-id"),
        vehicle_id=VehicleId("VH-TEST"),
        command_type=CommandType.LOCK,
        status=CommandStatus.SUCCEEDED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

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

This test verifies the HTTP layer (routing, response schema mapping) in isolation from the use case logic. The `StubLockUseCase` returns a pre-built command — the test does not care about the policy or the gateway.

---

## Fake Clock Pattern

When you need to test code that calls `clock.now()`, inject a fake clock:

```python
from datetime import datetime, timezone

class FakeClock:
    def __init__(self, fixed: datetime):
        self._time = fixed

    def now(self) -> datetime:
        return self._time

# In a test:
fixed_time = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
clock = FakeClock(fixed_time)
use_case = IngestTelemetryUseCase(
    telemetry_repo=InMemoryTelemetryRepository(),
    clock=clock,
    validation=TelemetryValidation(),
)
snap = use_case.execute(VehicleId("VH-001"), 0, 80, 5000, True, 22.0)
assert snap.timestamp == fixed_time
```

`FakeClock` satisfies the `Clock` Protocol structurally — no inheritance required.

---

## Deterministic ID Pattern

When you need to test code that calls `id_gen.new_command_id()`, inject a stub:

```python
from app.domain.value_objects.command_id import CommandId
from app.domain.value_objects.trip_id import TripId

class FixedIdGenerator:
    def new_command_id(self) -> CommandId:
        return CommandId("fixed-command-id")

    def new_trip_id(self) -> TripId:
        return TripId("fixed-trip-id")

# In a test:
id_gen = FixedIdGenerator()
use_case = LockVehicleUseCase(
    command_repo=InMemoryCommandRepository(),
    telemetry_repo=InMemoryTelemetryRepository(),
    gateway=FakeVehicleCommandGateway(),
    clock=SystemClock(),
    id_gen=id_gen,
    policy=CommandPolicy(),
)
cmd = use_case.execute(VehicleId("VH-001"))
assert cmd.id.value == "fixed-command-id"
```

---

## Test Fixture Design Principles

**One `create_app()` call per test.** Each test gets a fresh, empty container with empty repositories. No shared state between tests.

**Use fixtures for common setup.** The `client_with_telemetry` fixture shows how to build on top of the `client` fixture to seed data. Avoid seeding data in individual tests — it creates hard-to-read setup code.

**Prefer integration tests for happy paths, unit tests for edge cases.** An integration test that exercises the full HTTP stack is good for verifying the system works end to end. A unit test is better for testing every boundary condition of a business rule (all four `CommandPolicy` methods, all value object edge cases).

---

## Anti-Patterns to Avoid

**Sharing `TestClient` across tests.** A shared client means shared in-memory repositories. A telemetry record seeded in one test can affect another test's result.

**Not using `with TestClient(app) as c:`.** The lifespan does not run without the context manager. `app.state.container` will not exist and every request will raise `AttributeError`.

**Testing business logic through HTTP.** If you have 20 edge cases for `CommandPolicy`, writing 20 integration tests (each requiring an HTTP request, JSON parsing, and assertion) is slower and harder to read than 20 unit tests that call `policy.enforce_not_moving()` directly.

**Leaving `dependency_overrides` on a shared app instance.** If tests reuse an app instance, overrides from one test bleed into the next. Always use `create_app()` per test or clear overrides in a teardown.

---

## Exercises

1. Write a unit test for `AlertRules.evaluate()` that tests every alert type. Use a `TelemetrySnapshot` constructed directly with values that trigger each alert.

2. Write an integration test that sends telemetry with a very old timestamp (more than 10 minutes ago) and then evaluates alerts. Assert that `STALE_TELEMETRY` is in the response.

3. Write a dependency override test for `get_ingest_telemetry_use_case` where the stub raises `InvalidCommandError("simulated failure")`. Assert the response is HTTP 400 with `error.code == "INVALID_COMMAND"`.

---

## Review Checklist

- [ ] I understand the difference between unit, integration, and architecture tests.
- [ ] I know why each `client` fixture calls `create_app()` fresh.
- [ ] I can write a `FakeClock` that satisfies the `Clock` Protocol.
- [ ] I can write a dependency override test for any route.
- [ ] I know when to write a unit test vs. an integration test.
