from dataclasses import dataclass
from app.domain.errors import InvalidCommandError

@dataclass(frozen=True)
class Speed:
    kph: float

    def __post_init__(self):
        if self.kph < 0:
            raise InvalidCommandError(f"Speed cannot be negative: {self.kph}")
