import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useProductStore } from "../productStore";
import { createCategory, createProduct, deleteProduct, listProducts, restoreProduct, verifyAdminPassword } from "../../api/products";
import { ApiError } from "../../api/client";
import { defaultProducts } from "../../data/defaultProducts";
import type { ProductRecord } from "../../types/product";

vi.mock("../../api/products", () => ({
  createCategory: vi.fn(),
  createProduct: vi.fn(),
  deleteProduct: vi.fn(() => Promise.resolve()),
  listCategories: vi.fn(() => Promise.resolve([])),
  listProducts: vi.fn(() => Promise.resolve([])),
  restoreProduct: vi.fn(),
  updateProduct: vi.fn(),
  verifyAdminPassword: vi.fn(() => Promise.resolve({ ok: true }))
}));

const protectedProduct: ProductRecord = {
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

describe("productStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    window.localStorage.clear();
  });

  it("keeps built-in products protected unless forced by admin deletion", async () => {
    const store = useProductStore();
    store.products = [protectedProduct];

    const result = await store.removeProduct(protectedProduct);

    expect(result).toEqual({ removed: false, message: "Built-in products are protected." });
    expect(deleteProduct).not.toHaveBeenCalled();
    expect(store.products).toEqual([protectedProduct]);
  });

  it("passes force to the API and removes a built-in product after admin confirmation", async () => {
    const store = useProductStore();
    store.products = [protectedProduct];
    store.setAdminAccess("secret");

    const result = await store.removeProduct(protectedProduct, true);

    expect(deleteProduct).toHaveBeenCalledWith("product-0001", true, "secret");
    expect(result).toEqual({ removed: true, message: "Product removed." });
    expect(store.products).toEqual([]);
  });

  it("keeps the product visible when the backend rejects deletion", async () => {
    vi.mocked(deleteProduct).mockRejectedValueOnce(Object.assign(new Error("protected"), { status: 409 }));
    const store = useProductStore();
    store.products = [protectedProduct];
    store.setAdminAccess("secret");

    const result = await store.removeProduct(protectedProduct, true);

    expect(result).toEqual({ removed: false, message: "Backend rejected product deletion." });
    expect(store.products).toEqual([protectedProduct]);
    expect(store.statusMessage).toBe("Delete rejected");
  });

  it("loads deleted products and restores one into the active catalog", async () => {
    vi.mocked(listProducts).mockResolvedValueOnce([{ ...protectedProduct, deleted_at: "2026-04-30 12:00:00" }]);
    vi.mocked(restoreProduct).mockResolvedValueOnce({ ...protectedProduct, deleted_at: "" });
    const store = useProductStore();
    store.products = [];
    store.setAdminAccess("secret");

    await store.loadDeletedProducts();
    const result = await store.restoreProductRecord(protectedProduct.id);

    expect(listProducts).toHaveBeenCalledWith({ deleted: "only" });
    expect(restoreProduct).toHaveBeenCalledWith(protectedProduct.id, "secret");
    expect(result).toEqual({ restored: true, message: "Product restored." });
    expect(store.deletedProducts).toEqual([]);
    expect(store.products).toEqual([{ ...protectedProduct, deleted_at: "" }]);
    expect(store.statusMessage).toBe("Restored");
  });

  it("validates admin access through the backend before enabling product edits", async () => {
    const store = useProductStore();

    await store.unlockAdmin("secret");

    expect(verifyAdminPassword).toHaveBeenCalledWith("secret");
    expect(store.isAdmin).toBe(true);
  });

  it("unlocks admin locally on static deployments when the backend verify endpoint is unavailable", async () => {
    vi.mocked(verifyAdminPassword).mockRejectedValueOnce(new SyntaxError("Unexpected token '<'"));
    const store = useProductStore();

    await store.unlockAdmin("numens888");

    expect(verifyAdminPassword).toHaveBeenCalledWith("numens888");
    expect(store.isAdmin).toBe(true);
  });

  it("does not unlock locally when a real backend rejects the password", async () => {
    vi.mocked(verifyAdminPassword).mockRejectedValueOnce(new ApiError("Request failed with status 403", 403, {}));
    const store = useProductStore();

    await expect(store.unlockAdmin("numens888")).rejects.toBeInstanceOf(ApiError);

    expect(store.isAdmin).toBe(false);
  });

  it("does not unlock locally with the wrong static password", async () => {
    vi.mocked(verifyAdminPassword).mockRejectedValueOnce(new SyntaxError("Unexpected token '<'"));
    const store = useProductStore();

    await expect(store.unlockAdmin("wrong-password")).rejects.toBeInstanceOf(SyntaxError);

    expect(store.isAdmin).toBe(false);
  });

  it("does not silently save locally when the backend rejects a product write", async () => {
    vi.mocked(createProduct).mockRejectedValueOnce(new ApiError("Request failed with status 422", 422, {}));
    const store = useProductStore();
    store.setAdminAccess("secret");
    store.products = [];

    await expect(store.saveProduct({
      category: "Detector",
      factory_name: "Invalid",
      customer_name: "Invalid",
      product_name: "Invalid",
      standby: -0.5,
      alarm: 2,
      ledCost: 1,
      type: "Detector",
      built_in: false
    })).rejects.toBeInstanceOf(ApiError);

    expect(store.products).toEqual([]);
    expect(store.statusMessage).toBe("Save rejected");
  });

  it("does not silently cache a category when the backend rejects the write", async () => {
    vi.mocked(createCategory).mockRejectedValueOnce(new ApiError("Request failed with status 403", 403, {}));
    const store = useProductStore();
    store.setAdminAccess("bad-secret");
    store.categories = [];

    await expect(store.addCategory("Detector")).rejects.toBeInstanceOf(ApiError);

    expect(store.categories).toEqual([]);
  });

  it("refreshes cached built-in products from the bundled catalog while preserving custom products offline", async () => {
    vi.mocked(listProducts).mockRejectedValueOnce(new Error("offline"));
    const customProduct: ProductRecord = {
      id: "product-custom-1",
      category: "Detector",
      factory_name: "Custom factory",
      customer_name: "Custom customer",
      product_name: "Custom detector",
      standby: 0.7,
      alarm: 3,
      ledCost: 1,
      type: "Detector",
      built_in: false
    };
    const staleBuiltIn: ProductRecord = {
      ...defaultProducts[0],
      factory_name: "old-factory",
      product_name: "Old bundled device"
    };
    window.localStorage.setItem("loop-calculator.products", JSON.stringify([staleBuiltIn, customProduct]));

    const store = useProductStore();

    await store.bootstrap();

    expect(store.products.find((product) => product.id === defaultProducts[0].id)).toEqual(defaultProducts[0]);
    expect(store.products).toContainEqual(customProduct);
    expect(JSON.parse(window.localStorage.getItem("loop-calculator.products") ?? "[]")).toContainEqual(defaultProducts[0]);
  });

  it("keeps API-sourced built-in products when the backend is temporarily offline", async () => {
    vi.mocked(listProducts).mockRejectedValueOnce(new Error("offline"));
    const apiProduct: ProductRecord = {
      ...defaultProducts[0],
      factory_name: "api-factory",
      product_name: "API managed product"
    };
    window.localStorage.setItem("loop-calculator.products", JSON.stringify([apiProduct]));
    window.localStorage.setItem("loop-calculator.products.meta", JSON.stringify({ source: "api", seedSignature: null }));

    const store = useProductStore();

    await store.bootstrap();

    expect(store.products).toEqual([apiProduct]);
  });

  it("does not include retired 600 detector products in the bundled static catalog", () => {
    const retiredCodes = new Set(["600-001", "600-002", "600-003", "600-004", "600-005", "600-006"]);
    const retiredIds = new Set(["product-0013", "product-0014", "product-0015", "product-0016", "product-0017", "product-0018"]);

    expect(defaultProducts.some((product) => retiredIds.has(product.id))).toBe(false);
    expect(defaultProducts.some((product) => retiredCodes.has(product.factory_name) || retiredCodes.has(product.customer_name))).toBe(false);
  });

  it("removes retired built-in 600 detectors from API catalogs while preserving custom 600 products", async () => {
    const retiredBuiltIn: ProductRecord = {
      id: "product-0013",
      category: "Detector",
      factory_name: "600-001",
      customer_name: "600-001",
      product_name: "Smoke/Heat Detector",
      standby: 0.26,
      alarm: 2,
      ledCost: 1,
      type: "Detector",
      built_in: true
    };
    const custom600Product: ProductRecord = {
      id: "custom-600",
      category: "Detector",
      factory_name: "600-CUSTOM",
      customer_name: "600-CUSTOM",
      product_name: "Custom 600 Detector",
      standby: 0.5,
      alarm: 2,
      ledCost: 1,
      type: "Detector",
      built_in: false
    };
    vi.mocked(listProducts).mockResolvedValueOnce([retiredBuiltIn, custom600Product]);
    const store = useProductStore();

    await store.bootstrap();

    expect(store.products).toEqual([custom600Product]);
    expect(JSON.parse(window.localStorage.getItem("loop-calculator.products") ?? "[]")).toEqual([custom600Product]);
  });

  it("removes retired built-in 600 detectors from offline cached catalogs", async () => {
    vi.mocked(listProducts).mockRejectedValueOnce(new Error("offline"));
    const retiredBuiltIn: ProductRecord = {
      id: "product-0018",
      category: "Detector",
      factory_name: "600-006",
      customer_name: "600-006",
      product_name: "Heat Detector, Remote LED Output",
      standby: 0.26,
      alarm: 5,
      ledCost: 1,
      type: "Detector",
      built_in: true
    };
    const custom600Product: ProductRecord = {
      id: "custom-600",
      category: "Detector",
      factory_name: "600-CUSTOM",
      customer_name: "600-CUSTOM",
      product_name: "Custom 600 Detector",
      standby: 0.5,
      alarm: 2,
      ledCost: 1,
      type: "Detector",
      built_in: false
    };
    window.localStorage.setItem("loop-calculator.products", JSON.stringify([retiredBuiltIn, custom600Product]));
    window.localStorage.setItem("loop-calculator.products.meta", JSON.stringify({ source: "api", seedSignature: null }));
    const store = useProductStore();

    await store.bootstrap();

    expect(store.products).toEqual([custom600Product]);
    expect(JSON.parse(window.localStorage.getItem("loop-calculator.products") ?? "[]")).toEqual([custom600Product]);
  });
});
