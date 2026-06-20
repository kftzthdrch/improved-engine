# Chapter 04: Domain Layer

## Learning Objective

Understand what lives in `app/domain/`, why domain models use plain Python dataclasses instead of Pydantic, why value objects validate themselves, and why no framework imports are allowed here.

---

## What the Domain Layer Is

The domain layer is the innermost ring of the hexagon. It contains the business concepts and business rules of the system, expressed entirely in plain Python.

The domain layer has exactly zero external dependencies. It does not import FastAPI. It does not import Pydantic. It does not import SQLAlchemy. It does not even import from `app/application/` or `app/infrastructure/`. If you deleted every other folder in the project, the domain layer would still run without error.

Files: `app/domain/`

---

## Errors

File: `app/domain/errors.py`

All domain errors inherit from a single base class:

```python
class DomainError(Exception):
    pass

class InvalidVehicleIdError(DomainError):
    pass

class InvalidCommandError(DomainError):
    pass

class CommandRejectedError(DomainError):
    pass

class CommandNotFoundError(DomainError):
    pass

class TelemetryNotFoundError(DomainError):
    pass

class TripAlreadyActiveError(DomainError):
    pass

class TripNotFoundError(DomainError):
    pass

class DiagnosticCodeNotFoundError(DomainError):
    pass

class AlertNotFoundError(DomainError):
    pass
```

The exception handler in `app/api/exception_handlers.py` catches `DomainError` and maps each subclass to an HTTP status code. The domain itself never knows about HTTP — it just raises a Python exception and trusts the adapter layer to handle it appropriately.

---

## Enums

File: `app/domain/enums.py`

Enums define the controlled vocabularies for the system:

```python
class CommandType(str, Enum):
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"
    START_CLIMATE = "START_CLIMATE"
    STOP_CLIMATE = "STOP_CLIMATE"
    SET_CABIN_TEMPERATURE = "SET_CABIN_TEMPERATURE"
    FLASH_LIGHTS = "FLASH_LIGHTS"
    HONK_HORN = "HONK_HORN"
    OPEN_TRUNK = "OPEN_TRUNK"
    CLOSE_WINDOWS = "CLOSE_WINDOWS"

class CommandStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"

class AlertType(str, Enum):
    LOW_BATTERY = "LOW_BATTERY"
    CABIN_OVERHEAT = "CABIN_OVERHEAT"
    VEHICLE_MOVING = "VEHICLE_MOVING"
    DOOR_UNLOCKED = "DOOR_UNLOCKED"
    STALE_TELEMETRY = "STALE_TELEMETRY"
```

Inheriting from both `str` and `Enum` means the enum values serialize to their string representation automatically. FastAPI's Pydantic schemas can accept these values in JSON without any extra conversion.

---

## Value Objects

Directory: `app/domain/value_objects/`

A value object is an immutable wrapper around a primitive that enforces its own invariants. In this project all value objects are frozen dataclasses.

### VehicleId

File: `app/domain/value_objects/vehicle_id.py`

```python
@dataclass(frozen=True)
class VehicleId:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise InvalidVehicleIdError("Vehicle ID must not be empty")
        object.__setattr__(self, "value", self.value.strip().upper())
```

`frozen=True` means the instance is immutable — once created, `value` cannot be changed. `__post_init__` runs immediately after `__init__`. It raises `InvalidVehicleIdError` if the string is empty or whitespace, and normalizes the value to uppercase. `object.__setattr__` is required to bypass the frozen constraint during `__post_init__` initialization.

The result: you can never have a `VehicleId` with an empty string or inconsistent casing. Any code that holds a `VehicleId` is guaranteed to hold a valid one.

### Temperature

File: `app/domain/value_objects/temperature.py`

```python
@dataclass(frozen=True)
class Temperature:
    celsius: float

    def __post_init__(self):
        if not (-50 <= self.celsius <= 100):
            raise InvalidCommandError(f"Temperature {self.celsius}°C is outside realistic range")
```

The range check is a domain rule: temperatures outside -50 to 100 °C are not physically realistic for a vehicle cabin sensor.

### Speed, BatteryPercent, Odometer

Similar pattern in `app/domain/value_objects/speed.py`, `battery_percent.py`, and `odometer.py`:

- `Speed` rejects negative values.
- `BatteryPercent` rejects values outside 0–100.
- `Odometer` rejects negative values.

All are frozen dataclasses with `__post_init__` validation.

---

## Domain Models

Directory: `app/domain/models/`

Domain models are mutable dataclasses that represent business entities with lifecycle and behavior.

### Command

File: `app/domain/models/command.py`

```python
@dataclass
class Command:
    id: CommandId
    vehicle_id: VehicleId
    command_type: CommandType
    status: CommandStatus
    created_at: datetime
    updated_at: datetime
    payload: dict = field(default_factory=dict)
    failure_reason: str | None = None

    def mark_sent(self, updated_at: datetime) -> None: ...
    def mark_succeeded(self, updated_at: datetime) -> None: ...
    def mark_failed(self, reason: str, updated_at: datetime) -> None: ...
    def mark_rejected(self, reason: str, updated_at: datetime) -> None: ...
```

`Command` is *not* frozen — its status and failure reason change over its lifetime. The lifecycle methods (`mark_succeeded`, `mark_failed`, etc.) are domain behavior: they know what it means for a command to succeed or fail. The use case calls these methods; it does not manipulate the fields directly.

### TelemetrySnapshot

File: `app/domain/models/telemetry.py`

```python
@dataclass(frozen=True)
class TelemetrySnapshot:
    vehicle_id: VehicleId
    speed_kph: float
    battery_percent: float
    odometer_km: float
    door_locked: bool
    cabin_temperature_c: float
    timestamp: datetime
```

Snapshots are immutable — they represent a moment in time. You never modify a past reading; you create a new one.

### TripSession

File: `app/domain/models/trip.py`

```python
@dataclass
class TripSession:
    id: TripId
    vehicle_id: VehicleId
    status: TripStatus
    started_at: datetime
    start_odometer_km: float
    ended_at: datetime | None = None
    end_odometer_km: float | None = None

    @property
    def distance_km(self) -> float | None:
        if self.end_odometer_km is not None:
            return self.end_odometer_km - self.start_odometer_km
        return None
```

`distance_km` is a computed property — pure domain logic. It derives a value from existing fields with no side effects.

### MaintenanceState

File: `app/domain/models/maintenance.py`

```python
@dataclass
class MaintenanceState:
    vehicle_id: VehicleId
    last_service_odometer_km: float = 0.0
    last_tire_check_odometer_km: float = 0.0
    ...

    SERVICE_INTERVAL_KM = 15000
    TIRE_CHECK_INTERVAL_KM = 10000

    def is_service_due(self, current_odometer_km: float) -> bool:
        return (current_odometer_km - self.last_service_odometer_km) >= self.SERVICE_INTERVAL_KM
```

The service interval (15,000 km) is a domain constant defined on the model class. The check whether service is due is a method on the model. Both belong in the domain because they are pure business rules that do not depend on any framework.

---

## Why No Pydantic in the Domain

Pydantic is a data validation and serialization library designed for HTTP APIs. It adds concepts like JSON serialization, OpenAPI schema generation, and HTTP-friendly field aliases. None of those concepts belong in the domain.

If domain models were Pydantic `BaseModel` subclasses:

- They would depend on Pydantic, meaning the domain would have an external dependency.
- Tests would need Pydantic installed.
- Moving to a different web framework would require changing domain models.
- The architecture tests in `tests/architecture/test_forbidden_imports.py` would fail immediately: `test_domain_does_not_import_pydantic` scans every file in `app/domain/` and asserts that none of them import `pydantic`.

Instead, domain models use Python's standard `dataclasses`. When the HTTP layer needs to return a domain object, it maps it manually to a Pydantic response schema. See `docs/11_pydantic_schemas.md` for the mapping pattern.

---

## Why No FastAPI in the Domain

The same logic applies to FastAPI. Domain models must be callable from any context — a command-line script, a background job, a unit test, a message queue consumer — not just HTTP requests.

Architecture test: `test_domain_does_not_import_fastapi` in `tests/architecture/test_forbidden_imports.py`.

---

## Why Frozen Dataclasses for Value Objects

Value objects represent concepts whose identity is their value, not their instance. Two `VehicleId("VH-001")` instances should be equal because their `value` is equal — and frozen dataclasses give you that equality for free via `__eq__`.

Frozen dataclasses also prevent accidental mutation. A `VehicleId` should never change after creation. If code tried to write `my_vehicle_id.value = "something else"` on a frozen dataclass, Python would raise a `FrozenInstanceError` immediately.

---

## Anti-Patterns to Avoid

**Importing `fastapi` or `pydantic` in any file under `app/domain/`.** This breaks the architecture test and — more importantly — breaks the promise that domain logic is framework-independent.

**Putting validation logic in the application layer instead of the domain.** If `VehicleId` accepted any string without validation, every caller would have to remember to validate it separately. By validating in `__post_init__`, the invariant is enforced once, everywhere.

**Making `TelemetrySnapshot` mutable.** Sensor readings are historical facts. If a snapshot were mutable, one piece of code could silently alter another's view of the vehicle's history.

**Using `@property` to call a repository inside a domain model.** A property like `command.vehicle` that looks up a vehicle from a repository would inject an infrastructure concern into the domain. Domain models only work with data they already hold.

---

## Exercises

1. Open `tests/unit/domain/test_value_objects.py`. Run the tests. Read each assertion and find the matching validation in the value object file it exercises.

2. Try setting `vid.value = "other"` on a `VehicleId` instance in a Python REPL. Observe the `FrozenInstanceError`. Try the same on a `Command` instance (not frozen). Note the difference.

3. Add a new value object `FuelPercent` in `app/domain/value_objects/fuel_percent.py` that rejects values outside 0–100. Write a test for it in `tests/unit/domain/test_value_objects.py`. Run `pytest tests/architecture/` to confirm no rules are violated.

---

## Review Checklist

- [ ] I can explain why domain models use dataclasses instead of Pydantic.
- [ ] I can explain why value objects are frozen.
- [ ] I know what `__post_init__` does and when it runs.
- [ ] I understand what domain errors are and how they reach the HTTP layer.
- [ ] I can name all six domain models and three value objects.
