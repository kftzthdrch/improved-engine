# Chapter 11: Pydantic Schemas

## Learning Objective

Understand why Pydantic is used only at the HTTP boundary, how request and response schemas differ from domain models, and why the manual mapping step between domain objects and schemas is a feature rather than a flaw.

---

## Pydantic's Role in This Project

Pydantic is a data validation and serialization library. In this project it has one and only one job: define the shape of HTTP request bodies and HTTP response bodies.

Pydantic is not used for:

- Domain model validation (that is done with dataclass `__post_init__`).
- Business rule enforcement (that is done in `CommandPolicy` and other services).
- Data storage (in-memory repositories store domain dataclasses).
- Inter-layer communication (use cases receive and return domain types).

The architecture tests enforce this:

- `test_domain_does_not_import_pydantic` scans `app/domain/` — no Pydantic allowed.
- `test_application_does_not_import_pydantic` scans `app/application/` — no Pydantic allowed.

All Pydantic schemas live in `app/api/schemas/`.

---

## Request Schemas

Request schemas parse and validate the JSON body sent by the client.

### SetCabinTemperatureRequest

File: `app/api/schemas/command_schemas.py`

```python
class SetCabinTemperatureRequest(BaseModel):
    target_celsius: float
```

When a client sends `{"target_celsius": 22.0}`, FastAPI uses this schema to parse the JSON and inject a `SetCabinTemperatureRequest` instance into the route handler. If the client sends `{"target_celsius": "hot"}`, Pydantic raises a validation error and FastAPI returns HTTP 422 automatically.

### HonkHornRequest

```python
class HonkHornRequest(BaseModel):
    quiet_mode: bool = False
```

`quiet_mode` has a default value of `False`, so the field is optional in the request body. A client can omit it entirely.

### TelemetryIngestRequest

File: `app/api/schemas/telemetry_schemas.py`

```python
class TelemetryIngestRequest(BaseModel):
    speed_kph: float
    battery_percent: float
    odometer_km: float
    door_locked: bool
    cabin_temperature_c: float
```

All five fields are required. Pydantic validates that each is present and has the right type. Domain-level range validation (e.g., speed cannot be negative) happens later, in `TelemetryValidation` inside the use case.

---

## Response Schemas

Response schemas define the shape of the JSON body returned to the client.

### CommandResponse

File: `app/api/schemas/command_schemas.py`

```python
class CommandResponse(BaseModel):
    id: str
    vehicle_id: str
    command_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    payload: dict = {}
    failure_reason: str | None = None
```

Notice that `id`, `vehicle_id`, `command_type`, and `status` are all `str`. The domain uses `CommandId`, `VehicleId`, `CommandType` (enum), and `CommandStatus` (enum). The mapping function in the route handler unwraps these:

```python
def _to_response(cmd) -> CommandResponse:
    return CommandResponse(
        id=cmd.id.value,
        vehicle_id=cmd.vehicle_id.value,
        command_type=cmd.command_type.value,
        status=cmd.status.value,
        ...
    )
```

### TelemetryResponse

File: `app/api/schemas/telemetry_schemas.py`

```python
class TelemetryResponse(BaseModel):
    vehicle_id: str
    speed_kph: float
    battery_percent: float
    odometer_km: float
    door_locked: bool
    cabin_temperature_c: float
    timestamp: datetime
```

`VehicleStatusResponse` has the identical shape. They are separate classes because their semantic meaning differs — "latest status" vs "a history entry" — even if the fields happen to be the same today. They may diverge in the future.

### AlertResponse

File: `app/api/schemas/alert_schemas.py`

```python
class AlertResponse(BaseModel):
    vehicle_id: str
    alert_type: str
    message: str
    triggered_at: datetime
    active: bool
```

### ErrorResponse

File: `app/api/schemas/error_schemas.py`

```python
class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

`ErrorResponse` is not used as a `response_model` on any route — it documents the shape that `_error_body()` in `exception_handlers.py` produces.

---

## Why Schemas Are Not Domain Models

A domain model and a Pydantic schema serve fundamentally different concerns.

| Concern | Domain Model | Pydantic Schema |
| ------- | ------------ | --------------- |
| Purpose | Represent a business concept | Represent an HTTP payload |
| Validation | Business invariants | Type and format |
| Serialization | Not needed | JSON in/out |
| Framework | Pure Python | Pydantic |
| Layer | `app/domain/` | `app/api/schemas/` |
| Mutability | Sometimes mutable | Immutable by default |

If you made `Command` a Pydantic `BaseModel`:

- It would import Pydantic (domain layer rule violation).
- Pydantic's serialization would expose all internal fields, including ones meant to be internal.
- You could not add methods like `mark_succeeded()` easily (Pydantic v1 did not support arbitrary methods cleanly; Pydantic v2 does but conflates HTTP concerns with domain behavior).
- Changing the API response shape (e.g., renaming `vehicle_id` to `vin` in the response) would require changing the domain model.

By keeping them separate, the API response shape and the domain model shape can evolve independently.

---

## The Manual Mapping Step

The mapping from domain object to response schema is explicit and manual:

```python
# app/api/routes/commands.py

def _to_response(cmd) -> CommandResponse:
    return CommandResponse(
        id=cmd.id.value,
        vehicle_id=cmd.vehicle_id.value,
        command_type=cmd.command_type.value,
        status=cmd.status.value,
        created_at=cmd.created_at,
        updated_at=cmd.updated_at,
        payload=cmd.payload,
        failure_reason=cmd.failure_reason,
    )
```

Some developers consider this boilerplate. It is not. It is the adapter layer doing its job: translating between two representations. The benefits:

- **Explicit control** — you choose exactly which fields appear in the response. You can exclude internal fields. You can rename fields for the API without renaming them in the domain.
- **No leakage** — adding a new field to `Command` (e.g., an internal audit field) does not automatically expose it in the API. You must explicitly add it to the mapping.
- **Independent evolution** — the API response can be versioned and restructured without touching the domain.
- **Type safety** — the function signature `def _to_response(cmd) -> CommandResponse` makes it clear what goes in and what comes out.

---

## Schema Inventory

| Schema file | Request schemas | Response schemas |
| ----------- | --------------- | ---------------- |
| `command_schemas.py` | `SetCabinTemperatureRequest`, `HonkHornRequest` | `CommandResponse` |
| `telemetry_schemas.py` | `TelemetryIngestRequest` | `TelemetryResponse`, `VehicleStatusResponse` |
| `alert_schemas.py` | — | `AlertResponse` |
| `trip_schemas.py` | — | `TripResponse`, `TripSummaryResponse` |
| `maintenance_schemas.py` | — | `MaintenanceStatusResponse` |
| `diagnostic_schemas.py` | `DiagnosticIngestRequest` | `DiagnosticCodeResponse` |
| `eligibility_schemas.py` | — | `CommandEligibilityResponse` |
| `error_schemas.py` | — | `ErrorResponse`, `ErrorDetail` |

---

## Anti-Patterns to Avoid

**Using domain models as Pydantic models.** This merges two concerns that should be separate. See the comparison table above.

**Returning domain objects from route handlers without mapping.** FastAPI will try to serialize a plain Python dataclass and may fail or expose unexpected fields. Always map explicitly.

**Putting business validation in schemas.** A Pydantic validator that checks `if target_celsius < 16` in the schema is putting business logic in the API layer. That rule belongs in `CommandPolicy.enforce_cabin_temperature_range()`.

**Having schemas import from the domain.** Schemas should be independent. They work with plain Python types (str, float, datetime). If a schema imported `VehicleId` it would couple the API layer to the domain's value object structure.

---

## Exercises

1. Add a field `command_count: int` to `CommandResponse`. Do not add it to the domain `Command` model. Modify `_to_response()` to hardcode it as `0` for now. Run the tests and see that no architecture test breaks. Now add a real implementation that counts commands (if you have a way to pass the count).

2. Change `quiet_mode: bool = False` in `HonkHornRequest` to `quiet_mode: bool` (remove the default). Run the app. Try calling the horn endpoint without a body. Observe the 422 error Pydantic returns. Revert the change.

3. Open `/docs` with the app running. Find the `TelemetryIngestRequest` schema. Note that Pydantic field names become the JSON property names. Then look at the response schema for telemetry history. Confirm each property name matches the field in `TelemetryResponse`.

---

## Review Checklist

- [ ] I can explain why Pydantic is not allowed in `app/domain/` or `app/application/`.
- [ ] I know the difference between a request schema and a response schema.
- [ ] I understand why domain models and Pydantic schemas are separate.
- [ ] I can write a `_to_response()` mapping function for a new domain model.
- [ ] I know why the manual mapping step is a feature, not boilerplate.
