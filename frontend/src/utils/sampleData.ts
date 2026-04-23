import { createId } from "./ids";
import type { ProductRecord } from "../types/product";
import type { LoopDeviceRow, ProjectLoop, ProjectRecord } from "../types/project";

export function mapProductToDeviceRow(product: ProductRecord, sortOrder: number): LoopDeviceRow {
  return {
    id: createId("row"),
    sort_order: sortOrder,
    product_id: product.id,
    category: product.category,
    display_name: product.product_name || product.customer_name,
    customer_name: product.customer_name,
    factory_name: product.factory_name,
    product_name: product.product_name,
    standby_ma: product.standby,
    alarm_ma: product.alarm,
    led_cost: product.ledCost,
    device_type: product.type,
    lead_dist_m: 10,
    interval_dist_m: 10,
    qty: 1
  };
}

export function createDeviceRowForCategory(products: ProductRecord[], category: string, sortOrder: number): LoopDeviceRow {
  const product = products.find((item) => item.category === category);
  if (product) {
    return mapProductToDeviceRow(product, sortOrder);
  }
  return {
    id: createId("row"),
    sort_order: sortOrder,
    product_id: null,
    category,
    display_name: "",
    customer_name: "",
    factory_name: "",
    product_name: "",
    standby_ma: 0.5,
    alarm_ma: 0,
    led_cost: 1,
    device_type: category,
    lead_dist_m: 10,
    interval_dist_m: 10,
    qty: 1
  };
}

export function createEmptyLoop(projectId: string, index: number): ProjectLoop {
  return {
    id: createId("loop"),
    project_id: projectId,
    name: `Loop ${index}`,
    sort_order: index,
    address_limit: 125,
    max_current_ma: 400,
    min_voltage_v: 17,
    cable_size: "1.5",
    cable_resistance_ohm_per_km: 12.1,
    aux_current_ma: 0,
    device_rows: [],
    calculation_result: null
  };
}

export function buildSampleProject(products: ProductRecord[]): ProjectRecord {
  const projectId = createId("project");
  const preferred = [
    products.find((product) => product.category === "Detector"),
    products.find((product) => product.category === "MCP"),
    products.find((product) => product.category === "Sounder")
  ].filter(Boolean) as ProductRecord[];

  const loops = [createEmptyLoop(projectId, 1)];
  loops[0].device_rows = preferred.slice(0, 2).map((product, index) => mapProductToDeviceRow(product, index + 1));
  if (!loops[0].device_rows.length && products[0]) {
    loops[0].device_rows = [mapProductToDeviceRow(products[0], 1)];
  }

  return {
    id: projectId,
    name: "Engineering Workstation",
    active_loop_id: loops[0].id,
    loops,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
}
