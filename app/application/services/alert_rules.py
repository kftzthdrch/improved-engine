from datetime import datetime, timezone, timedelta
from app.domain.enums import AlertType
from app.domain.models.telemetry import TelemetrySnapshot

STALE_THRESHOLD_MINUTES = 10

class AlertRules:
    def evaluate(self, snapshot: TelemetrySnapshot, now: datetime) -> list[AlertType]:
        triggered = []
        if snapshot.battery_percent < 20:
            triggered.append(AlertType.LOW_BATTERY)
        if snapshot.cabin_temperature_c > 45:
            triggered.append(AlertType.CABIN_OVERHEAT)
        if snapshot.speed_kph > 0:
            triggered.append(AlertType.VEHICLE_MOVING)
        if not snapshot.door_locked:
            triggered.append(AlertType.DOOR_UNLOCKED)
        age = now - snapshot.timestamp.replace(tzinfo=timezone.utc) if snapshot.timestamp.tzinfo is None else now - snapshot.timestamp
        if age > timedelta(minutes=STALE_THRESHOLD_MINUTES):
            triggered.append(AlertType.STALE_TELEMETRY)
        return triggered
