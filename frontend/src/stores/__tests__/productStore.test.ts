import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useProductStore } from "../productStore";
import { createCategory, createProduct, deleteProduct, listProducts, restoreProduct, verifyAdminPassword } from "../../api/products";
import { ApiError } from "../../api/client";
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
});
