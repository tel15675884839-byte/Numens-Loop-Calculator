import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useProductStore } from "../productStore";
import { deleteProduct, listProducts, restoreProduct } from "../../api/products";
import type { ProductRecord } from "../../types/product";

vi.mock("../../api/products", () => ({
  createCategory: vi.fn(),
  createProduct: vi.fn(),
  deleteProduct: vi.fn(() => Promise.resolve()),
  listCategories: vi.fn(() => Promise.resolve([])),
  listProducts: vi.fn(() => Promise.resolve([])),
  restoreProduct: vi.fn(),
  updateProduct: vi.fn()
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

    const result = await store.removeProduct(protectedProduct, true);

    expect(deleteProduct).toHaveBeenCalledWith("product-0001", true);
    expect(result).toEqual({ removed: true, message: "Product removed." });
    expect(store.products).toEqual([]);
  });

  it("keeps the product visible when the backend rejects deletion", async () => {
    vi.mocked(deleteProduct).mockRejectedValueOnce(Object.assign(new Error("protected"), { status: 409 }));
    const store = useProductStore();
    store.products = [protectedProduct];

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

    await store.loadDeletedProducts();
    const result = await store.restoreProductRecord(protectedProduct.id);

    expect(listProducts).toHaveBeenCalledWith({ deleted: "only" });
    expect(restoreProduct).toHaveBeenCalledWith(protectedProduct.id);
    expect(result).toEqual({ restored: true, message: "Product restored." });
    expect(store.deletedProducts).toEqual([]);
    expect(store.products).toEqual([{ ...protectedProduct, deleted_at: "" }]);
    expect(store.statusMessage).toBe("Restored");
  });
});
