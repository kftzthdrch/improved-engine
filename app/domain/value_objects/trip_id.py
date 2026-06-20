from dataclasses import dataclass

@dataclass(frozen=True)
class TripId:
    value: str
