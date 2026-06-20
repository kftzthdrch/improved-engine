from fastapi import Request
from fastapi.responses import JSONResponse
from app.domain.errors import (
    InvalidVehicleIdError, InvalidCommandError, CommandRejectedError,
    CommandNotFoundError, TelemetryNotFoundError, TripAlreadyActiveError,
    TripNotFoundError, DiagnosticCodeNotFoundError, AlertNotFoundError, DomainError,
)

def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}

async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    mapping = {
        InvalidVehicleIdError: (400, "INVALID_VEHICLE_ID"),
        InvalidCommandError: (400, "INVALID_COMMAND"),
        CommandRejectedError: (409, "COMMAND_REJECTED"),
        CommandNotFoundError: (404, "COMMAND_NOT_FOUND"),
        TelemetryNotFoundError: (404, "TELEMETRY_NOT_FOUND"),
        TripAlreadyActiveError: (409, "TRIP_ALREADY_ACTIVE"),
        TripNotFoundError: (404, "TRIP_NOT_FOUND"),
        DiagnosticCodeNotFoundError: (404, "DIAGNOSTIC_CODE_NOT_FOUND"),
        AlertNotFoundError: (404, "ALERT_NOT_FOUND"),
    }
    status_code, error_code = mapping.get(type(exc), (500, "INTERNAL_ERROR"))
    return JSONResponse(status_code=status_code, content=_error_body(error_code, str(exc)))

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=_error_body("INTERNAL_ERROR", "An unexpected error occurred"))
