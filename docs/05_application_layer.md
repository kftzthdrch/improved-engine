# Chapter 05: Application Layer

## Learning Objective

Understand use cases, application services, and ports in `app/application/`: why there is one class per use case, why use cases are framework-free dataclasses with `execute()` methods, and what the application services (`CommandPolicy`, `TelemetryValidation`, `AlertRules`, `MaintenanceRules`) do.

---

## What the Application Layer Is

The application layer sits between the domain (center) and the adapters (outer ring). It orchestrates domain objects to fulfill user intentions.

The application layer:

- Knows about domain models, value objects, and errors.
- Knows about ports (interfaces) but not about concrete infrastructure.
- Does not know about FastAPI, Pydantic, HTTP, or databases.

The architecture tests in `tests/architecture/test_forbidden_imports.py` enforce this:

- `test_application_does_not_import_fastapi`
- `test_application_does_not_import_pydantic`
- `test_application_does_not_import_infrastructure`
- `test_application_does_not_import_api`

Files: `app/application/`

---

## Use Cases

Directory: `app/application/use_cases/`

A use case represents a single user action. There is one class per use case, one file per class. Each class has a single public method: `execute()`.

### Why One Class Per Use Case?

The alternative — a single `VehicleService` class with 20+ methods — creates several problems:

- The class grows without bound as the system grows.
- Every constructor injection is shared across all methods, even when unneeded.
- Tests for one method must construct the entire service including dependencies it does not use.
- Reading a single use case requires navigating a large file.

One class per use case gives you a file you can read in 30 seconds, a constructor that lists exactly the dependencies the action needs, and a test that constructs only what is required.

### The execute() Pattern

```python
# app/application/use_cases/commands/lock_vehicle.py
@dataclass
class LockVehicleUseCase:
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
            command_type=CommandType.LOCK,
            status=CommandStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        latest = self.telemetry_repo.get_latest(vehicle_id)
        try:
            self.policy.enforce_not_moving(latest)
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

Reading this method top to bottom tells you the entire story of what happens when a lock command is issued:

1. Generate a new command ID and record the current time.
2. Create a `PENDING` command.
3. Fetch the latest telemetry.
4. Check the policy — if the vehicle is moving, mark the command rejected, save it, and re-raise.
5. Save the command.
6. Send through the gateway.
7. Mark succeeded or failed based on the gateway result.
8. Save the final state and return.

Notice what is absent: no FastAPI, no Pydantic, no HTTP status codes, no database queries. The use case is pure Python orchestration.

### Use Case as Dataclass

Using `@dataclass` for use cases is a deliberate choice. The `@dataclass` decorator generates `__init__`, which means:

- Dependencies are injected via constructor — they are explicit.
- The composition root (`app/composition/container.py`) can create use cases with plain Python: `LockVehicleUseCase(command_repo=..., gateway=..., ...)`.
- There is no IoC container magic, no decorator scanning, no runtime reflection.

### Full Inventory of Use Cases

**Commands (9):** `lock_vehicle`, `unlock_vehicle`, `start_climate`, `stop_climate`, `set_cabin_temperature`, `flash_lights`, `honk_horn`, `open_trunk`, `close_windows`

**Telemetry (3):** `ingest_telemetry`, `get_vehicle_status`, `get_telemetry_history`

**Alerts (3):** `evaluate_vehicle_alerts`, `get_active_alerts`, `clear_vehicle_alert`

**Trips (4):** `start_trip`, `end_trip`, `get_current_trip`, `get_trip_summary`

**Maintenance (2):** `get_maintenance_status`, `record_service_reset`

**Diagnostics (3):** `ingest_diagnostic_codes`, `get_active_diagnostic_codes`, `clear_diagnostic_code`

**Eligibility (1):** `get_command_eligibility`

Total: 25 use cases, each in its own file.

---

## Application Services

Directory: `app/application/services/`

Application services are stateless helper objects that encapsulate business rules used by multiple use cases.

### CommandPolicy

File: `app/application/services/command_policy.py`

```python
class CommandPolicy:
    def enforce_not_moving(self, latest_telemetry: TelemetrySnapshot | None) -> None:
        if latest_telemetry and latest_telemetry.speed_kph > 0:
            raise CommandRejectedError("Vehicle is moving")

    def enforce_battery_sufficient(self, latest_telemetry: TelemetrySnapshot | None, min_percent: float = 20.0) -> None:
        if latest_telemetry and latest_telemetry.battery_percent < min_percent:
            raise CommandRejectedError(f"Battery too low: {latest_telemetry.battery_percent}%")

    def enforce_cabin_temperature_range(self, target_celsius: float) -> None:
        if not (16.0 <= target_celsius <= 30.0):
            raise CommandRejectedError(f"Target temperature {target_celsius}°C is outside allowed range 16–30°C")

    def enforce_quiet_mode_off(self, quiet_mode: bool) -> None:
        if quiet_mode:
            raise CommandRejectedError("Quiet mode is active")
```

Multiple command use cases share these rules. `LockVehicleUseCase` calls `enforce_not_moving`. `StartClimateUseCase` calls `enforce_not_moving` and `enforce_battery_sufficient`. `HonkHornUseCase` calls `enforce_quiet_mode_off`. Rather than duplicating the rule in each use case, they all receive a `CommandPolicy` instance and call the relevant method.

### TelemetryValidation

File: `app/application/services/telemetry_validation.py`

Validates raw telemetry values before they are saved as a snapshot. Raises `InvalidCommandError` on out-of-range values. Called by `IngestTelemetryUseCase`.

### AlertRules

File: `app/application/services/alert_rules.py`

```python
class AlertRules:
    def evaluate(self, snapshot: TelemetrySnapshot, now: datetime) -> list[AlertType]:
        triggered = []
        if snapshot.battery_percent < 20:
            triggered.append(AlertType.LOW_BATTERY)
        if snapshot.cabin_temperature_c > 45:
            triggered.append(AlertType.CABIN_OVERHEAT)
        if snapshot.speed_kph > 0:
            triggered.append(AlertType.VEHICLE_MOVING)
        if not snapshot.door_locked:
            triggered.append(AlertType.DOOR_UNLOCKED)
        age = now - snapshot.timestamp...
        if age > timedelta(minutes=10):
            triggered.append(AlertType.STALE_TELEMETRY)
        return triggered
```

`EvaluateVehicleAlertsUseCase` passes the latest telemetry snapshot and the current time to `AlertRules.evaluate()` and receives a list of triggered alert types.

### MaintenanceRules

File: `app/application/services/maintenance_rules.py`

Determines whether a service or tire check is due based on the odometer reading. Called by `GetMaintenanceStatusUseCase`.

---

## Ports

Directory: `app/application/ports/`

Ports are `typing.Protocol` classes that define what the application layer needs from the outside world, without specifying how those needs are met.

```python
# app/application/ports/command_repository.py
class CommandRepository(Protocol):
    def save(self, command: Command) -> None: ...
    def get(self, command_id: CommandId) -> Command | None: ...
    def list_for_vehicle(self, vehicle_id: VehicleId) -> list[Command]: ...
```

`LockVehicleUseCase` declares its dependency as `command_repo: CommandRepository`. At runtime the composition root injects `InMemoryCommandRepository`. In a test you could inject any object that has `save`, `get`, and `list_for_vehicle` methods — a stub, a mock, or another in-memory implementation.

See `docs/06_ports_and_adapters.md` for the full port inventory and detailed explanation.

---

## Why Use Cases Are Framework-Free

Consider this test from `tests/unit/application/test_command_policy.py`:

```python
policy = CommandPolicy()

def test_enforce_not_moving_raises_when_moving():
    with pytest.raises(CommandRejectedError):
        policy.enforce_not_moving(make_snapshot(speed=10))
```

No `TestClient`. No HTTP request. No app factory. No lifespan. Just Python.

This is the payoff of keeping the application layer framework-free. You can test every business rule at the speed of a unit test — milliseconds, not seconds.

If `CommandPolicy` imported FastAPI and required an HTTP context, this test would need a running server. The test suite would slow down dramatically, and the business rules would be coupled to the web framework.

---

## Anti-Patterns to Avoid

**A single "service" class with all use cases as methods.** See "Why One Class Per Use Case?" above.

**Importing `InMemoryCommandRepository` in a use case.** The use case must declare its dependency as the port protocol, not the concrete class. The composition root chooses the concrete implementation.

**Calling `datetime.now()` directly in a use case.** Use cases call `self.clock.now()` so that tests can inject a fake clock and get deterministic, reproducible results.

**Calling `uuid.uuid4()` directly in a use case.** Same reason — use `self.id_gen.new_command_id()` so tests can inject a deterministic ID.

**Putting HTTP-level logic (status codes, JSON) in a use case.** Use cases return domain objects. The API layer maps them to HTTP responses.

---

## Exercises

1. Read `app/application/use_cases/commands/start_climate.py`. Compare it to `lock_vehicle.py`. Which policy methods does each call? Why are the policies different?

2. Read `tests/unit/application/test_command_policy.py`. Write one additional test: verify that `enforce_battery_sufficient` passes when battery is exactly 20% (the boundary case).

3. Read `app/application/use_cases/telemetry/ingest_telemetry.py`. Identify the three ports it uses. Trace each one back to its Protocol file and then to its concrete implementation in `app/infrastructure/`.

---

## Review Checklist

- [ ] I can explain why there is one class per use case.
- [ ] I understand what `@dataclass` gives the use case pattern.
- [ ] I know the difference between a use case and an application service.
- [ ] I can name the four application services and their responsibilities.
- [ ] I understand why calling `datetime.now()` directly in a use case is wrong.
