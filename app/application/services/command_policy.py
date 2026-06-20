from app.domain.errors import CommandRejectedError
from app.domain.models.telemetry import TelemetrySnapshot

class CommandPolicy:
    def enforce_not_moving(self, latest_telemetry: TelemetrySnapshot | None) -> None:
        if latest_telemetry and latest_telemetry.speed_kph > 0:
            raise CommandRejectedError("Vehicle is moving")

    def enforce_battery_sufficient(self, latest_telemetry: TelemetrySnapshot | None, min_percent: float = 20.0) -> None:
        if latest_telemetry and latest_telemetry.battery_percent < min_percent:
            raise CommandRejectedError(f"Battery too low: {latest_telemetry.battery_percent}%")

    def enforce_cabin_temperature_range(self, target_celsius: float) -> None:
        if not (16.0 <= target_celsius <= 30.0):
            raise CommandRejectedError(f"Target temperature {target_celsius}°C is outside allowed range 16–30°C")

    def enforce_quiet_mode_off(self, quiet_mode: bool) -> None:
        if quiet_mode:
            raise CommandRejectedError("Quiet mode is active")
