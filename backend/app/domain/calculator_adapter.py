from __future__ import annotations

from loop_calculator.calculator import LoopCalculationRequest, LoopDeviceInput

from backend.app.schemas import CalculationRequest


def build_loop_calculation_request(request: CalculationRequest) -> LoopCalculationRequest:
    devices = [
        LoopDeviceInput(
            product_id=device.product_id,
            display_name=device.display_name,
            category=device.category,
            standby_ma=device.standby,
            alarm_ma=device.alarm,
            led_cost=device.ledCost,
            device_type=device.type_,
            lead_dist_m=device.lead_dist,
            interval_dist_m=device.interval_dist,
            qty=device.qty,
        )
        for device in request.devices
    ]
    return LoopCalculationRequest(
        devices=devices,
        max_current_ma=request.max_current_ma,
        min_voltage_v=request.min_voltage_v,
        cable_resistance_ohm_per_km=request.cable_resistance_ohm_per_km,
        addr_limit=request.addr_limit,
    )

