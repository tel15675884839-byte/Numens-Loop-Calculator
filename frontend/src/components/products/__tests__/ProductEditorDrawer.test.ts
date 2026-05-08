import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ProductEditorDrawer from "../ProductEditorDrawer.vue";
import { setLocale } from "../../../i18n";

const builtInDraft = {
  id: "product-0001",
  category: "Detector",
  factory_name: "NFS2-3030",
  customer_name: "NFS2-3030",
  product_name: "Built-in Detector",
  standby: 0.5,
  alarm: 2,
  ledCost: 1,
  type: "Detector",
  built_in: true
};

describe("ProductEditorDrawer", () => {
  it("enables built-in product deletion only when admin mode is active", () => {
    const locked = mount(ProductEditorDrawer, {
      props: {
        open: true,
        draft: builtInDraft,
        categories: ["Detector"],
        isAdmin: false
      }
    });
    const unlocked = mount(ProductEditorDrawer, {
      props: {
        open: true,
        draft: builtInDraft,
        categories: ["Detector"],
        isAdmin: true
      }
    });

    expect(locked.get("button[aria-label='Delete product']").attributes("disabled")).toBeDefined();
    expect(unlocked.get("button[aria-label='Delete product']").attributes("disabled")).toBeUndefined();
  });

  it("keeps Factory name label in English while translating other editor labels", () => {
    setLocale("de");
    const wrapper = mount(ProductEditorDrawer, {
      props: {
        open: true,
        draft: builtInDraft,
        categories: ["Detector"],
        isAdmin: true
      }
    });

    expect(wrapper.text()).toContain("Factory name");
    expect(wrapper.text()).toContain("Produktname");
    expect(wrapper.text()).not.toContain("Werksname");

    setLocale("en");
  });
});
