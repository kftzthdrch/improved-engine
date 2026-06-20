from app.domain.errors import InvalidCommandError

class TelemetryValidation:
    def validate(self, speed_kph: float, battery_percent: float, odometer_km: float, cabin_temperature_c: float) -> None:
        if speed_kph < 0:
            raise InvalidCommandError("speed_kph cannot be negative")
        if not (0 <= battery_percent <= 100):
            raise InvalidCommandError("battery_percent must be between 0 and 100")
        if odometer_km < 0:
            raise InvalidCommandError("odometer_km cannot be negative")
        if not (-50 <= cabin_temperature_c <= 100):
            raise InvalidCommandError("cabin_temperature_c is outside realistic range")
