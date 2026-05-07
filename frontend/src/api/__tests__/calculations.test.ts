import { beforeEach, describe, expect, it, vi } from "vitest";

import { calculateLoop } from "../calculations";
import { requestJson } from "../client";
import type { CalculationLoopRequest } from "../../types/calculation";

vi.mock("../client", () => ({
  requestJson: vi.fn()
}));

const request: CalculationLoopRequest = {
  devices: [
    {
      product_id: "det-1",
      display_name: "Detector",
      category: "Detector",
      standby: 0.5,
      alarm: 2,
      ledCost: 1,
      type: "Detector",
      lead_dist: 20,
      interval_dist: 15,
      qty: 12
    }
  ],
  max_current_ma: 40,
  min_voltage_v: 27.95,
  cable_resistance_ohm_per_km: 12.1,
  addr_limit: 10
};

describe("calculateLoop API adapter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("posts the calculation request and expands backend diagnostics for the web calculation model", async () => {
    vi.mocked(requestJson).mockResolvedValueOnce({
      total_addresses: 15,
      total_current_ma: 53.5,
      total_distance_m: 250,
      voltage_drop_v: 0.243936,
      end_voltage_v: 27.756064,
      max_install_distance_m: 51.24294897022243,
      recommended_cable_size: "N/A",
      recommended_cable_unit: "",
      diagnostics: [
        { key: "diag_address_over", params: { value: 15, limit: 10 } },
        { key: "diag_current_over", params: { value: 53.5 } },
        { key: "diag_voltage_low", params: { value: 27.756064 } },
        { key: "diag_length_over", params: { value: 1200, limit: 1000 } }
      ]
    });

    const result = await calculateLoop(request);

    expect(requestJson).toHaveBeenCalledWith("/api/calculations/loop", {
      method: "POST",
      body: JSON.stringify(request)
    });
    expect(result.diagnostics).toEqual([
      "Address count (15) exceeds limit (10)",
      "Loop current (53.5mA) is overloaded",
      "End voltage (27.76V) is too low",
      "Total cable length (1200.0m) exceeds system limit (1000m)"
    ]);
    expect(result.standby_current_ma).toBe(53.5);
    expect(result.alarm_current_ma).toBe(53.5);
    expect(result.addr_limit).toBe(10);
    expect(result.max_current_ma).toBe(40);
    expect(result.min_voltage_v).toBe(27.95);
    expect(result.cable_resistance_ohm_per_km).toBe(12.1);
    expect(result.panel_voltage_v).toBe(28);
    expect(result.max_cable_length_m).toBe(1000);
  });
});
