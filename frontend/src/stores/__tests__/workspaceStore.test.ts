import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useWorkspaceStore } from "../workspaceStore";
import type { CalculationLoopResponse } from "../../types/calculation";

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
    vi.clearAllMocks();
    vi.restoreAllMocks();
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

  it("starts with an empty loop when no backend or local project exists", async () => {
    const store = useWorkspaceStore();

    await store.bootstrap();

    expect(store.activeLoop?.device_rows).toEqual([]);
  });

  it("limits projects to six loops", () => {
    const store = useWorkspaceStore();
    store.createBlankProject();

    for (let index = 0; index < 8; index += 1) {
      store.addLoop();
    }

    expect(store.activeProject?.loops).toHaveLength(6);
    expect(store.activeLoop?.sort_order).toBe(6);
    expect(store.canAddLoop).toBe(false);
  });

  it("keeps an unsaved project active when creating a new project is cancelled", async () => {
    const store = useWorkspaceStore();
    store.createBlankProject();
    const originalProjectId = store.activeProjectId;
    store.setProjectName("Unsaved configuration");

    const nextProject = store.createBlankProject();
    const dialogStore = (await import("../dialogStore")).useDialogStore();
    expect(dialogStore.activeDialog?.message).toBe("This project has unsaved changes. Discard changes before leaving?");
    expect(dialogStore.activeDialog?.confirmLabel).toBe("Discard changes");
    dialogStore.resolve(false);
    await nextProject;

    expect(store.activeProjectId).toBe(originalProjectId);
    expect(store.activeProject?.name).toBe("Unsaved configuration");
    expect(store.saveState).toBe("dirty");
  });

  it("keeps an unsaved project active when switching projects is cancelled", async () => {
    const projectsApi = await import("../../api/projects");
    const store = useWorkspaceStore();
    store.createBlankProject();
    const originalProjectId = store.activeProjectId;
    store.projects = [
      ...store.projects,
      {
        id: "other-project",
        name: "Other project",
        active_loop_id: "other-loop",
        loop_count: 1
      }
    ];
    store.setProjectName("Unsaved configuration");

    const selection = store.selectProject("other-project");
    const dialogStore = (await import("../dialogStore")).useDialogStore();
    expect(dialogStore.activeDialog?.message).toBe("This project has unsaved changes. Discard changes before leaving?");
    expect(dialogStore.activeDialog?.confirmLabel).toBe("Discard changes");
    dialogStore.resolve(false);
    await selection;

    expect(projectsApi.getProject).not.toHaveBeenCalled();
    expect(store.activeProjectId).toBe(originalProjectId);
  });

  it("continues creating a new project when unsaved changes are confirmed", async () => {
    const store = useWorkspaceStore();
    store.createBlankProject();
    const originalProjectId = store.activeProjectId;
    store.setProjectName("Unsaved configuration");

    const nextProject = store.createBlankProject();
    const dialogStore = (await import("../dialogStore")).useDialogStore();
    expect(dialogStore.activeDialog?.message).toBe("This project has unsaved changes. Discard changes before leaving?");
    expect(dialogStore.activeDialog?.confirmLabel).toBe("Discard changes");
    dialogStore.resolve(true);
    await nextProject;

    expect(store.activeProjectId).not.toBe(originalProjectId);
    expect(store.activeProject?.name).not.toBe("Unsaved configuration");
    expect(store.saveState).toBe("idle");
  });

  it("switches to a cached project immediately while the backend copy is still loading", async () => {
    const projectsApi = await import("../../api/projects");
    let resolveRemote: ((project: {
      id: string;
      name: string;
      active_loop_id: string;
      loops: Array<{
        id: string;
        project_id: string;
        name: string;
        sort_order: number;
        address_limit: number;
        max_current_ma: number;
        min_voltage_v: number;
        cable_size: string;
        cable_resistance_ohm_per_km: number;
        aux_current_ma: number;
        device_rows: never[];
        calculation_result: null;
      }>;
    }) => void) | null = null;
    vi.mocked(projectsApi.getProject).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveRemote = resolve;
        })
    );

    localStorage.setItem("loop-calculator.workspace.v2", JSON.stringify([
      {
        id: "cached-project",
        name: "Cached project",
        active_loop_id: "cached-loop",
        loops: [
          {
            id: "cached-loop",
            project_id: "cached-project",
            name: "Loop 1",
            sort_order: 1,
            address_limit: 125,
            max_current_ma: 400,
            min_voltage_v: 17,
            cable_size: "1.5",
            cable_resistance_ohm_per_km: 12.1,
            aux_current_ma: 0,
            device_rows: [],
            calculation_result: null
          }
        ]
      }
    ]));

    const store = useWorkspaceStore();
    store.createBlankProject();
    store.projects = [
      ...store.projects,
      {
        id: "cached-project",
        name: "Cached project",
        active_loop_id: "cached-loop",
        loop_count: 1
      }
    ];

    await store.selectProject("cached-project");

    expect(store.activeProjectId).toBe("cached-project");
    expect(store.activeProject?.name).toBe("Cached project");

    resolveRemote?.({
      id: "cached-project",
      name: "Remote project",
      active_loop_id: "cached-loop",
      loops: [
        {
          id: "cached-loop",
          project_id: "cached-project",
          name: "Loop 1",
          sort_order: 1,
          address_limit: 125,
          max_current_ma: 400,
          min_voltage_v: 17,
          cable_size: "1.5",
          cable_resistance_ohm_per_km: 12.1,
          aux_current_ma: 0,
          device_rows: [],
          calculation_result: null
        }
      ]
    });
    await Promise.resolve();
    await Promise.resolve();

    expect(store.activeProject?.name).toBe("Remote project");
  });

  it("does not mark a blank project dirty until editable data changes", () => {
    const store = useWorkspaceStore();

    store.createBlankProject();

    expect(store.hasUnsavedChanges).toBe(false);
    expect(store.saveState).toBe("idle");

    store.setProjectName("Unsaved configuration");

    expect(store.hasUnsavedChanges).toBe(true);
    expect(store.saveState).toBe("dirty");
  });

  it("discards unsaved changes and clears the unsaved state when leaving is confirmed", async () => {
    const store = useWorkspaceStore();
    store.createBlankProject();
    const originalName = store.activeProject?.name;
    store.setProjectName("Unsaved configuration");

    const leave = store.canLeaveActiveProject();
    const dialogStore = (await import("../dialogStore")).useDialogStore();
    dialogStore.resolve(true);

    expect(await leave).toBe(true);
    expect(store.activeProject?.name).toBe(originalName);
    expect(store.hasUnsavedChanges).toBe(false);
    expect(store.saveState).toBe("idle");
  });

  it("creates new projects through the create endpoint after switching to a blank project", async () => {
    const projectsApi = await import("../../api/projects");
    vi.mocked(projectsApi.createProject).mockResolvedValueOnce({
      id: "saved-project",
      name: "Project 1",
      active_loop_id: "loop-1",
      loops: [
        {
          id: "loop-1",
          project_id: "saved-project",
          name: "Loop 1",
          sort_order: 1,
          address_limit: 125,
          max_current_ma: 400,
          min_voltage_v: 17,
          cable_size: "1.5",
          cable_resistance_ohm_per_km: 12.1,
          aux_current_ma: 0,
          device_rows: [],
          calculation_result: null
        }
      ]
    });
    const store = useWorkspaceStore();

    store.createBlankProject();
    await store.saveActiveProject();

    expect(projectsApi.createProject).toHaveBeenCalledOnce();
    expect(projectsApi.updateProject).not.toHaveBeenCalled();
    expect(store.saveState).toBe("saved");
  });

  it("creates a project when saving a locally cached project that is missing from the backend", async () => {
    const projectsApi = await import("../../api/projects");
    const missingBackendProject = Object.assign(new Error("missing project"), { status: 404 });
    vi.mocked(projectsApi.updateProject).mockRejectedValueOnce(missingBackendProject);
    vi.mocked(projectsApi.createProject).mockResolvedValueOnce({
      id: "saved-local-project",
      name: "Locally cached project",
      active_loop_id: "loop-1",
      loops: [
        {
          id: "loop-1",
          project_id: "saved-local-project",
          name: "Loop 1",
          sort_order: 1,
          address_limit: 125,
          max_current_ma: 400,
          min_voltage_v: 17,
          cable_size: "1.5",
          cable_resistance_ohm_per_km: 12.1,
          aux_current_ma: 0,
          device_rows: [],
          calculation_result: null
        }
      ]
    });
    const store = useWorkspaceStore();

    localStorage.setItem("loop-calculator.workspace.v2", JSON.stringify([
      {
        id: "local-project",
        name: "Local project",
        active_loop_id: "loop-1",
        loops: [
          {
            id: "loop-1",
            project_id: "local-project",
            name: "Loop 1",
            sort_order: 1,
            address_limit: 125,
            max_current_ma: 400,
            min_voltage_v: 17,
            cable_size: "1.5",
            cable_resistance_ohm_per_km: 12.1,
            aux_current_ma: 0,
            device_rows: [],
            calculation_result: null
          }
        ]
      }
    ]));
    await store.bootstrap();
    store.setProjectName("Locally cached project");
    await store.saveActiveProject();

    expect(projectsApi.updateProject).toHaveBeenCalledOnce();
    expect(projectsApi.createProject).toHaveBeenCalledOnce();
    expect(store.saveState).toBe("saved");
    expect(store.activeProjectId).toBe("saved-local-project");
  });

  it("saves a project print profile through the active project persistence path", async () => {
    const projectsApi = await import("../../api/projects");
    const store = useWorkspaceStore();

    store.createBlankProject();
    vi.mocked(projectsApi.createProject).mockResolvedValueOnce({
      ...store.activeProject!,
      print_profile: {
        project_no: "NUM-2401",
        customer: "North Plant",
        site: "Zone A",
        panel: "FACP-01",
        revision: "A",
        prepared_by: "Engineering",
        issue_date: "2026-04-30",
        notes: "Issued for review"
      }
    });

    await store.savePrintProfile({
      project_no: "NUM-2401",
      customer: "North Plant",
      site: "Zone A",
      panel: "FACP-01",
      revision: "A",
      prepared_by: "Engineering",
      issue_date: "2026-04-30",
      notes: "Issued for review"
    });

    expect(store.activeProject?.print_profile?.project_no).toBe("NUM-2401");
    expect(projectsApi.createProject).toHaveBeenCalledOnce();
    expect(store.saveState).toBe("saved");
  });

  it("hydrates calculation snapshots for every loop when a project is loaded", async () => {
    vi.useFakeTimers();
    try {
      localStorage.setItem("loop-calculator.workspace.v2", JSON.stringify([
        {
          id: "multi-loop-project",
          name: "Multi-loop project",
          active_loop_id: "loop-1",
          loops: [
            {
              id: "loop-1",
              project_id: "multi-loop-project",
              name: "Loop 1",
              sort_order: 1,
              address_limit: 125,
              max_current_ma: 400,
              min_voltage_v: 17,
              cable_size: "1.5",
              cable_resistance_ohm_per_km: 12.1,
              aux_current_ma: 0,
              device_rows: [],
              calculation_result: null
            },
            {
              id: "loop-2",
              project_id: "multi-loop-project",
              name: "Loop 2",
              sort_order: 2,
              address_limit: 125,
              max_current_ma: 400,
              min_voltage_v: 17,
              cable_size: "1.5",
              cable_resistance_ohm_per_km: 12.1,
              aux_current_ma: 0,
              device_rows: [],
              calculation_result: null
            }
          ]
        }
      ]));
      const store = useWorkspaceStore();

      await store.bootstrap();
      await vi.runAllTimersAsync();

      expect(store.activeProject?.loops.map((loop) => Boolean(loop.calculation_result))).toEqual([true, true]);
    } finally {
      vi.useRealTimers();
    }
  });

  it("does not calculate missing snapshots as a side effect of switching loops", async () => {
    vi.useFakeTimers();
    try {
      const calculationsApi = await import("../../api/calculations");
      const store = useWorkspaceStore();
      store.createBlankProject();
      const firstLoopId = store.activeLoopId;
      store.addLoop();
      store.setActiveLoop(firstLoopId);
      await vi.runAllTimersAsync();
      vi.mocked(calculationsApi.calculateLoop).mockClear();

      const secondLoopId = store.activeProject?.loops.find((loop) => loop.id !== firstLoopId)?.id ?? "";
      const secondLoop = store.activeProject?.loops.find((loop) => loop.id === secondLoopId);
      if (secondLoop) {
        secondLoop.calculation_result = null;
      }

      store.setActiveLoop(secondLoopId);
      expect(store.activeProject?.loops.find((loop) => loop.id === secondLoopId)?.calculation_result).toBeNull();

      await vi.runAllTimersAsync();

      expect(store.activeProject?.loops.find((loop) => loop.id === secondLoopId)?.calculation_result).toBeNull();
      expect(calculationsApi.calculateLoop).not.toHaveBeenCalled();
    } finally {
      vi.useRealTimers();
    }
  });

  it("ignores stale async calculation results after loop inputs change again", async () => {
    vi.useFakeTimers();
    try {
      const calculationsApi = await import("../../api/calculations");
      let resolveFirstCalculation: ((value: CalculationLoopResponse) => void) | null = null;
      vi.mocked(calculationsApi.calculateLoop).mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveFirstCalculation = resolve;
          })
      );
      const store = useWorkspaceStore();
      store.createBlankProject();
      const loopId = store.activeLoopId;

      store.updateSystemParameters(loopId, { max_current_ma: 300 });
      const staleSnapshot = { ...store.activeLoop!.calculation_result!, max_current_ma: 300 };
      await vi.advanceTimersByTimeAsync(250);

      store.updateSystemParameters(loopId, { max_current_ma: 200 });
      resolveFirstCalculation?.(staleSnapshot);
      await Promise.resolve();

      expect(store.activeLoop?.calculation_result?.max_current_ma).toBe(200);
    } finally {
      vi.useRealTimers();
    }
  });
});
