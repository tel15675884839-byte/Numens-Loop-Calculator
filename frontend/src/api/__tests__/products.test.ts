import { beforeEach, describe, expect, it, vi } from "vitest";

import { deleteProduct, listProducts, restoreProduct } from "../products";
import { requestJson } from "../client";

vi.mock("../client", () => ({
  requestJson: vi.fn()
}));

describe("products API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("requests a forced product delete when admin mode allows removing protected records", async () => {
    vi.mocked(requestJson).mockResolvedValueOnce(undefined);

    await deleteProduct("product-0001", true);

    expect(requestJson).toHaveBeenCalledWith("/api/products/product-0001?force=true", {
      method: "DELETE"
    });
  });

  it("can request deleted products only for the recovery view", async () => {
    vi.mocked(requestJson).mockResolvedValueOnce([]);

    await listProducts({ deleted: "only" });

    expect(requestJson).toHaveBeenCalledWith("/api/products?deleted=only");
  });

  it("restores a soft-deleted product", async () => {
    vi.mocked(requestJson).mockResolvedValueOnce({
      id: "product-0001",
      category: "Detector",
      factory_name: "NFS2-3030",
      customer_name: "NFS2-3030",
      product_name: "Built-in Detector",
      standby_ma: 0.5,
      alarm_ma: 2,
      led_cost: 1,
      device_type: "Detector",
      built_in: true,
      deleted_at: ""
    });

    const restored = await restoreProduct("product-0001");

    expect(requestJson).toHaveBeenCalledWith("/api/products/product-0001/restore", {
      method: "POST"
    });
    expect(restored.deleted_at).toBe("");
  });
});
