import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { calculateLoop } from "../api/calculations";
import { createProject, deleteProject, getProject, listProjects, updateProject } from "../api/projects";
import { defaultProducts } from "../data/defaultProducts";
import { sampleWorkspaceProjects } from "../data/sampleWorkspace";
import type { CalculationLoopRequest, CalculationLoopResponse } from "../types/calculation";
import type { LoopCalculationSnapshot, LoopDeviceRow, ProjectListItem, ProjectLoop, ProjectRecord } from "../types/project";
import { calculateLoopLocally } from "../utils/calculation";
import { createDeviceRowForCategory, mapProductToDeviceRow } from "../utils/sampleData";
import { createId } from "../utils/ids";
import { readJson, writeJson } from "../utils/storage";
import type { ProductRecord } from "../types/product";

const WORKSPACE_CACHE_KEY = "loop-calculator.workspace.v2";

type SaveState = "idle" | "dirty" | "saving" | "saved" | "error";
type ProjectMode = "new" | "edit";

const calculationTimers = new Map<string, ReturnType<typeof setTimeout>>();

function cloneProject(project: ProjectRecord): ProjectRecord {
  return JSON.parse(JSON.stringify(project)) as ProjectRecord;
}

function normalizeLoop(loop: ProjectLoop): ProjectLoop {
  return {
    ...loop,
    device_rows: [...loop.device_rows].sort((left, right) => left.sort_order - right.sort_order),
    calculation_result: loop.calculation_result ? { ...loop.calculation_result, diagnostics: [...loop.calculation_result.diagnostics] } : null
  };
}

function normalizeProject(project: ProjectRecord): ProjectRecord {
  return {
    ...project,
    loops: [...project.loops].sort((left, right) => left.sort_order - right.sort_order).map(normalizeLoop)
  };
}

function createLoopFromIndex(projectId: string, index: number, base?: Partial<ProjectLoop>): ProjectLoop {
  return {
    id: createId("loop"),
    project_id: projectId,
    name: `Loop ${index}`,
    sort_order: index,
    address_limit: base?.address_limit ?? 125,
    max_current_ma: base?.max_current_ma ?? 400,
    min_voltage_v: base?.min_voltage_v ?? 17,
    cable_size: base?.cable_size ?? "1.5",
    cable_resistance_ohm_per_km: base?.cable_resistance_ohm_per_km ?? 12.1,
    aux_current_ma: base?.aux_current_ma ?? 0,
    device_rows: base?.device_rows ? [...base.device_rows] : [],
    calculation_result: base?.calculation_result ?? null
  };
}

function createProjectDraft(name = "New Project"): ProjectRecord {
  const projectId = createId("project");
  const loops = [createLoopFromIndex(projectId, 1)];
  return {
    id: projectId,
    name,
    active_loop_id: loops[0].id,
    loops,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
}

function toCalculationRequest(loop: ProjectLoop): CalculationLoopRequest {
  return {
    devices: loop.device_rows.map((row) => ({
      product_id: row.product_id,
      display_name: row.display_name,
      category: row.category,
      standby: row.standby_ma,
      alarm: row.alarm_ma,
      ledCost: row.led_cost,
      type: row.device_type,
      lead_dist: row.lead_dist_m,
      interval_dist: row.interval_dist_m,
      qty: row.qty
    })),
    max_current_ma: loop.max_current_ma,
    min_voltage_v: loop.min_voltage_v,
    cable_resistance_ohm_per_km: loop.cable_resistance_ohm_per_km,
    addr_limit: loop.address_limit
  };
}

function snapshotResult(result: CalculationLoopResponse): CalculationLoopSnapshot {
  return { ...result };
}

function createDeviceRowFromProduct(product: ProductRecord, sortOrder: number): LoopDeviceRow {
  return mapProductToDeviceRow(product, sortOrder);
}

function getLocalProjects() {
  return readJson<ProjectRecord[]>(WORKSPACE_CACHE_KEY) ?? sampleWorkspaceProjects;
}

export const useWorkspaceStore = defineStore("workspace", () => {
  const projects = ref<ProjectListItem[]>([]);
  const activeProject = ref<ProjectRecord | null>(null);
  const activeProjectId = ref<string>("");
  const activeLoopId = ref<string>("");
  const loading = ref(false);
  const error = ref<string | null>(null);
  const saveState = ref<SaveState>("idle");
  const projectMode = ref<ProjectMode>("edit");
  const lastSavedAt = ref<string | null>(null);
  const calculationBusyLoopIds = ref<string[]>([]);

  const activeLoop = computed(() => activeProject.value?.loops.find((loop) => loop.id === activeLoopId.value) ?? null);

  const activeLoopIndex = computed(() => activeProject.value?.loops.findIndex((loop) => loop.id === activeLoopId.value) ?? 0);

  function touchDirty() {
    if (saveState.value !== "saving") {
      saveState.value = "dirty";
    }
  }

  function writeCache(project: ProjectRecord | null) {
    if (!project) {
      return;
    }
    writeJson(WORKSPACE_CACHE_KEY, [project]);
  }

  function setActiveProject(project: ProjectRecord) {
    const normalized = normalizeProject(cloneProject(project));
    activeProject.value = normalized;
    activeProjectId.value = normalized.id;
    activeLoopId.value = normalized.active_loop_id || normalized.loops[0]?.id || "";
    saveState.value = "idle";
    projectMode.value = "edit";
    lastSavedAt.value = normalized.updated_at ?? null;
    writeCache(normalized);
    const summary = {
      id: normalized.id,
      name: normalized.name,
      active_loop_id: normalized.active_loop_id,
      loop_count: normalized.loops.length,
      created_at: normalized.created_at,
      updated_at: normalized.updated_at
    };
    const index = projects.value.findIndex((item) => item.id === normalized.id);
    if (index >= 0) {
      projects.value[index] = summary;
    } else {
      projects.value = [summary, ...projects.value];
    }
    ensureInitialCalculation();
  }

  async function bootstrap() {
    loading.value = true;
    error.value = null;
    try {
      const remoteProjects = await listProjects();
      projects.value = remoteProjects;
      const firstProjectId = remoteProjects[0]?.id;
      if (firstProjectId) {
        const project = await getProject(firstProjectId);
        setActiveProject(project);
      } else {
        const fallback = getLocalProjects()[0] ?? createProjectDraft();
        projectMode.value = "edit";
        setActiveProject(fallback);
      }
    } catch (cause) {
      const fallback = getLocalProjects()[0] ?? createProjectDraft();
      projectMode.value = "edit";
      setActiveProject(fallback);
      error.value = cause instanceof Error ? cause.message : "Unable to load workspace";
    } finally {
      loading.value = false;
    }
  }

  function setProjectName(name: string) {
    if (!activeProject.value) {
      return;
    }
    activeProject.value.name = name;
    activeProject.value.updated_at = new Date().toISOString();
    touchDirty();
  }

  function selectProject(projectId: string) {
    if (activeProjectId.value === projectId) {
      return;
    }
    const found = projects.value.find((item) => item.id === projectId);
    if (!found) {
      return;
    }
    void openProject(projectId);
  }

  async function openProject(projectId: string) {
    try {
      const project = await getProject(projectId);
      projectMode.value = "edit";
      setActiveProject(project);
    } catch {
      const fallback = getLocalProjects().find((project) => project.id === projectId);
      if (fallback) {
        projectMode.value = "edit";
        setActiveProject(fallback);
      }
    }
  }

  function createBlankProject() {
    const project = createProjectDraft(`Project ${projects.value.length + 1}`);
    projectMode.value = "new";
    setActiveProject(project);
    touchDirty();
  }

  async function saveActiveProject() {
    if (!activeProject.value) {
      return;
    }
    saveState.value = "saving";
    try {
      const previousProjectId = activeProjectId.value;
      const result = projectMode.value === "new"
        ? await createProject(activeProject.value)
        : await updateProject(activeProjectId.value, activeProject.value);
      setActiveProject(result);
      if (projectMode.value === "new" && previousProjectId && previousProjectId !== result.id) {
        projects.value = projects.value.filter((project) => project.id !== previousProjectId);
      }
      projectMode.value = "edit";
      saveState.value = "saved";
      lastSavedAt.value = new Date().toISOString();
    } catch {
      writeCache(activeProject.value);
      saveState.value = "error";
      error.value = "Project saved locally only. Backend persistence failed.";
    }
  }

  async function removeProject(projectId: string) {
    try {
      await deleteProject(projectId);
    } catch {
      // Local-only deletion when the API is unavailable.
    }
    projects.value = projects.value.filter((project) => project.id !== projectId);
    if (activeProjectId.value === projectId) {
      const next = projects.value[0];
      if (next) {
        await openProject(next.id);
      } else {
        createBlankProject();
      }
    }
  }

  function getCurrentLoop() {
    return activeLoop.value;
  }

  function setActiveLoop(loopId: string) {
    if (!activeProject.value) {
      return;
    }
    activeLoopId.value = loopId;
    activeProject.value.active_loop_id = loopId;
    touchDirty();
  }

  function updateLoop(loopId: string, patch: Partial<ProjectLoop>) {
    if (!activeProject.value) {
      return;
    }
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) {
      return;
    }
    Object.assign(loop, patch);
    loop.calculation_result = loop.calculation_result ? { ...loop.calculation_result } : null;
    activeProject.value.updated_at = new Date().toISOString();
    touchDirty();
    scheduleCalculation(loopId);
  }

  function addLoop() {
    if (!activeProject.value) {
      return;
    }
    const loop = createLoopFromIndex(activeProject.value.id, activeProject.value.loops.length + 1);
    activeProject.value.loops = [...activeProject.value.loops, loop];
    setActiveLoop(loop.id);
    touchDirty();
    scheduleCalculation(loop.id);
  }

  function removeLoop(loopId: string) {
    if (!activeProject.value || activeProject.value.loops.length <= 1) {
      return;
    }
    activeProject.value.loops = activeProject.value.loops.filter((loop) => loop.id !== loopId);
    activeProject.value.loops = activeProject.value.loops.map((loop, index) => ({ ...loop, sort_order: index + 1 }));
    const next = activeProject.value.loops[0];
    activeLoopId.value = next.id;
    activeProject.value.active_loop_id = next.id;
    touchDirty();
    scheduleCalculation(next.id);
  }

  function addDeviceRow(loopId: string) {
    if (!activeProject.value) {
      return;
    }
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) {
      return;
    }
    const row = createDeviceRowFromProduct(defaultProducts[0] ?? {
      id: "product-temp",
      category: "Detector",
      factory_name: "Generic",
      customer_name: "Generic",
      product_name: "Generic Detector",
      standby: 0.5,
      alarm: 2,
      ledCost: 1,
      type: "Detector",
      built_in: true
    }, loop.device_rows.length + 1);
    loop.device_rows = [...loop.device_rows, row];
    touchDirty();
    scheduleCalculation(loopId);
  }

  function addDeviceRowForCategory(loopId: string, category: string, products: ProductRecord[]) {
    if (!activeProject.value) {
      return false;
    }
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) {
      return false;
    }
    const totalQuantity = loop.device_rows.reduce((sum, row) => sum + row.qty, 0);
    if (totalQuantity >= loop.address_limit) {
      error.value = "Address limit reached for this loop.";
      return false;
    }
    const row = createDeviceRowForCategory(products, category, loop.device_rows.length + 1);
    loop.device_rows = [...loop.device_rows, row];
    error.value = null;
    touchDirty();
    scheduleCalculation(loopId);
    return true;
  }

  function updateDeviceRow(loopId: string, rowId: string, patch: Partial<LoopDeviceRow>) {
    if (!activeProject.value) {
      return;
    }
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) {
      return;
    }
    loop.device_rows = loop.device_rows.map((row) => (row.id === rowId ? { ...row, ...patch } : row));
    touchDirty();
    scheduleCalculation(loopId);
  }

  function removeDeviceRow(loopId: string, rowId: string) {
    if (!activeProject.value) {
      return;
    }
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) {
      return;
    }
    loop.device_rows = loop.device_rows.filter((row) => row.id !== rowId).map((row, index) => ({ ...row, sort_order: index + 1 }));
    touchDirty();
    scheduleCalculation(loopId);
  }

  function assignProductToRow(loopId: string, rowId: string, product: ProductRecord | null) {
    if (!product) {
      return;
    }
    updateDeviceRow(loopId, rowId, {
      product_id: product.id,
      category: product.category,
      display_name: product.product_name || product.customer_name,
      customer_name: product.customer_name,
      factory_name: product.factory_name,
      product_name: product.product_name,
      standby_ma: product.standby,
      alarm_ma: product.alarm,
      led_cost: product.ledCost,
      device_type: product.type
    });
  }

  function updateSystemParameters(loopId: string, patch: Partial<ProjectLoop>) {
    updateLoop(loopId, patch);
  }

  function scheduleCalculation(loopId: string) {
    const loop = activeProject.value?.loops.find((item) => item.id === loopId);
    if (!loop) {
      return;
    }
    const existing = calculationTimers.get(loopId);
    if (existing) {
      clearTimeout(existing);
    }
    calculationTimers.set(loopId, setTimeout(() => {
      void runCalculation(loopId);
    }, 250));
  }

  async function runCalculation(loopId: string) {
    if (!activeProject.value) {
      return;
    }
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) {
      return;
    }
    calculationBusyLoopIds.value = Array.from(new Set([...calculationBusyLoopIds.value, loopId]));
    const request = toCalculationRequest(loop);
    try {
      const result = await calculateLoop(request);
      loop.calculation_result = snapshotResult(result);
    } catch {
      const localResult = calculateLoopLocally(request);
      loop.calculation_result = snapshotResult(localResult);
    } finally {
      calculationBusyLoopIds.value = calculationBusyLoopIds.value.filter((id) => id !== loopId);
    }
  }

  function rowCount(loopId: string) {
    return activeProject.value?.loops.find((loop) => loop.id === loopId)?.device_rows.length ?? 0;
  }

  function ensureInitialCalculation() {
    if (activeLoop.value && !activeLoop.value.calculation_result) {
      scheduleCalculation(activeLoop.value.id);
    }
  }

  return {
    projects,
    activeProject,
    activeProjectId,
    activeLoopId,
    activeLoop,
    activeLoopIndex,
    loading,
    error,
    saveState,
    lastSavedAt,
    calculationBusyLoopIds,
    bootstrap,
    setProjectName,
    selectProject,
    openProject,
    createBlankProject,
    saveActiveProject,
    removeProject,
    setActiveLoop,
    updateLoop,
    addLoop,
    removeLoop,
    addDeviceRow,
    addDeviceRowForCategory,
    updateDeviceRow,
    removeDeviceRow,
    assignProductToRow,
    updateSystemParameters,
    scheduleCalculation,
    runCalculation,
    rowCount,
    getCurrentLoop,
    ensureInitialCalculation
  };
});
