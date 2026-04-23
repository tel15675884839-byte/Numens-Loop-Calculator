import { requestJson } from "./client";
import type { CalculationLoopRequest, CalculationLoopResponse } from "../types/calculation";

interface ApiCalculationDiagnostic {
  key: string;
  params?: Record<string, unknown>;
}

type ApiCalculationResponse = Omit<
  CalculationLoopResponse,
  "diagnostics" | "standby_current_ma" | "alarm_current_ma" | "addr_limit" | "max_current_ma" | "min_voltage_v" | "cable_resistance_ohm_per_km" | "panel_voltage_v" | "max_cable_length_m"
> & {
  diagnostics: ApiCalculationDiagnostic[];
  standby_current_ma?: number;
  alarm_current_ma?: number;
  addr_limit?: number;
  max_current_ma?: number;
  min_voltage_v?: number;
  cable_resistance_ohm_per_km?: number;
  panel_voltage_v?: number;
  max_cable_length_m?: number;
};

function diagnosticText(diagnostic: ApiCalculationDiagnostic): string {
  const params = diagnostic.params ?? {};
  if (diagnostic.key === "diag_address_over") {
    return `Address count (${params.value}) exceeds limit (${params.limit})`;
  }
  if (diagnostic.key === "diag_current_over") {
    return `Loop current (${Number(params.value ?? 0).toFixed(1)}mA) is overloaded`;
  }
  if (diagnostic.key === "diag_voltage_low") {
    return `End voltage (${Number(params.value ?? 0).toFixed(2)}V) is too low`;
  }
  if (diagnostic.key === "diag_length_over") {
    return `Total cable length (${Number(params.value ?? 0).toFixed(1)}m) exceeds system limit (${params.limit}m)`;
  }
  return diagnostic.key;
}

function fromApiCalculation(response: ApiCalculationResponse, request: CalculationLoopRequest): CalculationLoopResponse {
  return {
    ...response,
    standby_current_ma: response.standby_current_ma ?? response.total_current_ma,
    alarm_current_ma: response.alarm_current_ma ?? response.total_current_ma,
    diagnostics: response.diagnostics.map(diagnosticText),
    addr_limit: response.addr_limit ?? request.addr_limit,
    max_current_ma: response.max_current_ma ?? request.max_current_ma,
    min_voltage_v: response.min_voltage_v ?? request.min_voltage_v,
    cable_resistance_ohm_per_km: response.cable_resistance_ohm_per_km ?? request.cable_resistance_ohm_per_km,
    panel_voltage_v: response.panel_voltage_v ?? 28,
    max_cable_length_m: response.max_cable_length_m ?? 1000
  };
}

export function calculateLoop(request: CalculationLoopRequest) {
  return requestJson<ApiCalculationResponse>("/api/calculations/loop", {
    method: "POST",
    body: JSON.stringify(request)
  }).then((response) => fromApiCalculation(response, request));
}
