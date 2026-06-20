from dataclasses import dataclass
from app.application.ports.alert_repository import AlertRepository
from app.application.ports.telemetry_repository import TelemetryRepository
from app.application.ports.clock import Clock
from app.application.services.alert_rules import AlertRules
from app.domain.enums import AlertType
from app.domain.models.alert import VehicleAlert
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class EvaluateVehicleAlertsUseCase:
    telemetry_repo: TelemetryRepository
    alert_repo: AlertRepository
    clock: Clock
    rules: AlertRules

    def execute(self, vehicle_id: VehicleId) -> list[VehicleAlert]:
        latest = self.telemetry_repo.get_latest(vehicle_id)
        if latest is None:
            return []
        now = self.clock.now()
        triggered_types = self.rules.evaluate(latest, now)
        active_alerts = []
        for alert_type in triggered_types:
            alert = VehicleAlert(
                vehicle_id=vehicle_id,
                alert_type=alert_type,
                message=self._message_for(alert_type, latest),
                triggered_at=now,
                active=True,
            )
            self.alert_repo.upsert(alert)
            active_alerts.append(alert)
        return active_alerts

    def _message_for(self, alert_type: AlertType, snapshot: TelemetrySnapshot) -> str:
        messages = {
            AlertType.LOW_BATTERY: f"Battery at {snapshot.battery_percent:.0f}%",
            AlertType.CABIN_OVERHEAT: f"Cabin temperature {snapshot.cabin_temperature_c:.1f}°C",
            AlertType.VEHICLE_MOVING: f"Vehicle moving at {snapshot.speed_kph:.1f} km/h",
            AlertType.DOOR_UNLOCKED: "Door is unlocked",
            AlertType.STALE_TELEMETRY: "Telemetry data is stale",
        }
        return messages.get(alert_type, alert_type.value)
