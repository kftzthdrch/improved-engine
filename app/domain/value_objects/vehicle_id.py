from dataclasses import dataclass
from app.domain.errors import InvalidVehicleIdError

@dataclass(frozen=True)
class VehicleId:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise InvalidVehicleIdError("Vehicle ID must not be empty")
        object.__setattr__(self, "value", self.value.strip().upper())
