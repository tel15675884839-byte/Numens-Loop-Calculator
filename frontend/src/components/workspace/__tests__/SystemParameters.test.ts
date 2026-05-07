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
  it("shows cable size in a compact project-styled menu", async () => {
    const wrapper = mount(SystemParameters, {
      props: {
        loop,
        categories: []
      }
    });

    expect(wrapper.find("select").exists()).toBe(false);
    expect(wrapper.get('[data-testid="cable-size-trigger"]').text()).toContain("1.5 mm² (12.1 Ω/km)");

    await wrapper.get('[data-testid="cable-size-trigger"]').trigger("click");

    const menu = wrapper.get('[data-testid="cable-size-menu"]');
    expect(menu.text()).toContain("2.5 mm² (7.41 Ω/km)");

    await wrapper.get('[data-testid="cable-size-option"][data-size="2.5"]').trigger("click");

    expect(wrapper.emitted("update")?.[0]).toEqual([
      {
        cable_size: "2.5",
        cable_resistance_ohm_per_km: 7.41
      }
    ]);
    expect(wrapper.find('[data-testid="cable-size-menu"]').exists()).toBe(false);
  });

  it("closes the cable menu after selecting a custom cable", async () => {
    const wrapper = mount(SystemParameters, {
      props: {
        loop,
        categories: []
      }
    });

    await wrapper.get('[data-testid="cable-size-trigger"]').trigger("click");
    await wrapper.get('[data-testid="cable-size-option"][data-size="Custom"]').trigger("click");

    expect(wrapper.emitted("update")?.[0]).toEqual([
      {
        cable_size: "",
        cable_resistance_ohm_per_km: 0
      }
    ]);
    expect(wrapper.find('[data-testid="cable-size-menu"]').exists()).toBe(false);
  });

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
