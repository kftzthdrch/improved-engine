# Chapter 08: FastAPI API Layer

## Learning Objective

Understand the structure of the FastAPI API layer: why route handlers are thin, how routers are grouped by domain area, how request schemas map to use case calls, and how use case results map to response schemas.

---

## The API Layer's Single Responsibility

The API layer (`app/api/`) has one job: translate HTTP into use case calls and translate use case results back into HTTP.

A route handler should do exactly three things:

1. Accept the HTTP request (path parameters, query parameters, body).
2. Call the use case.
3. Map the result to a response schema and return it.

If a route handler contains an `if` statement that makes a business decision — "if the vehicle is moving, return 409" — it is doing work that belongs in the use case or domain. Business decisions are made in `app/application/` and `app/domain/`. The API layer is just a translator.

---

## Router Grouping by Domain Area

Each domain area has its own router file in `app/api/routes/`:

| Router file | Tag | Domain area |
| ----------- | --- | ----------- |
| `commands.py` | `commands` | Vehicle command issuance |
| `telemetry.py` | `telemetry` | Sensor data ingest and query |
| `alerts.py` | `alerts` | Alert evaluation and management |
| `trips.py` | `trips` | Trip tracking |
| `maintenance.py` | `maintenance` | Service interval tracking |
| `diagnostics.py` | `diagnostics` | Fault code management |
| `eligibility.py` | `eligibility` | Command eligibility query |
| `health.py` | `health` | Liveness check |
| `ui.py` | `ui` | Dashboard HTML render |

Each router is included in `create_app()` in `app/main.py`.

---

## Thin Route Handler Example

The lock command handler is a good example of a minimal, thin route:

```python
# app/api/routes/commands.py

@router.post("/vehicles/{vehicle_id}/commands/lock", response_model=CommandResponse, status_code=200)
def lock_vehicle(vehicle_id: str = Path(...), use_case=Depends(get_lock_vehicle_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)
```

The entire handler is three lines:

- Accept `vehicle_id` from the URL.
- Call `use_case.execute()` with a domain value object.
- Map the returned `Command` to a `CommandResponse` schema and return it.

No `if` statements. No business rules. No error handling (errors are handled by exception handlers). No repository calls.

---

## Request Schema to Use Case Call

When the request has a body, the handler receives a Pydantic schema instance and passes individual fields to the use case:

```python
# app/api/routes/commands.py

@router.post("/vehicles/{vehicle_id}/commands/climate/temperature", response_model=CommandResponse, status_code=200)
def set_cabin_temperature(body: SetCabinTemperatureRequest, vehicle_id: str = Path(...), use_case=Depends(get_set_cabin_temperature_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id), body.target_celsius)
    return _to_response(cmd)
```

The schema:

```python
# app/api/schemas/command_schemas.py
class SetCabinTemperatureRequest(BaseModel):
    target_celsius: float
```

The route does not validate `target_celsius` — it passes it to the use case, which passes it to `CommandPolicy.enforce_cabin_temperature_range()`. The policy raises `CommandRejectedError` if the value is outside 16–30 °C. The exception handler maps that to HTTP 409.

This separation means:

- The validation rule (16–30 °C allowed range) is defined once, in the application layer.
- If you added a CLI adapter, the same rule would apply without duplicating it.

---

## Use Case Result to Response Schema

Use cases return domain objects. Route handlers map them to Pydantic response schemas using local helper functions:

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

The mapping extracts `.value` from each value object (`cmd.id.value`, `cmd.vehicle_id.value`) because the Pydantic schema works with plain strings and the domain uses typed value objects.

For telemetry:

```python
# app/api/routes/telemetry.py

def _to_telemetry_response(snap) -> TelemetryResponse:
    return TelemetryResponse(
        vehicle_id=snap.vehicle_id.value,
        speed_kph=snap.speed_kph,
        battery_percent=snap.battery_percent,
        odometer_km=snap.odometer_km,
        door_locked=snap.door_locked,
        cabin_temperature_c=snap.cabin_temperature_c,
        timestamp=snap.timestamp,
    )
```

---

## Routes That Handle Lists

When a use case returns a list of domain objects, the handler maps each one:

```python
# app/api/routes/telemetry.py

@router.get("/vehicles/{vehicle_id}/telemetry/history", response_model=list[TelemetryResponse])
def get_telemetry_history(vehicle_id: str = Path(...), use_case=Depends(get_telemetry_history_use_case)):
    history = use_case.execute(VehicleId(vehicle_id))
    return [_to_telemetry_response(s) for s in history]
```

`response_model=list[TelemetryResponse]` tells FastAPI the response is a JSON array of `TelemetryResponse` objects.

---

## Routes That Return No Body

The alert clear endpoint returns HTTP 204 (No Content):

```python
# app/api/routes/alerts.py

@router.delete("/vehicles/{vehicle_id}/alerts/{alert_type}", status_code=204)
def clear_alert(vehicle_id: str = Path(...), alert_type: str = Path(...), use_case=Depends(get_clear_alert_use_case)):
    try:
        at = AlertType(alert_type)
    except ValueError:
        raise AlertNotFoundError(f"Unknown alert type: {alert_type}")
    use_case.execute(VehicleId(vehicle_id), at)
```

Note the `try/except` here — it converts a Python `ValueError` from `AlertType(alert_type)` into a domain error. This is legitimate adapter logic: parsing and validating the URL segment before it reaches the use case. The use case should not receive invalid enum values.

---

## The Health Endpoint

File: `app/api/routes/health.py`

```python
router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    return {"status": "ok"}
```

The simplest possible route — no use case, no schema, no dependency. A health check only needs to confirm the app is running.

---

## Why Routes Do Not Contain Business Logic

If business logic lives in route handlers:

- You cannot test that logic without making an HTTP request.
- CLI, WebSocket, or message queue adapters would need to duplicate the logic.
- The logic is hidden in the HTTP layer rather than being explicitly named as a use case.
- Changing the HTTP API requires carefully extracting business rules that should never have been there.

The discipline of keeping routes thin is what makes the hexagon work. Every decision the system makes is in the use cases and domain — never in the routes.

---

## Anti-Patterns to Avoid

**Business logic in a route handler.** An `if speed > 0: return JSONResponse(409, ...)` in a route is the most common violation. That check belongs in `CommandPolicy`.

**Repository calls in a route handler.** A route that imports and calls `InMemoryCommandRepository` directly bypasses the use case, the policy, and the port. It creates a hidden shortcut that breaks the architecture.

**Returning domain objects directly.** FastAPI cannot automatically serialize `Command` (a dataclass). You must call the mapping function to convert it to a `CommandResponse` (a Pydantic model).

**Sharing a `_to_response` helper across routers.** Each router owns its own mapping helpers. Shared mappers create cross-domain coupling. If `CommandResponse` and `TripResponse` diverge, a shared mapper becomes a maintenance problem.

---

## Exercises

1. Read `app/api/routes/alerts.py` in full. Note where the `try/except ValueError` is. Write one sentence explaining why this `try/except` is appropriate API-layer code rather than a business rule.

2. Add a new field `received_at: datetime` to `TelemetryResponse` in `app/api/schemas/telemetry_schemas.py`. It should always equal the current time (use `datetime.now(timezone.utc)`). Add it to the `_to_telemetry_response` helper. Run the tests and observe which ones fail — why do they fail?

3. Open `/docs` while the app is running. Find the telemetry ingest endpoint. Examine what FastAPI shows for the request body schema and the response schema. Note how they come directly from `TelemetryIngestRequest` and `TelemetryResponse`.

---

## Review Checklist

- [ ] I can state the three things a thin route handler does.
- [ ] I know how request schemas map to use case calls.
- [ ] I know how use case results map to response schemas.
- [ ] I understand why business logic must not appear in route handlers.
- [ ] I can locate the mapping helper for any router in the project.
