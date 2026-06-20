from dataclasses import dataclass
from app.application.ports.alert_repository import AlertRepository
from app.domain.models.alert import VehicleAlert
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class GetActiveAlertsUseCase:
    alert_repo: AlertRepository

    def execute(self, vehicle_id: VehicleId) -> list[VehicleAlert]:
        return self.alert_repo.get_active(vehicle_id)
