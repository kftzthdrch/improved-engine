from fastapi import APIRouter, Depends, Path
from app.api.dependencies import get_maintenance_status_use_case, get_service_reset_use_case
from app.api.schemas.maintenance_schemas import MaintenanceStatusResponse
from app.domain.value_objects.vehicle_id import VehicleId

router = APIRouter(tags=["maintenance"])

def _to_response(status) -> MaintenanceStatusResponse:
    return MaintenanceStatusResponse(
        vehicle_id=status.state.vehicle_id.value,
        last_service_odometer_km=status.state.last_service_odometer_km,
        last_tire_check_odometer_km=status.state.last_tire_check_odometer_km,
        last_service_date=status.state.last_service_date,
        last_tire_check_date=status.state.last_tire_check_date,
        current_odometer_km=status.current_odometer_km,
        service_due=status.service_due,
        tire_check_due=status.tire_check_due,
    )

@router.get("/vehicles/{vehicle_id}/maintenance", response_model=MaintenanceStatusResponse)
def get_maintenance(vehicle_id: str = Path(...), use_case=Depends(get_maintenance_status_use_case)):
    return _to_response(use_case.execute(VehicleId(vehicle_id)))

@router.post("/vehicles/{vehicle_id}/maintenance/service-reset", response_model=MaintenanceStatusResponse)
def service_reset(vehicle_id: str = Path(...), maintenance_uc=Depends(get_maintenance_status_use_case), reset_uc=Depends(get_service_reset_use_case)):
    reset_uc.execute(VehicleId(vehicle_id))
    return _to_response(maintenance_uc.execute(VehicleId(vehicle_id)))
