# Chapter 17: Learning Exercises

## Learning Objective

Practice adding features to the project by following the hexagonal architecture patterns established in the existing code. Each exercise walks through the exact files to create or edit.

---

## Exercise 1: Add a New Command Use Case (REMOTE_START_ENGINE)

This exercise adds a complete new command — from domain enum to HTTP route.

### Step 1: Add the enum value

Edit `app/domain/enums.py`. Add to `CommandType`:

```python
REMOTE_START_ENGINE = "REMOTE_START_ENGINE"
```

### Step 2: Create the use case

Create `app/application/use_cases/commands/remote_start_engine.py`:

```python
from dataclasses import dataclass
from app.application.ports.command_repository import CommandRepository
from app.application.ports.telemetry_repository import TelemetryRepository
from app.application.ports.vehicle_command_gateway import VehicleCommandGateway
from app.application.ports.clock import Clock
from app.application.ports.id_generator import IdGenerator
from app.application.services.command_policy import CommandPolicy
from app.domain.enums import CommandType, CommandStatus
from app.domain.models.command import Command
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class RemoteStartEngineUseCase:
    command_repo: CommandRepository
    telemetry_repo: TelemetryRepository
    gateway: VehicleCommandGateway
    clock: Clock
    id_gen: IdGenerator
    policy: CommandPolicy

    def execute(self, vehicle_id: VehicleId) -> Command:
        now = self.clock.now()
        command = Command(
            id=self.id_gen.new_command_id(),
            vehicle_id=vehicle_id,
            command_type=CommandType.REMOTE_START_ENGINE,
            status=CommandStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        latest = self.telemetry_repo.get_latest(vehicle_id)
        try:
            self.policy.enforce_battery_sufficient(latest, min_percent=30.0)
        except Exception as e:
            command.mark_rejected(str(e), self.clock.now())
            self.command_repo.save(command)
            raise
        self.command_repo.save(command)
        result = self.gateway.send(vehicle_id, command.id, command.command_type, {})
        if result.success:
            command.mark_succeeded(self.clock.now())
        else:
            command.mark_failed(result.error_message or "Gateway failure", self.clock.now())
        self.command_repo.save(command)
        return command
```

### Step 3: Register in the container

Edit `app/composition/container.py`. Add the import:

```python
from app.application.use_cases.commands.remote_start_engine import RemoteStartEngineUseCase
```

Add to `Container.__init__()`:

```python
self.remote_start_engine = RemoteStartEngineUseCase(
    command_repo=self.command_repo,
    telemetry_repo=self.telemetry_repo,
    gateway=self.gateway,
    clock=self.clock,
    id_gen=self.id_gen,
    policy=self.command_policy,
)
```

### Step 4: Add a dependency provider

Edit `app/api/dependencies.py`:

```python
def get_remote_start_engine_use_case(request: Request):
    return get_container(request).remote_start_engine
```

### Step 5: Add the route

Edit `app/api/routes/commands.py`:

```python
from app.api.dependencies import ..., get_remote_start_engine_use_case

@router.post("/vehicles/{vehicle_id}/commands/engine/start", response_model=CommandResponse, status_code=200)
def remote_start_engine(vehicle_id: str = Path(...), use_case=Depends(get_remote_start_engine_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)
```

### Step 6: Write a test

Add to `tests/integration/api/test_commands.py`:

```python
def test_remote_start_rejected_when_battery_low(client):
    client.post("/vehicles/VH-001/telemetry", json={
        "speed_kph": 0, "battery_percent": 20, "odometer_km": 5000,
        "door_locked": True, "cabin_temperature_c": 22,
    })
    r = client.post("/vehicles/VH-001/commands/engine/start")
    assert r.status_code == 409
```

Run `pytest tests/architecture/` to confirm no rules are violated.

---

## Exercise 2: Add a New Alert Rule (LOW_FUEL)

This exercise adds a new alert type and evaluation rule.

### Step 1: Add the enum value

Edit `app/domain/enums.py`. Add to `AlertType`:

```python
LOW_FUEL = "LOW_FUEL"
```

### Step 2: Add the fuel field to TelemetrySnapshot (optional)

If your telemetry includes fuel level, add `fuel_percent: float = 100.0` to `TelemetrySnapshot` in `app/domain/models/telemetry.py` and `TelemetryIngestRequest` in `app/api/schemas/telemetry_schemas.py`.

Alternatively, reuse `battery_percent` as a proxy (for this exercise, treat battery below 10% as "low fuel").

### Step 3: Add the rule

Edit `app/application/services/alert_rules.py`. Add to `evaluate()`:

```python
if snapshot.battery_percent < 10:
    triggered.append(AlertType.LOW_FUEL)
```

### Step 4: Write a unit test for the new rule

Add to `tests/unit/` or `tests/integration/api/`:

```python
def test_low_fuel_alert_triggered():
    rules = AlertRules()
    snapshot = TelemetrySnapshot(
        vehicle_id=VehicleId("VH-001"),
        speed_kph=0, battery_percent=5, odometer_km=1000,
        door_locked=True, cabin_temperature_c=22,
        timestamp=datetime.now(timezone.utc),
    )
    triggered = rules.evaluate(snapshot, datetime.now(timezone.utc))
    assert AlertType.LOW_FUEL in triggered
```

Run `pytest tests/architecture/` to confirm the domain change did not introduce any forbidden imports.

---

## Exercise 3: Replace FakeVehicleCommandGateway with a Delayed Fake

This exercise practices adapter swapping by creating a new outbound adapter.

### Step 1: Create the new adapter

Create `app/infrastructure/vehicle_gateway/slow_fake_vehicle_gateway.py`:

```python
import time
from app.application.ports.vehicle_command_gateway import GatewayResult
from app.domain.enums import CommandType
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.command_id import CommandId

class SlowFakeVehicleCommandGateway:
    def __init__(self, delay_seconds: float = 0.1):
        self._delay = delay_seconds
        self.sent_commands: list[dict] = []

    def send(self, vehicle_id: VehicleId, command_id: CommandId, command_type: CommandType, payload: dict) -> GatewayResult:
        self.sent_commands.append({
            "vehicle_id": vehicle_id.value,
            "command_id": command_id.value,
            "command_type": command_type.value,
        })
        time.sleep(self._delay)
        return GatewayResult(success=True)
```

### Step 2: Swap in container.py

Edit `app/composition/container.py`:

```python
# Before
from app.infrastructure.vehicle_gateway.fake_vehicle_gateway import FakeVehicleCommandGateway
self.gateway = FakeVehicleCommandGateway()

# After
from app.infrastructure.vehicle_gateway.slow_fake_vehicle_gateway import SlowFakeVehicleCommandGateway
self.gateway = SlowFakeVehicleCommandGateway(delay_seconds=0.05)
```

### Step 3: Verify

Run `pytest tests/integration/api/test_commands.py`. The tests should still pass (slightly slower). Run `pytest tests/architecture/` to confirm no rules are violated. Revert `container.py` when done.

**Observation:** You changed exactly two lines in `container.py` (the import and the instantiation). No use case, no route, no schema, no test changed.

---

## Exercise 4: Add a New UI Section (Command History)

This exercise adds a "Command History" section to the dashboard that calls `GET /commands/{command_id}`.

### Step 1: Add HTML to the template

Edit `app/ui/templates/index.html`. Add a section:

```html
<section id="command-history">
    <h2>Command History</h2>
    <input id="cmd-id-input" type="text" placeholder="Command ID">
    <button onclick="fetchCommand()">Fetch</button>
    <pre id="cmd-result"></pre>
</section>
```

### Step 2: Add JavaScript

Edit `app/ui/static/app.js`:

```javascript
async function fetchCommand() {
    const commandId = document.getElementById("cmd-id-input").value;
    const response = await fetch(`/commands/${commandId}`);
    const data = await response.json();
    document.getElementById("cmd-result").textContent = JSON.stringify(data, null, 2);
}
```

### Step 3: Test it

Start the app. Issue a lock command to any vehicle. Copy the `id` from the response. Paste it into the "Command ID" input. Click "Fetch". Confirm the command record appears.

No Python files change except the template and the JavaScript file. The `GET /commands/{command_id}` endpoint already exists in `app/api/routes/commands.py`.

---

## Exercise 5: Add an Architecture Test for a New Forbidden Import

This exercise adds an architecture test that prevents `app/api/routes/` from importing from `app/composition/` directly.

### Step 1: Write the test

Add to `tests/architecture/test_layer_direction.py`:

```python
API_ROUTES_DIR = os.path.join(BASE, 'app', 'api', 'routes')

def test_api_routes_do_not_import_composition():
    for fp in get_python_files(API_ROUTES_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.composition'), \
                f"{fp} imports app.composition — use Depends() instead of importing Container directly"
```

### Step 2: Run the test

```bash
pytest tests/architecture/test_layer_direction.py::test_api_routes_do_not_import_composition
```

It should pass — no route file imports `app.composition`.

### Step 3: Verify the guard works

Add `from app.composition.container import Container` to `app/api/routes/commands.py`. Run the test. Observe the failure. Remove the import.

---

## Exercise 6: Write a Dependency Override Test for the Telemetry Use Case

This exercise practices the dependency override pattern from `docs/09_dependency_injection.md`.

### Step 1: Create the test

Add to `tests/integration/api/test_dependency_override.py`:

```python
from app.api.dependencies import get_ingest_telemetry_use_case
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId
from datetime import datetime, timezone

def make_stub_snapshot():
    return TelemetrySnapshot(
        vehicle_id=VehicleId("VH-STUB"),
        speed_kph=42.0,
        battery_percent=75.0,
        odometer_km=12345.0,
        door_locked=False,
        cabin_temperature_c=25.0,
        timestamp=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

def test_telemetry_dependency_override():
    app = create_app()

    class StubIngestUseCase:
        def execute(self, vehicle_id, speed_kph, battery_percent, odometer_km, door_locked, cabin_temperature_c):
            return make_stub_snapshot()

    app.dependency_overrides[get_ingest_telemetry_use_case] = lambda: StubIngestUseCase()

    with TestClient(app) as client:
        r = client.post("/vehicles/VH-STUB/telemetry", json={
            "speed_kph": 0, "battery_percent": 0, "odometer_km": 0,
            "door_locked": True, "cabin_temperature_c": 0,
        })

    assert r.status_code == 201
    data = r.json()
    assert data["speed_kph"] == 42.0
    assert data["battery_percent"] == 75.0
    assert data["vehicle_id"] == "VH-STUB"
```

### Step 2: Run it

```bash
pytest tests/integration/api/test_dependency_override.py::test_telemetry_dependency_override
```

### Step 3: Understand what is being tested

This test verifies that:

- The route correctly passes all telemetry fields to the use case's `execute()` method.
- The `_to_telemetry_response()` helper maps all fields correctly.
- The HTTP response has status 201 and the correct JSON shape.

The stub use case ignores the input and returns a fixed snapshot, so the test is purely about the HTTP layer, not the business logic.

---

## General Exercise Guidance

When adding any feature to this project, always work from the inside out:

1. **Domain first** — add error types, enums, or models if needed.
2. **Ports** — if you need a new capability from an external system, define the port.
3. **Use case** — implement the application logic.
4. **Infrastructure** — implement the port if needed.
5. **Composition** — wire the new use case into the container.
6. **API** — add the route, schema, and dependency provider.
7. **Tests** — unit test for business rules, integration test for the HTTP endpoint.
8. **Architecture tests** — run `pytest tests/architecture/` and confirm nothing is violated.

Working inside-out ensures that the domain is always clean, the use case is always testable without a running server, and the HTTP layer stays thin.

---

## Review Checklist

- [ ] I can add a new command use case end-to-end following the pattern.
- [ ] I can add a new alert rule without changing any file outside the application layer.
- [ ] I can swap an outbound adapter by changing only `container.py`.
- [ ] I can add a UI section by editing only `templates/index.html` and `app.js`.
- [ ] I can write an architecture test for a new import rule.
- [ ] I can write a dependency override test that isolates the HTTP layer.
