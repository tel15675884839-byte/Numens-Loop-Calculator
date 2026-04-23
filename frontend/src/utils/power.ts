import type { ProjectLoop, ProjectRecord } from "../types/project";

const BATTERY_CAPACITY_AH = 7.2;
const BATTERY_DERATING_FACTOR = 1.25;
const PANEL_QUIESCENT_CURRENT_MA = 200;

function loopStandbyCurrent(loop: ProjectLoop): number {
  return loop.calculation_result?.standby_current_ma
    ?? loop.device_rows.reduce((sum, row) => sum + row.qty * row.standby_ma, 0);
}

function loopAlarmCurrent(loop: ProjectLoop): number {
  return loop.calculation_result?.alarm_current_ma
    ?? loop.device_rows.reduce((sum, row) => sum + row.qty * row.alarm_ma, 0);
}

function runtimeHours(capacityAh: number, currentMa: number): number {
  return currentMa > 0 ? capacityAh / (currentMa / 1000) : 0;
}

export function calculateGlobalBatteryRuntime(project: ProjectRecord | null) {
  const effectiveCapacityAh = BATTERY_CAPACITY_AH / BATTERY_DERATING_FACTOR;
  const loops = project?.loops ?? [];
  const totalAuxCurrentMa = loops.reduce((sum, loop) => sum + loop.aux_current_ma, 0);
  const loopStandbyCurrentMa = loops.reduce((sum, loop) => sum + loopStandbyCurrent(loop), 0);
  const loopAlarmCurrentMa = loops.reduce((sum, loop) => sum + loopAlarmCurrent(loop), 0);
  const totalStandbyCurrentMa = PANEL_QUIESCENT_CURRENT_MA + totalAuxCurrentMa + loopStandbyCurrentMa;
  const totalAlarmCurrentMa = PANEL_QUIESCENT_CURRENT_MA + totalAuxCurrentMa + loopAlarmCurrentMa;

  return {
    battery_capacity_ah: BATTERY_CAPACITY_AH,
    derating_factor: BATTERY_DERATING_FACTOR,
    effective_capacity_ah: effectiveCapacityAh,
    panel_current_ma: PANEL_QUIESCENT_CURRENT_MA,
    aux_current_ma: totalAuxCurrentMa,
    loop_standby_current_ma: loopStandbyCurrentMa,
    loop_alarm_current_ma: loopAlarmCurrentMa,
    total_standby_current_ma: totalStandbyCurrentMa,
    total_alarm_current_ma: totalAlarmCurrentMa,
    standby_hours: runtimeHours(effectiveCapacityAh, totalStandbyCurrentMa),
    alarm_hours: runtimeHours(effectiveCapacityAh, totalAlarmCurrentMa)
  };
}
