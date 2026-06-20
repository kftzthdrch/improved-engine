from dataclasses import dataclass
from app.application.ports.alert_repository import AlertRepository
from app.domain.enums import AlertType
from app.domain.errors import AlertNotFoundError
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class ClearVehicleAlertUseCase:
    alert_repo: AlertRepository

    def execute(self, vehicle_id: VehicleId, alert_type: AlertType) -> None:
        cleared = self.alert_repo.clear(vehicle_id, alert_type)
        if not cleared:
            raise AlertNotFoundError(f"No active alert of type {alert_type.value}")
