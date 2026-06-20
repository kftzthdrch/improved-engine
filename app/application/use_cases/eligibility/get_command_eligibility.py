from dataclasses import dataclass
from app.application.ports.telemetry_repository import TelemetryRepository
from app.domain.enums import CommandType
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class CommandEligibility:
    command_type: CommandType
    allowed: bool
    reason: str | None = None

@dataclass
class GetCommandEligibilityUseCase:
    telemetry_repo: TelemetryRepository

    def execute(self, vehicle_id: VehicleId, quiet_mode: bool = False) -> list[CommandEligibility]:
        latest = self.telemetry_repo.get_latest(vehicle_id)
        is_moving = latest.speed_kph > 0 if latest else False
        battery_low = latest.battery_percent < 20 if latest else False

        results = []
        for cmd in CommandType:
            allowed = True
            reason = None
            if cmd in (CommandType.LOCK, CommandType.OPEN_TRUNK) and is_moving:
                allowed = False
                reason = "Vehicle is moving"
            elif cmd == CommandType.START_CLIMATE and battery_low:
                allowed = False
                reason = "Battery too low"
            elif cmd == CommandType.HONK_HORN and quiet_mode:
                allowed = False
                reason = "Quiet mode is active"
            results.append(CommandEligibility(command_type=cmd, allowed=allowed, reason=reason))
        return results
