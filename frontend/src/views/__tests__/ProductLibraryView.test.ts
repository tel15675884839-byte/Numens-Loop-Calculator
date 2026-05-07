import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProductLibraryView from "../ProductLibraryView.vue";
import ProductTable from "../../components/products/ProductTable.vue";
import { useDialogStore } from "../../stores/dialogStore";
import { useProductStore } from "../../stores/productStore";
import type { ProductRecord } from "../../types/product";

vi.mock("../../api/products", () => ({
  createCategory: vi.fn(),
  createProduct: vi.fn(),
  deleteProduct: vi.fn(),
  listCategories: vi.fn(() => Promise.resolve([])),
  listProducts: vi.fn(() => Promise.resolve([])),
  restoreProduct: vi.fn(),
  updateProduct: vi.fn()
}));

const builtInProduct: ProductRecord = {
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

describe("ProductLibraryView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    window.localStorage.clear();
  });

  it("allows admin-confirmed deletion of a built-in product through the force path", async () => {
    const productStore = useProductStore();
    productStore.products = [builtInProduct];
    productStore.isAdmin = true;
    const removeSpy = vi.spyOn(productStore, "removeProduct").mockResolvedValue({
      removed: true,
      message: "Product removed."
    });

    const wrapper = mount(ProductLibraryView, {
      global: {
        stubs: {
          ProductEditorDrawer: true,
          ProductFilters: true
        }
      }
    });
    const table = wrapper.findComponent(ProductTable);

    table.vm.$emit("delete", builtInProduct);
    await wrapper.vm.$nextTick();
    useDialogStore().resolve(true);
    await flushPromises();

    expect(removeSpy).toHaveBeenCalledWith(builtInProduct, true);
  });

  it("opens the admin recovery panel and restores a deleted product", async () => {
    const productStore = useProductStore();
    productStore.isAdmin = true;
    productStore.deletedProducts = [{ ...builtInProduct, deleted_at: "2026-04-30 12:00:00" }];
    const loadDeletedSpy = vi.spyOn(productStore, "loadDeletedProducts").mockResolvedValue(productStore.deletedProducts);
    const restoreSpy = vi.spyOn(productStore, "restoreProductRecord").mockResolvedValue({
      restored: true,
      message: "Product restored."
    });

    const wrapper = mount(ProductLibraryView, {
      global: {
        stubs: {
          ProductEditorDrawer: true,
          ProductTable: true
        }
      }
    });

    const deletedButton = wrapper.findAll("button").find((button) => button.text().includes("Deleted"));
    expect(deletedButton).toBeTruthy();
    await deletedButton!.trigger("click");

    expect(loadDeletedSpy).toHaveBeenCalled();
    expect(wrapper.text()).toContain("Built-in Detector");

    const restoreButton = wrapper.findAll("button").find((button) => button.text().includes("Restore"));
    expect(restoreButton).toBeTruthy();
    await restoreButton!.trigger("click");

    expect(restoreSpy).toHaveBeenCalledWith("product-0001");
  });
});
