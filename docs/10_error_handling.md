# Chapter 10: Error Handling

## Learning Objective

Understand how domain errors are raised in the core, propagate through the application layer, and are caught by FastAPI exception handlers to produce consistent, structured HTTP error responses.

---

## The Error Flow

Error handling in this project follows a deliberate, layered flow:

1. A value object or domain model raises a `DomainError` subclass.
2. The error propagates up through the use case without being caught.
3. FastAPI's exception handler intercepts it before it becomes a 500.
4. The handler maps the error type to an HTTP status code and error code string.
5. A consistent JSON body is returned to the client.

No route handler contains `try/except` for domain errors. No use case catches errors just to re-raise them as HTTP exceptions. The exception handlers are the single point of translation.

---

## The Domain Error Hierarchy

File: `app/domain/errors.py`

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

All errors share a common base class `DomainError`. This allows the exception handler to catch `DomainError` in a single `add_exception_handler` call and dispatch to the right HTTP status by checking `type(exc)`.

---

## The Exception Handlers

File: `app/api/exception_handlers.py`

```python
def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}

async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    mapping = {
        InvalidVehicleIdError:         (400, "INVALID_VEHICLE_ID"),
        InvalidCommandError:           (400, "INVALID_COMMAND"),
        CommandRejectedError:          (409, "COMMAND_REJECTED"),
        CommandNotFoundError:          (404, "COMMAND_NOT_FOUND"),
        TelemetryNotFoundError:        (404, "TELEMETRY_NOT_FOUND"),
        TripAlreadyActiveError:        (409, "TRIP_ALREADY_ACTIVE"),
        TripNotFoundError:             (404, "TRIP_NOT_FOUND"),
        DiagnosticCodeNotFoundError:   (404, "DIAGNOSTIC_CODE_NOT_FOUND"),
        AlertNotFoundError:            (404, "ALERT_NOT_FOUND"),
    }
    status_code, error_code = mapping.get(type(exc), (500, "INTERNAL_ERROR"))
    return JSONResponse(status_code=status_code, content=_error_body(error_code, str(exc)))

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=_error_body("INTERNAL_ERROR", "An unexpected error occurred"))
```

Both handlers are registered in `create_app()` in `app/main.py`:

```python
app.add_exception_handler(DomainError, domain_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

FastAPI checks handlers in registration order. When a `CommandRejectedError` is raised, FastAPI sees it is a `DomainError` and calls `domain_exception_handler`. The generic handler only fires for non-`DomainError` exceptions.

---

## Error to HTTP Status Code Mapping

| Domain Error | HTTP Status | Error Code |
| ------------ | ----------- | ---------- |
| `InvalidVehicleIdError` | 400 Bad Request | `INVALID_VEHICLE_ID` |
| `InvalidCommandError` | 400 Bad Request | `INVALID_COMMAND` |
| `CommandRejectedError` | 409 Conflict | `COMMAND_REJECTED` |
| `CommandNotFoundError` | 404 Not Found | `COMMAND_NOT_FOUND` |
| `TelemetryNotFoundError` | 404 Not Found | `TELEMETRY_NOT_FOUND` |
| `TripAlreadyActiveError` | 409 Conflict | `TRIP_ALREADY_ACTIVE` |
| `TripNotFoundError` | 404 Not Found | `TRIP_NOT_FOUND` |
| `DiagnosticCodeNotFoundError` | 404 Not Found | `DIAGNOSTIC_CODE_NOT_FOUND` |
| `AlertNotFoundError` | 404 Not Found | `ALERT_NOT_FOUND` |
| Any other exception | 500 Internal Server Error | `INTERNAL_ERROR` |

### Why 409 for Rejected Commands?

HTTP 409 Conflict means "the request could not be completed due to a conflict with the current state of the resource." A command rejected because the vehicle is moving is exactly this — the vehicle's current state conflicts with the operation.

HTTP 400 Bad Request means the client sent invalid data. `CommandRejectedError` is raised by business policy, not by bad input, so 400 is wrong.

HTTP 422 Unprocessable Entity is used by FastAPI for Pydantic validation failures. `CommandRejectedError` passes validation but fails a business rule — 422 is wrong too.

---

## Consistent Error Response Shape

Every error response has the same JSON structure:

```json
{
  "error": {
    "code": "COMMAND_REJECTED",
    "message": "Vehicle is moving"
  }
}
```

This is defined by `_error_body()` in `exception_handlers.py` and by the schema in `app/api/schemas/error_schemas.py`:

```python
class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

Having a consistent shape means API clients need only one error-parsing function. They read `response.error.code` to dispatch and `response.error.message` for human-readable detail.

---

## How Errors Travel Through the Stack

Consider a lock command on a moving vehicle:

1. `lock_vehicle` route calls `use_case.execute(VehicleId("VH-001"))`.
2. `LockVehicleUseCase.execute()` calls `self.policy.enforce_not_moving(latest)`.
3. `CommandPolicy.enforce_not_moving()` sees `speed_kph = 60` and raises `CommandRejectedError("Vehicle is moving")`.
4. `enforce_not_moving` propagates the error back to `execute()`.
5. `execute()` catches it, marks the command rejected, saves it, and re-raises.
6. The error propagates out of the use case back to the route handler.
7. FastAPI's exception handling middleware intercepts it.
8. `domain_exception_handler` is called with the `CommandRejectedError`.
9. The handler returns `JSONResponse(status_code=409, content={"error": {"code": "COMMAND_REJECTED", "message": "Vehicle is moving"}})`.
10. The client receives HTTP 409 with the JSON body.

The route handler never saw the error at all.

---

## Pydantic Validation Errors

FastAPI handles Pydantic validation errors (e.g., a required field missing in the request body, or a field with the wrong type) automatically, returning HTTP 422 with a detailed validation error body. These are distinct from domain errors — they happen before any use case code runs.

You do not need to do anything for this. FastAPI's built-in behavior handles it.

---

## Anti-Patterns to Avoid

**Catching domain errors in route handlers and returning `HTTPException`.** This bypasses the exception handler system, duplicates error mapping logic, and makes the error format inconsistent.

```python
# Wrong
@router.post("/vehicles/{vehicle_id}/commands/lock")
def lock_vehicle(...):
    try:
        cmd = use_case.execute(...)
    except CommandRejectedError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

```python
# Right: just let the error propagate; the handler catches it
@router.post("/vehicles/{vehicle_id}/commands/lock")
def lock_vehicle(...):
    cmd = use_case.execute(...)
    return _to_response(cmd)
```

**Raising `HTTPException` from use cases or domain objects.** Use cases and domain objects must not import `fastapi`. They raise `DomainError` subclasses. The API layer maps those to HTTP.

**Different error shapes for different errors.** If some endpoints return `{"detail": "..."}` and others return `{"error": {"code": "...", "message": "..."}}`, clients need multiple parsers. Consistency is enforced by always going through `_error_body()`.

**A flat mapping without a default.** The handler uses `mapping.get(type(exc), (500, "INTERNAL_ERROR"))`. The fallback to 500 ensures that even unregistered `DomainError` subclasses return a sensible response.

---

## Exercises

1. Run `pytest tests/integration/api/test_commands.py -k test_lock_rejected_when_moving`. Confirm it returns 409. Then look at `app/api/exception_handlers.py` and find the exact line that produces the 409.

2. Add a new error class `FuelLevelCriticalError(DomainError)` to `app/domain/errors.py`. Add it to the mapping in `app/api/exception_handlers.py` with status 503 and code `FUEL_CRITICAL`. Write a dependency override test that injects a use case stub raising this error and asserts 503.

3. What happens if you remove the `generic_exception_handler` registration and a Python `KeyError` is raised inside a use case? Test it by raising `KeyError("test")` from a stub and observe the response.

---

## Review Checklist

- [ ] I can trace a `CommandRejectedError` from where it is raised to the HTTP response.
- [ ] I understand why 409 is correct for policy rejections and not 400 or 422.
- [ ] I know the consistent error response shape and where it is defined.
- [ ] I understand why route handlers must not catch domain errors.
- [ ] I know what happens to Pydantic validation errors (422, handled by FastAPI automatically).
