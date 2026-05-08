import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
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
    expect(wrapper.get('[data-testid="lead-field"]').text()).toContain("m");
    expect(wrapper.get('[data-testid="interval-field"]').text()).toContain("m");
    expect(wrapper.get('[data-testid="alarm-field"]').text()).toContain("mA");
    expect(wrapper.text()).toContain("Lead");
    expect(wrapper.text()).toContain("Interval");
    expect(wrapper.text()).toContain("Alarm");
    expect(wrapper.text()).not.toContain("Lead m");
    expect(wrapper.text()).not.toContain("Interval m");
    expect(wrapper.text()).not.toContain("Alarm mA");
    expect(wrapper.text()).not.toContain("Manual row");
    expect(wrapper.find('option[value=""]').exists()).toBe(false);
  });

  it("selects numeric field text on focus so replacement typing does not append", async () => {
    const wrapper = mount(DeviceTable, {
      props: {
        rows,
        products,
        categories: ["Detector"]
      }
    });

    const quantityInput = wrapper.get('input[inputmode="numeric"]');
    const selectSpy = vi.spyOn(quantityInput.element as HTMLInputElement, "select");

    await quantityInput.trigger("mousedown");
    await quantityInput.trigger("mouseup");
    await quantityInput.trigger("click");

    expect(selectSpy).toHaveBeenCalledTimes(3);
    expect(quantityInput.attributes("type")).toBe("text");
  });
});
