from app.domain.models.maintenance import MaintenanceState

class MaintenanceRules:
    def check_service_due(self, state: MaintenanceState, current_odometer_km: float) -> bool:
        return state.is_service_due(current_odometer_km)

    def check_tire_check_due(self, state: MaintenanceState, current_odometer_km: float) -> bool:
        return state.is_tire_check_due(current_odometer_km)
