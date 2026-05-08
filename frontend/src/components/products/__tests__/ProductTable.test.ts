import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ProductTable from "../ProductTable.vue";
import { setLocale } from "../../../i18n";
import type { ProductRecord } from "../../../types/product";

const products: ProductRecord[] = [
  {
    id: "mcp-1",
    category: "MCP",
    factory_name: "660-001",
    customer_name: "660-001",
    product_name: "Manual Call Point",
    standby: 0.4,
    alarm: 2,
    ledCost: 1,
    type: "MCP",
    built_in: true
  }
];

describe("ProductTable", () => {
  it("translates built-in product names in read-only display while keeping model codes unchanged", () => {
    setLocale("de");
    const wrapper = mount(ProductTable, {
      props: {
        products,
        isAdmin: false
      }
    });

    expect(wrapper.text()).toContain("Handmelder");
    expect(wrapper.text()).toContain("660-001");
    expect(wrapper.text()).not.toContain("Manual Call Point");

    setLocale("en");
  });
});
