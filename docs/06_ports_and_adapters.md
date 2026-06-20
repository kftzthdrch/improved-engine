# Chapter 06: Ports and Adapters

## Learning Objective

Understand every port (interface) in this project, what it requires, which concrete adapter implements it, and how swapping an adapter works in practice without changing any use case code.

---

## What a Port Is

A port is an interface — a contract that the application layer defines and that outbound adapters must satisfy.

In this project ports are defined using Python's `typing.Protocol`. A Protocol specifies method signatures without providing any implementation. Any object that has those methods with the right signatures satisfies the protocol, without needing to inherit from it (structural subtyping).

```python
# app/application/ports/clock.py
from typing import Protocol
from datetime import datetime

class Clock(Protocol):
    def now(self) -> datetime: ...
```

Any class that has a `now()` method returning a `datetime` satisfies `Clock`. It does not need to inherit from `Clock`. Python checks this structurally, not nominally.

---

## The Nine Ports

### 1. CommandRepository

File: `app/application/ports/command_repository.py`

```python
class CommandRepository(Protocol):
    def save(self, command: Command) -> None: ...
    def get(self, command_id: CommandId) -> Command | None: ...
    def list_for_vehicle(self, vehicle_id: VehicleId) -> list[Command]: ...
```

Concrete adapter: `app/infrastructure/persistence/in_memory_command_repository.py`

Used by: all command use cases (lock, unlock, start climate, etc.)

### 2. TelemetryRepository

File: `app/application/ports/telemetry_repository.py`

```python
class TelemetryRepository(Protocol):
    def save(self, snapshot: TelemetrySnapshot) -> None: ...
    def get_latest(self, vehicle_id: VehicleId) -> TelemetrySnapshot | None: ...
    def get_history(self, vehicle_id: VehicleId) -> list[TelemetrySnapshot]: ...
```

Concrete adapter: `app/infrastructure/persistence/in_memory_telemetry_repository.py`

Used by: `IngestTelemetryUseCase`, `GetVehicleStatusUseCase`, `GetTelemetryHistoryUseCase`, `LockVehicleUseCase`, `StartClimateUseCase`, `OpenTrunkUseCase`, `StartTripUseCase`, `EndTripUseCase`, `EvaluateVehicleAlertsUseCase`, `GetCommandEligibilityUseCase`, `GetMaintenanceStatusUseCase`, `RecordServiceResetUseCase`

### 3. AlertRepository

File: `app/application/ports/alert_repository.py`

Handles saving and querying active vehicle alerts.

Concrete adapter: `app/infrastructure/persistence/in_memory_alert_repository.py`

Used by: `EvaluateVehicleAlertsUseCase`, `GetActiveAlertsUseCase`, `ClearVehicleAlertUseCase`

### 4. TripRepository

File: `app/application/ports/trip_repository.py`

Handles saving and querying trip sessions.

Concrete adapter: `app/infrastructure/persistence/in_memory_trip_repository.py`

Used by: `StartTripUseCase`, `EndTripUseCase`, `GetCurrentTripUseCase`, `GetTripSummaryUseCase`

### 5. MaintenanceRepository

File: `app/application/ports/maintenance_repository.py`

Handles saving and querying maintenance state per vehicle.

Concrete adapter: `app/infrastructure/persistence/in_memory_maintenance_repository.py`

Used by: `GetMaintenanceStatusUseCase`, `RecordServiceResetUseCase`

### 6. DiagnosticRepository

File: `app/application/ports/diagnostic_repository.py`

Handles saving and querying diagnostic codes.

Concrete adapter: `app/infrastructure/persistence/in_memory_diagnostic_repository.py`

Used by: `IngestDiagnosticCodesUseCase`, `GetActiveDiagnosticCodesUseCase`, `ClearDiagnosticCodeUseCase`

### 7. VehicleCommandGateway

File: `app/application/ports/vehicle_command_gateway.py`

```python
class GatewayResult:
    def __init__(self, success: bool, error_message: str | None = None):
        self.success = success
        self.error_message = error_message

class VehicleCommandGateway(Protocol):
    def send(
        self,
        vehicle_id: VehicleId,
        command_id: CommandId,
        command_type: CommandType,
        payload: dict,
    ) -> GatewayResult: ...
```

This port represents the channel to the physical vehicle. In production this would be replaced by an MQTT, cellular, or proprietary gateway.

Concrete adapter: `app/infrastructure/vehicle_gateway/fake_vehicle_gateway.py` (`FakeVehicleCommandGateway`)

Used by: all command use cases

### 8. Clock

File: `app/application/ports/clock.py`

```python
class Clock(Protocol):
    def now(self) -> datetime: ...
```

Concrete adapter: `app/infrastructure/time/system_clock.py` (`SystemClock`)

This port exists so tests can inject a fake clock and get deterministic timestamps. Without it, `datetime.now()` called directly in use cases would produce different values on every test run, making assertions on timestamps impossible.

Used by: `IngestTelemetryUseCase`, `LockVehicleUseCase`, `StartTripUseCase`, `EndTripUseCase`, `EvaluateVehicleAlertsUseCase`, `RecordServiceResetUseCase`, `IngestDiagnosticCodesUseCase`

### 9. IdGenerator

File: `app/application/ports/id_generator.py`

```python
class IdGenerator(Protocol):
    def new_command_id(self) -> CommandId: ...
    def new_trip_id(self) -> TripId: ...
```

Concrete adapter: `app/infrastructure/ids/uuid_generator.py` (`UuidGenerator`)

This port exists so tests can inject a deterministic ID generator (e.g., always returning `CommandId("test-id-001")`) instead of random UUIDs. Predictable IDs make test assertions on command IDs possible.

Used by: all command use cases, `StartTripUseCase`

---

## Port Summary Table

| Port | File | Concrete Adapter |
| ---- | ---- | ---------------- |
| `CommandRepository` | `ports/command_repository.py` | `in_memory_command_repository.py` |
| `TelemetryRepository` | `ports/telemetry_repository.py` | `in_memory_telemetry_repository.py` |
| `AlertRepository` | `ports/alert_repository.py` | `in_memory_alert_repository.py` |
| `TripRepository` | `ports/trip_repository.py` | `in_memory_trip_repository.py` |
| `MaintenanceRepository` | `ports/maintenance_repository.py` | `in_memory_maintenance_repository.py` |
| `DiagnosticRepository` | `ports/diagnostic_repository.py` | `in_memory_diagnostic_repository.py` |
| `VehicleCommandGateway` | `ports/vehicle_command_gateway.py` | `fake_vehicle_gateway.py` |
| `Clock` | `ports/clock.py` | `system_clock.py` |
| `IdGenerator` | `ports/id_generator.py` | `uuid_generator.py` |

---

## How Adapter Swapping Works

Here is the complete set of steps to replace `FakeVehicleCommandGateway` with a real MQTT gateway, without changing any use case:

**Step 1.** Create `app/infrastructure/vehicle_gateway/mqtt_vehicle_gateway.py`:

```python
# This is a hypothetical example
import paho.mqtt.client as mqtt

class MQTTVehicleCommandGateway:
    def __init__(self, broker_host: str, broker_port: int):
        self._client = mqtt.Client()
        self._client.connect(broker_host, broker_port)

    def send(self, vehicle_id, command_id, command_type, payload) -> GatewayResult:
        topic = f"vehicles/{vehicle_id.value}/commands"
        message = {"command_id": command_id.value, "type": command_type.value, **payload}
        result = self._client.publish(topic, json.dumps(message))
        return GatewayResult(success=result.rc == mqtt.MQTT_ERR_SUCCESS)
```

This class satisfies `VehicleCommandGateway` structurally — it has a `send` method with the right signature.

**Step 2.** Edit `app/composition/container.py` to use the new gateway:

```python
# Before
self.gateway = FakeVehicleCommandGateway()

# After
self.gateway = MQTTVehicleCommandGateway(broker_host="localhost", broker_port=1883)
```

**Step 3.** Done.

`LockVehicleUseCase`, `StartClimateUseCase`, and every other command use case continue to work without modification. They call `self.gateway.send(...)` — they do not know or care whether the gateway sends over MQTT or pretends to.

The same pattern applies to any port:

- Replace all six in-memory repositories with SQLAlchemy repositories by changing six lines in `container.py`.
- Replace `SystemClock` with a clock that reads from a time server by changing one line.
- Replace `UuidGenerator` with a sequential ID generator in tests by injecting a stub.

---

## Protocol vs ABC

Python offers two ways to define an interface: `typing.Protocol` and `abc.ABC`.

`Protocol` uses structural subtyping — if an object has the right methods, it satisfies the protocol. No inheritance required. This is ideal for adapters because infrastructure classes do not need to know about the port they are implementing.

`abc.ABC` uses nominal subtyping — the class must explicitly inherit from the ABC and implement all `@abstractmethod` methods. This is an explicit declaration.

This project uses `Protocol` because:

- Infrastructure classes have no dependency on `app/application/ports/`. They just happen to have the right methods.
- You can satisfy a port with a test stub that is just a plain object with the right methods — no imports needed.
- Python's type checker (mypy or pyright) can verify Protocol conformance statically.

---

## Anti-Patterns to Avoid

**Concrete imports in use cases.** If `LockVehicleUseCase` imported `InMemoryCommandRepository` instead of declaring `command_repo: CommandRepository`, swapping the repository would require editing the use case. The port is the firewall.

**Methods on a port that return infrastructure types.** If `TelemetryRepository.get_latest` returned a SQLAlchemy row instead of a `TelemetrySnapshot`, the application layer would need to know about SQLAlchemy. Ports must return domain types only.

**Putting adapter configuration in a port.** The `Clock` port defines `now() -> datetime`. It does not define `connect(url: str)`. Connection details belong in the adapter, not the interface.

---

## Exercises

1. Read `app/application/ports/vehicle_command_gateway.py`. Then read `app/infrastructure/vehicle_gateway/fake_vehicle_gateway.py`. Confirm that `FakeVehicleCommandGateway` has a `send` method with the same signature as the Protocol. Python does not enforce this at import time — only a type checker or test confirms it.

2. Write a `SlowFakeVehicleCommandGateway` class (in a test file or scratch file) that sleeps for 0.1 seconds before returning `GatewayResult(success=True)`. Inject it into a `LockVehicleUseCase` and call `execute()`. The use case should work without any changes.

3. Add a new method `count_for_vehicle(self, vehicle_id: VehicleId) -> int` to the `CommandRepository` Protocol. Then add the method to `InMemoryCommandRepository`. Run the tests. Observe that the architecture tests still pass and the integration tests still pass.

---

## Review Checklist

- [ ] I can name all nine ports from memory.
- [ ] I understand why `Protocol` is preferred over `abc.ABC` in this project.
- [ ] I can describe the exact steps to swap an outbound adapter without touching use cases.
- [ ] I know why `Clock` and `IdGenerator` are ports and not just `datetime.now()` / `uuid.uuid4()` calls.
- [ ] I understand the difference between a port (interface) and an adapter (concrete implementation).
