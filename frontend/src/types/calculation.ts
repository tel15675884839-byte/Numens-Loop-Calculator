export interface CalculationDeviceInput {
  product_id: string | null;
  display_name: string;
  category: string;
  standby: number;
  alarm: number;
  ledCost: number;
  type: string;
  lead_dist: number;
  interval_dist: number;
  qty: number;
}

export interface CalculationLoopRequest {
  devices: CalculationDeviceInput[];
  max_current_ma: number;
  min_voltage_v: number;
  cable_resistance_ohm_per_km: number;
  addr_limit: number;
}

export interface CalculationLoopResponse {
  total_addresses: number;
  total_current_ma: number;
  total_distance_m: number;
  voltage_drop_v: number;
  end_voltage_v: number;
  max_install_distance_m: number;
  recommended_cable_size: string;
  recommended_cable_unit: string;
  standby_current_ma: number;
  alarm_current_ma: number;
  diagnostics: string[];
  addr_limit: number;
  max_current_ma: number;
  min_voltage_v: number;
  cable_resistance_ohm_per_km: number;
  panel_voltage_v: number;
  max_cable_length_m: number;
}
