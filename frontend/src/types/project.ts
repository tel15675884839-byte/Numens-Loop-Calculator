export interface LoopDeviceRow {
  id: string;
  sort_order: number;
  product_id: string | null;
  category: string;
  display_name: string;
  customer_name: string;
  factory_name: string;
  product_name: string;
  standby_ma: number;
  alarm_ma: number;
  led_cost: number;
  device_type: string;
  lead_dist_m: number;
  interval_dist_m: number;
  qty: number;
}

export interface LoopCalculationSnapshot {
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

export interface ProjectLoop {
  id: string;
  project_id: string;
  name: string;
  sort_order: number;
  address_limit: number;
  max_current_ma: number;
  min_voltage_v: number;
  cable_size: string;
  cable_resistance_ohm_per_km: number;
  aux_current_ma: number;
  device_rows: LoopDeviceRow[];
  calculation_result: LoopCalculationSnapshot | null;
}

export interface ProjectRecord {
  id: string;
  name: string;
  active_loop_id: string;
  loops: ProjectLoop[];
  created_at?: string;
  updated_at?: string;
}

export interface ProjectListItem {
  id: string;
  name: string;
  active_loop_id: string;
  loop_count: number;
  created_at?: string;
  updated_at?: string;
}
