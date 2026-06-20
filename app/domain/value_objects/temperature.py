from dataclasses import dataclass
from app.domain.errors import InvalidCommandError

@dataclass(frozen=True)
class Temperature:
    celsius: float

    def __post_init__(self):
        if not (-50 <= self.celsius <= 100):
            raise InvalidCommandError(f"Temperature {self.celsius}°C is outside realistic range")
