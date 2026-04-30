import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SystemParameters from "../SystemParameters.vue";
import type { ProjectLoop } from "../../../types/project";

const loop: ProjectLoop = {
  id: "loop-1",
  project_id: "project-1",
  name: "Loop 1",
  sort_order: 1,
  address_limit: 125,
  max_current_ma: 400,
  min_voltage_v: 17,
  cable_size: "1.5",
  cable_resistance_ohm_per_km: 12.1,
  aux_current_ma: 0,
  device_rows: [],
  calculation_result: null
};

describe("SystemParameters", () => {
  it("shows the aux current unit inside the input field", () => {
    const wrapper = mount(SystemParameters, {
      props: {
        loop,
        categories: []
      }
    });

    expect(wrapper.text()).toContain("AUX current");
    expect(wrapper.text()).not.toContain("AUX current mA");
    expect(wrapper.get('[data-testid="aux-current-field"]').text()).toContain("mA");
  });
});
