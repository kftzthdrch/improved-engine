from dataclasses import dataclass
from app.domain.errors import InvalidCommandError

@dataclass(frozen=True)
class BatteryPercent:
    value: float

    def __post_init__(self):
        if not (0 <= self.value <= 100):
            raise InvalidCommandError(f"Battery percent must be between 0 and 100: {self.value}")
