from dataclasses import dataclass
from datetime import datetime
from app.domain.enums import DiagnosticSeverity
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class DiagnosticCode:
    vehicle_id: VehicleId
    code: str
    severity: DiagnosticSeverity
    description: str
    first_seen_at: datetime
    last_seen_at: datetime
    active: bool = True
