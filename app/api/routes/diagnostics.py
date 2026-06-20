from fastapi import APIRouter, Depends, Path
from app.api.dependencies import (
    get_ingest_diagnostics_use_case, get_active_diagnostics_use_case, get_clear_diagnostic_use_case,
)
from app.api.schemas.diagnostic_schemas import DiagnosticCodeRequest, DiagnosticCodeResponse
from app.application.use_cases.diagnostics.ingest_diagnostic_codes import DiagnosticCodeInput
from app.domain.enums import DiagnosticSeverity
from app.domain.value_objects.vehicle_id import VehicleId

router = APIRouter(tags=["diagnostics"])

def _to_response(dc) -> DiagnosticCodeResponse:
    return DiagnosticCodeResponse(
        vehicle_id=dc.vehicle_id.value,
        code=dc.code,
        severity=dc.severity.value,
        description=dc.description,
        first_seen_at=dc.first_seen_at,
        last_seen_at=dc.last_seen_at,
        active=dc.active,
    )

@router.post("/vehicles/{vehicle_id}/diagnostics", response_model=list[DiagnosticCodeResponse], status_code=201)
def ingest_diagnostics(body: DiagnosticCodeRequest, vehicle_id: str = Path(...), use_case=Depends(get_ingest_diagnostics_use_case)):
    inputs = [DiagnosticCodeInput(code=c.code, severity=DiagnosticSeverity(c.severity), description=c.description) for c in body.codes]
    results = use_case.execute(VehicleId(vehicle_id), inputs)
    return [_to_response(dc) for dc in results]

@router.get("/vehicles/{vehicle_id}/diagnostics", response_model=list[DiagnosticCodeResponse])
def get_diagnostics(vehicle_id: str = Path(...), use_case=Depends(get_active_diagnostics_use_case)):
    return [_to_response(dc) for dc in use_case.execute(VehicleId(vehicle_id))]

@router.delete("/vehicles/{vehicle_id}/diagnostics/{code}", status_code=204)
def clear_diagnostic(vehicle_id: str = Path(...), code: str = Path(...), use_case=Depends(get_clear_diagnostic_use_case)):
    use_case.execute(VehicleId(vehicle_id), code)
