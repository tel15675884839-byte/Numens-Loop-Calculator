import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { usePrintStore } from "../printStore";
import { useWorkspaceStore } from "../workspaceStore";
import type { ProjectPrintProfile, ProjectRecord } from "../../types/project";

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

function buildProject(printProfile: ProjectPrintProfile | null): ProjectRecord {
  return {
    id: "project-1",
    name: "Print Project",
    active_loop_id: "loop-1",
    print_profile: printProfile,
    loops: [
      {
        id: "loop-1",
        project_id: "project-1",
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
  };
}

function withCalculation(project: ProjectRecord): ProjectRecord {
  return {
    ...project,
    loops: project.loops.map((loop) => ({
      ...loop,
      calculation_result: {
        total_addresses: 1,
        total_current_ma: 10,
        total_distance_m: 10,
        voltage_drop_v: 0.01,
        end_voltage_v: 27.99,
        max_install_distance_m: 1000,
        recommended_cable_size: "1.0",
        recommended_cable_unit: "mm2",
        standby_current_ma: 10,
        alarm_current_ma: 10,
        diagnostics: [],
        addr_limit: 125,
        max_current_ma: 400,
        min_voltage_v: 17,
        cable_resistance_ohm_per_km: 12.1,
        panel_voltage_v: 28,
        max_cable_length_m: 1000
      }
    }))
  };
}

describe("printStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it("initializes draft metadata from the saved project print profile", () => {
    const store = usePrintStore();

    store.initializeFromProject(withCalculation(buildProject({
      project_no: "NUM-2401",
      customer: "North Plant",
      site: "Zone A",
      panel: "FACP-01",
      revision: "A",
      prepared_by: "Engineering",
      issue_date: "2026-04-30",
      notes: "Issued for review"
    })), "2026-05-01");

    expect(store.draftProfile?.project_no).toBe("NUM-2401");
    expect(store.draftProfile?.issue_date).toBe("2026-04-30");
    expect(store.canPrint).toBe(true);
  });

  it("prefills issue date for projects without a saved print profile", () => {
    const store = usePrintStore();

    store.initializeFromProject(withCalculation(buildProject(null)), "2026-05-01");

    expect(store.draftProfile?.project_no).toBe("");
    expect(store.draftProfile?.issue_date).toBe("2026-05-01");
    expect(store.canPrint).toBe(false);
  });

  it("does not allow printing until every loop has a calculation snapshot", () => {
    const store = usePrintStore();
    const project = buildProject({
      project_no: "NUM-2401",
      customer: "North Plant",
      site: "Zone A",
      panel: "FACP-01",
      revision: "A",
      prepared_by: "Engineering",
      issue_date: "2026-04-30",
      notes: "Issued for review"
    });

    store.initializeFromProject(project, "2026-05-01");

    expect(store.canPrint).toBe(false);
  });

  it("keeps draft edits when recalculation readiness is refreshed", () => {
    const store = usePrintStore();
    const project = buildProject({
      project_no: "NUM-2401",
      customer: "North Plant",
      site: "Zone A",
      panel: "FACP-01",
      revision: "A",
      prepared_by: "Engineering",
      issue_date: "2026-04-30",
      notes: "Issued for review"
    });

    store.initializeFromProject(project, "2026-05-01");
    store.updateDraft({ revision: "B" });
    store.refreshCalculationReady(withCalculation(project));

    expect(store.draftProfile?.revision).toBe("B");
    expect(store.canPrint).toBe(true);
  });

  it("keeps preview edits temporary until the profile is saved as project defaults", async () => {
    const workspace = useWorkspaceStore();
    const saveSpy = vi.spyOn(workspace, "savePrintProfile").mockResolvedValue();
    const store = usePrintStore();
    store.initializeFromProject(withCalculation(buildProject(null)), "2026-05-01");

    store.updateDraft({
      project_no: "NUM-2401",
      customer: "North Plant",
      revision: "A",
      prepared_by: "Engineering"
    });

    expect(saveSpy).not.toHaveBeenCalled();
    expect(store.canPrint).toBe(true);

    await store.saveDefaults();

    expect(saveSpy).toHaveBeenCalledWith({
      project_no: "NUM-2401",
      customer: "North Plant",
      site: "",
      panel: "",
      revision: "A",
      prepared_by: "Engineering",
      issue_date: "2026-05-01",
      notes: ""
    });
  });

  it("resets the draft back to the saved profile", () => {
    const store = usePrintStore();
    store.initializeFromProject(withCalculation(buildProject({
      project_no: "NUM-2401",
      customer: "North Plant",
      site: "Zone A",
      panel: "FACP-01",
      revision: "A",
      prepared_by: "Engineering",
      issue_date: "2026-04-30",
      notes: "Issued for review"
    })), "2026-05-01");

    store.updateDraft({ revision: "B", site: "Zone B" });
    store.resetDraft();

    expect(store.draftProfile?.revision).toBe("A");
    expect(store.draftProfile?.site).toBe("Zone A");
  });
});
