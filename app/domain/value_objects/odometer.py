from dataclasses import dataclass
from app.domain.errors import InvalidCommandError

@dataclass(frozen=True)
class Odometer:
    km: float

    def __post_init__(self):
        if self.km < 0:
            raise InvalidCommandError(f"Odometer cannot be negative: {self.km}")
