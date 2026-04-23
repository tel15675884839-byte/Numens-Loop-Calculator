from __future__ import annotations

from loop_calculator.calculator import calculate_loop

from backend.app.domain.calculator_adapter import build_loop_calculation_request
from backend.app.schemas import CalculationRequest
from backend.app.storage import SQLiteStore


class BackendService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def calculate_loop(self, request: CalculationRequest) -> dict[str, object]:
        calculator_request = build_loop_calculation_request(request)
        result = calculate_loop(calculator_request)
        return {
            "total_addresses": result.total_addresses,
            "total_current_ma": result.total_current_ma,
            "total_distance_m": result.total_distance_m,
            "voltage_drop_v": result.voltage_drop_v,
            "end_voltage_v": result.end_voltage_v,
            "max_install_distance_m": result.max_install_distance_m,
            "recommended_cable_size": result.recommended_cable_size,
            "recommended_cable_unit": result.recommended_cable_unit,
            "standby_current_ma": result.standby_current_ma,
            "alarm_current_ma": result.alarm_current_ma,
            "diagnostics": [
                {"key": issue.key, "params": dict(issue.params)}
                for issue in result.diagnostics
            ],
        }
