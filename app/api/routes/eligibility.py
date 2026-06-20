from fastapi import APIRouter, Depends, Path, Query
from app.api.dependencies import get_command_eligibility_use_case
from app.api.schemas.eligibility_schemas import CommandEligibilityResponse, CommandEligibilityItem
from app.domain.value_objects.vehicle_id import VehicleId

router = APIRouter(tags=["eligibility"])

@router.get("/vehicles/{vehicle_id}/commands/eligibility", response_model=CommandEligibilityResponse)
def get_eligibility(vehicle_id: str = Path(...), quiet_mode: bool = Query(False), use_case=Depends(get_command_eligibility_use_case)):
    results = use_case.execute(VehicleId(vehicle_id), quiet_mode)
    return CommandEligibilityResponse(
        vehicle_id=vehicle_id,
        eligibility=[CommandEligibilityItem(command_type=r.command_type.value, allowed=r.allowed, reason=r.reason) for r in results],
    )
