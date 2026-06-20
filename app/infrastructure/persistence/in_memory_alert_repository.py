from collections import defaultdict
from app.domain.models.alert import VehicleAlert
from app.domain.enums import AlertType
from app.domain.value_objects.vehicle_id import VehicleId

class InMemoryAlertRepository:
    def __init__(self):
        self._store: dict[str, dict[str, VehicleAlert]] = defaultdict(dict)

    def save(self, alert: VehicleAlert) -> None:
        self._store[alert.vehicle_id.value][alert.alert_type.value] = alert

    def upsert(self, alert: VehicleAlert) -> None:
        self.save(alert)

    def get_active(self, vehicle_id: VehicleId) -> list[VehicleAlert]:
        return [a for a in self._store.get(vehicle_id.value, {}).values() if a.active]

    def clear(self, vehicle_id: VehicleId, alert_type: AlertType) -> bool:
        vehicle_alerts = self._store.get(vehicle_id.value, {})
        alert = vehicle_alerts.get(alert_type.value)
        if alert and alert.active:
            alert.active = False
            return True
        return False
