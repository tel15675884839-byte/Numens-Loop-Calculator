import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CalculationInspector from "../CalculationInspector.vue";
import type { CalculationLoopResponse } from "../../../types/calculation";
import type { ProjectLoop, ProjectRecord } from "../../../types/project";

const result: CalculationLoopResponse = {
  total_addresses: 14,
  total_current_ma: 170.2,
  total_distance_m: 140,
  voltage_drop_v: 0.29,
  end_voltage_v: 27.71,
  max_install_distance_m: 500,
  recommended_cable_size: "1.0",
  recommended_cable_unit: "mm²",
  standby_current_ma: 120,
  alarm_current_ma: 57400,
  diagnostics: [],
  addr_limit: 125,
  max_current_ma: 400,
  min_voltage_v: 17,
  cable_resistance_ohm_per_km: 18.1,
  panel_voltage_v: 28,
  max_cable_length_m: 1000
};

const loop: ProjectLoop = {
  id: "loop-1",
  project_id: "project-1",
  name: "Loop 1",
  sort_order: 1,
  address_limit: 125,
  max_current_ma: 400,
  min_voltage_v: 17,
  cable_size: "1.0",
  cable_resistance_ohm_per_km: 18.1,
  aux_current_ma: 0,
  device_rows: [],
  calculation_result: result
};

const project: ProjectRecord = {
  id: "project-1",
  name: "Project 1",
  active_loop_id: "loop-1",
  loops: [loop]
};

describe("CalculationInspector", () => {
  it("renders a single battery symbol with standby and alarm runtimes", () => {
    const wrapper = mount(CalculationInspector, {
      props: {
        loop,
        project,
        result,
        busy: false
      }
    });

    const standbyGauge = wrapper.get('[data-testid="battery-standby"]');
    const alarmGauge = wrapper.get('[data-testid="battery-alarm"]');
    const powerCard = wrapper.get(".battery-symbol").element.closest(".bg-white");

    expect(standbyGauge.text()).toContain("18.0h");
    expect(alarmGauge.text()).toContain("0.1h");
    expect(wrapper.find(".battery-symbol").exists()).toBe(true);
    expect(powerCard?.textContent).not.toContain("%");
    expect(wrapper.text()).toContain("Power Calculations");
    expect(wrapper.text()).toContain("System Parameters");
    expect(wrapper.findAll('p > span.inline-flex').length).toBe(0);
  });
});
