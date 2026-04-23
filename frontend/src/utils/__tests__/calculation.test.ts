import { describe, expect, it } from "vitest";
import { calculateLoopLocally } from "../calculation";
import { calculateGlobalBatteryRuntime } from "../power";
import { buildSampleProject, createDeviceRowForCategory, mapProductToDeviceRow } from "../sampleData";
import type { ProductRecord } from "../../types/product";

describe("calculateLoopLocally", () => {
  it("produces a stable summary for a simple row set", () => {
    const result = calculateLoopLocally({
      devices: [
        {
          product_id: "product-1",
          display_name: "Detector",
          category: "Detector",
          standby: 0.5,
          alarm: 2,
          ledCost: 1,
          type: "Detector",
          lead_dist: 10,
          interval_dist: 10,
          qty: 2
        }
      ],
      max_current_ma: 400,
      min_voltage_v: 17,
      cable_resistance_ohm_per_km: 12.1,
      addr_limit: 125
    });

    expect(result.total_addresses).toBe(2);
    expect(result.total_current_ma).toBeGreaterThan(0);
    expect(result.end_voltage_v).toBeLessThan(28);
    expect(result.diagnostics).toHaveLength(0);
    expect(result.max_cable_length_m).toBe(1000);
  });
});

describe("calculateGlobalBatteryRuntime", () => {
  it("combines every loop with host and aux current before estimating runtime", () => {
    const result = calculateGlobalBatteryRuntime({
      id: "project-1",
      name: "Project",
      active_loop_id: "loop-1",
      loops: [
        {
          id: "loop-1",
          project_id: "project-1",
          name: "Loop 1",
          sort_order: 1,
          address_limit: 125,
          max_current_ma: 400,
          min_voltage_v: 17,
          cable_size: "1.5",
          cable_resistance_ohm_per_km: 12.1,
          aux_current_ma: 20,
          device_rows: [],
          calculation_result: { ...calculateLoopLocally({
            devices: [{ product_id: null, display_name: "A", category: "Detector", standby: 10, alarm: 50, ledCost: 1, type: "Detector", lead_dist: 10, interval_dist: 10, qty: 1 }],
            max_current_ma: 400,
            min_voltage_v: 17,
            cable_resistance_ohm_per_km: 12.1,
            addr_limit: 125
          }) }
        },
        {
          id: "loop-2",
          project_id: "project-1",
          name: "Loop 2",
          sort_order: 2,
          address_limit: 125,
          max_current_ma: 400,
          min_voltage_v: 17,
          cable_size: "1.5",
          cable_resistance_ohm_per_km: 12.1,
          aux_current_ma: 30,
          device_rows: [],
          calculation_result: { ...calculateLoopLocally({
            devices: [{ product_id: null, display_name: "B", category: "MCP", standby: 20, alarm: 100, ledCost: 1, type: "MCP", lead_dist: 10, interval_dist: 10, qty: 1 }],
            max_current_ma: 400,
            min_voltage_v: 17,
            cable_resistance_ohm_per_km: 12.1,
            addr_limit: 125
          }) }
        }
      ]
    });

    expect(result.effective_capacity_ah).toBeCloseTo(5.76);
    expect(result.total_standby_current_ma).toBeCloseTo(280);
    expect(result.total_alarm_current_ma).toBeCloseTo(400);
    expect(result.standby_hours).toBeCloseTo(20.57, 2);
    expect(result.alarm_hours).toBeCloseTo(14.4, 2);
  });
});

describe("mapProductToDeviceRow", () => {
  it("snapshots product fields into a device row", () => {
    const product: ProductRecord = {
      id: "product-99",
      category: "Sounder",
      factory_name: "641-001",
      customer_name: "641-001",
      product_name: "Sounder",
      standby: 0.35,
      alarm: 16,
      ledCost: 0,
      type: "Sounder",
      built_in: true
    };

    const row = mapProductToDeviceRow(product, 3);
    expect(row.product_id).toBe("product-99");
    expect(row.product_name).toBe("Sounder");
    expect(row.standby_ma).toBe(0.35);
    expect(row.sort_order).toBe(3);
  });

  it("uses the first product in the selected category with default distance and quantity", () => {
    const products: ProductRecord[] = [
      { id: "detector-1", category: "Detector", factory_name: "D1", customer_name: "D1", product_name: "Detector 1", standby: 0.5, alarm: 2, ledCost: 1, type: "Detector", built_in: true },
      { id: "mcp-1", category: "MCP", factory_name: "M1", customer_name: "M1", product_name: "MCP 1", standby: 0.4, alarm: 2, ledCost: 1, type: "MCP", built_in: true }
    ];

    const row = createDeviceRowForCategory(products, "MCP", 2);

    expect(row.product_id).toBe("mcp-1");
    expect(row.qty).toBe(1);
    expect(row.lead_dist_m).toBe(10);
    expect(row.interval_dist_m).toBe(10);
  });
});

describe("buildSampleProject", () => {
  it("starts with one default loop", () => {
    const project = buildSampleProject([]);

    expect(project.loops).toHaveLength(1);
    expect(project.active_loop_id).toBe(project.loops[0].id);
  });
});
