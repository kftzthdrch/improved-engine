from dataclasses import dataclass
from datetime import datetime
from app.domain.enums import AlertType
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class VehicleAlert:
    vehicle_id: VehicleId
    alert_type: AlertType
    message: str
    triggered_at: datetime
    active: bool = True
