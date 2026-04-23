import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useWorkspaceStore } from "../workspaceStore";

vi.mock("../../api/projects", () => ({
  createProject: vi.fn(() => Promise.reject(new Error("offline"))),
  deleteProject: vi.fn(),
  getProject: vi.fn(),
  listProjects: vi.fn(() => Promise.resolve([])),
  updateProject: vi.fn(() => Promise.reject(new Error("offline")))
}));

vi.mock("../../api/calculations", () => ({
  calculateLoop: vi.fn(() => Promise.reject(new Error("offline")))
}));

describe("workspaceStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it("marks failed saves as errors instead of reporting server persistence success", async () => {
    const store = useWorkspaceStore();
    store.createBlankProject();

    await store.saveActiveProject();

    expect(store.saveState).toBe("error");
    expect(store.error).toBe("Project saved locally only. Backend persistence failed.");
  });

  it("adds a device by selected category and blocks additions at the address limit", () => {
    const store = useWorkspaceStore();
    store.createBlankProject();
    const loopId = store.activeLoopId;
    store.updateSystemParameters(loopId, { address_limit: 1 });

    const added = store.addDeviceRowForCategory(loopId, "Detector", [
      { id: "mcp-1", category: "MCP", factory_name: "M1", customer_name: "M1", product_name: "MCP 1", standby: 0.4, alarm: 2, ledCost: 1, type: "MCP", built_in: true },
      { id: "detector-1", category: "Detector", factory_name: "D1", customer_name: "D1", product_name: "Detector 1", standby: 0.5, alarm: 2, ledCost: 1, type: "Detector", built_in: true }
    ]);
    const blocked = store.addDeviceRowForCategory(loopId, "Detector", [
      { id: "detector-1", category: "Detector", factory_name: "D1", customer_name: "D1", product_name: "Detector 1", standby: 0.5, alarm: 2, ledCost: 1, type: "Detector", built_in: true }
    ]);

    expect(added).toBe(true);
    expect(blocked).toBe(false);
    expect(store.activeLoop?.device_rows).toHaveLength(1);
    expect(store.activeLoop?.device_rows[0].product_id).toBe("detector-1");
    expect(store.activeLoop?.device_rows[0].lead_dist_m).toBe(10);
    expect(store.error).toBe("Address limit reached for this loop.");
  });
});
