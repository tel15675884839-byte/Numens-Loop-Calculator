import type { CalculationDeviceInput, CalculationLoopRequest, CalculationLoopResponse } from "../types/calculation";

const DEFAULT_PANEL_VOLTAGE = 28;
const DEFAULT_MAX_ALARM_LEDS = 10;
const DEFAULT_MAX_CABLE_LENGTH_M = 1000;

const DEFAULT_CABLE_TYPES = [
  { size: "1.0", resistance_ohm_per_km: 18.1, unit: "mm²" },
  { size: "1.5", resistance_ohm_per_km: 12.1, unit: "mm²" },
  { size: "2.5", resistance_ohm_per_km: 7.41, unit: "mm²" },
  { size: "4.0", resistance_ohm_per_km: 4.61, unit: "mm²" }
];

function coerceNumber(value: number | string | null | undefined, fallback: number) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function cloneDeviceInput(device: CalculationDeviceInput): CalculationDeviceInput {
  return { ...device };
}

export function calculateLoopLocally(request: CalculationLoopRequest): CalculationLoopResponse {
  const devices = request.devices.map(cloneDeviceInput);
  const totalAddresses = devices.reduce((sum, device) => sum + coerceNumber(device.qty, 0), 0);
  const standbyCurrent = devices.reduce((sum, device) => sum + coerceNumber(device.qty, 0) * coerceNumber(device.standby, 0), 0);

  const ledReserved = devices.reduce((sum, device) => {
    const qty = coerceNumber(device.qty, 0);
    const ledCost = coerceNumber(device.ledCost, 1);
    return sum + (device.type === "LSM" || ledCost > 1 ? qty * ledCost : 0);
  }, 0);

  const ledRemaining = Math.max(0, DEFAULT_MAX_ALARM_LEDS - ledReserved);
  let ledUsed = 0;
  let totalCurrent = 0;
  const processed = devices.map((device) => {
    const qty = coerceNumber(device.qty, 0);
    const ledCost = coerceNumber(device.ledCost, 1);
    let activeAlarmLeds = 0;
    if (device.type === "LSM" || ledCost > 1 || ledCost === 0) {
      activeAlarmLeds = qty;
    } else {
      const canUse = ledRemaining - ledUsed;
      activeAlarmLeds = canUse > 0 ? Math.min(qty, Math.floor(canUse / ledCost)) : 0;
      ledUsed += activeAlarmLeds * ledCost;
    }
    const rowCurrent = activeAlarmLeds * coerceNumber(device.alarm, 0) + (qty - activeAlarmLeds) * coerceNumber(device.standby, 0);
    totalCurrent += rowCurrent;
    return { device, activeAlarmLeds, rowCurrent };
  });

  let totalDistance = 0;
  let voltageDrop = 0;
  let flowMa = totalCurrent;

  for (const result of processed) {
    const device = result.device;
    const qty = coerceNumber(device.qty, 0);
    if (qty <= 0) {
      continue;
    }

    const leadR = coerceNumber(request.cable_resistance_ohm_per_km, 0) * (coerceNumber(device.lead_dist, 0) / 1000) * 2;
    voltageDrop += (flowMa / 1000) * leadR;
    totalDistance += coerceNumber(device.lead_dist, 0);

    const intervalR = coerceNumber(request.cable_resistance_ohm_per_km, 0) * (coerceNumber(device.interval_dist, 0) / 1000) * 2;
    if (qty > 1) {
      const avgCurrent = result.rowCurrent / qty;
      const flowAfterFirst = flowMa - avgCurrent;
      const intervals = qty - 1;
      const factor = intervals * flowAfterFirst - (intervals * (intervals - 1)) / 2 * avgCurrent;
      voltageDrop += (factor / 1000) * intervalR;
      totalDistance += intervals * coerceNumber(device.interval_dist, 0);
    }

    flowMa -= result.rowCurrent;
  }

  const endVoltage = DEFAULT_PANEL_VOLTAGE - voltageDrop;
  const maxInstallDistance = voltageDrop > 0
    ? totalDistance * ((DEFAULT_PANEL_VOLTAGE - coerceNumber(request.min_voltage_v, 17)) / voltageDrop)
    : DEFAULT_MAX_CABLE_LENGTH_M;

  let recommendedCableSize = "N/A";
  let recommendedCableUnit = "";
  if (coerceNumber(request.cable_resistance_ohm_per_km, 0) > 0) {
    for (const cable of DEFAULT_CABLE_TYPES) {
      const testDrop = (cable.resistance_ohm_per_km / coerceNumber(request.cable_resistance_ohm_per_km, 0)) * voltageDrop;
      if (DEFAULT_PANEL_VOLTAGE - testDrop >= coerceNumber(request.min_voltage_v, 17)) {
        recommendedCableSize = cable.size;
        recommendedCableUnit = cable.unit;
        break;
      }
    }
  }

  const diagnostics: string[] = [];
  if (totalAddresses > request.addr_limit) {
    diagnostics.push(`Address count (${totalAddresses}) exceeds limit (${request.addr_limit})`);
  }
  if (totalCurrent > request.max_current_ma) {
    diagnostics.push(`Loop current (${totalCurrent.toFixed(1)}mA) is overloaded`);
  }
  if (endVoltage < request.min_voltage_v) {
    diagnostics.push(`End voltage (${endVoltage.toFixed(2)}V) is too low`);
  }
  if (totalDistance > DEFAULT_MAX_CABLE_LENGTH_M) {
    diagnostics.push(`Total cable length (${totalDistance.toFixed(1)}m) exceeds system limit (${DEFAULT_MAX_CABLE_LENGTH_M}m)`);
  }

  return {
    total_addresses: totalAddresses,
    total_current_ma: totalCurrent,
    total_distance_m: totalDistance,
    voltage_drop_v: voltageDrop,
    end_voltage_v: endVoltage,
    max_install_distance_m: maxInstallDistance,
    recommended_cable_size: recommendedCableSize,
    recommended_cable_unit: recommendedCableUnit,
    standby_current_ma: standbyCurrent,
    alarm_current_ma: totalCurrent,
    diagnostics,
    addr_limit: request.addr_limit,
    max_current_ma: request.max_current_ma,
    min_voltage_v: request.min_voltage_v,
    cable_resistance_ohm_per_km: request.cable_resistance_ohm_per_km,
    panel_voltage_v: DEFAULT_PANEL_VOLTAGE,
    max_cable_length_m: DEFAULT_MAX_CABLE_LENGTH_M
  };
}
