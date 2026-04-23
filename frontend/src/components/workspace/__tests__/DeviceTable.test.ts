import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import DeviceTable from "../DeviceTable.vue";
import type { LoopDeviceRow } from "../../../types/project";
import type { ProductRecord } from "../../../types/product";

const products: ProductRecord[] = [
  {
    id: "product-1",
    category: "Detector",
    factory_name: "600-005",
    customer_name: "600-005",
    product_name: "Heat Detector",
    standby: 0.26,
    alarm: 2,
    ledCost: 1,
    type: "Detector",
    built_in: true
  }
];

const rows: LoopDeviceRow[] = [
  {
    id: "row-1",
    sort_order: 1,
    product_id: "product-1",
    category: "Detector",
    display_name: "Heat Detector",
    customer_name: "600-005",
    factory_name: "600-005",
    product_name: "Heat Detector",
    standby_ma: 0.26,
    alarm_ma: 2,
    led_cost: 1,
    device_type: "Detector",
    lead_dist_m: 10,
    interval_dist_m: 10,
    qty: 1
  }
];

describe("DeviceTable", () => {
  it("removes duplicate display/type editors and keeps row scrolling inside the panel", () => {
    const wrapper = mount(DeviceTable, {
      props: {
        rows,
        products,
        categories: ["Detector"]
      }
    });

    expect(wrapper.text()).not.toContain("TYPE");
    expect(wrapper.findAll("input").some((input) => input.element.value === "Heat Detector")).toBe(false);
    expect(wrapper.find('[data-testid="device-table-scroll"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="device-table-scroll"]').classes()).toContain("overflow-auto");
  });
});
