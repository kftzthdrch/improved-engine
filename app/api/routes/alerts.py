from fastapi import APIRouter, Depends, Path
from app.api.dependencies import get_active_alerts_use_case, get_clear_alert_use_case
from app.api.schemas.alert_schemas import AlertResponse
from app.domain.enums import AlertType
from app.domain.errors import AlertNotFoundError
from app.domain.value_objects.vehicle_id import VehicleId

router = APIRouter(tags=["alerts"])

@router.get("/vehicles/{vehicle_id}/alerts", response_model=list[AlertResponse])
def get_alerts(vehicle_id: str = Path(...), use_case=Depends(get_active_alerts_use_case)):
    alerts = use_case.execute(VehicleId(vehicle_id))
    return [AlertResponse(
        vehicle_id=a.vehicle_id.value,
        alert_type=a.alert_type.value,
        message=a.message,
        triggered_at=a.triggered_at,
        active=a.active,
    ) for a in alerts]

@router.delete("/vehicles/{vehicle_id}/alerts/{alert_type}", status_code=204)
def clear_alert(vehicle_id: str = Path(...), alert_type: str = Path(...), use_case=Depends(get_clear_alert_use_case)):
    try:
        at = AlertType(alert_type)
    except ValueError:
        raise AlertNotFoundError(f"Unknown alert type: {alert_type}")
    use_case.execute(VehicleId(vehicle_id), at)
