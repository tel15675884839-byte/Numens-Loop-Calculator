import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { calculateLoop } from "../api/calculations";
import { createProject, deleteProject, getProject, listProjects, updateProject } from "../api/projects";
import { defaultProducts } from "../data/defaultProducts";
import { sampleWorkspaceProjects } from "../data/sampleWorkspace";
import { useDialogStore } from "./dialogStore";
import type { CalculationLoopRequest, CalculationLoopResponse } from "../types/calculation";
import type { LoopCalculationSnapshot, LoopDeviceRow, ProjectListItem, ProjectLoop, ProjectPrintProfile, ProjectRecord } from "../types/project";
import { calculateLoopLocally } from "../utils/calculation";
import { createDeviceRowForCategory, mapProductToDeviceRow } from "../utils/sampleData";
import { createId } from "../utils/ids";
import { readJson, writeJson } from "../utils/storage";
import type { ProductRecord } from "../types/product";

const WORKSPACE_CACHE_KEY = "loop-calculator.workspace.v2";
const MAX_LOOPS = 6;

type SaveState = "idle" | "dirty" | "saving" | "saved" | "error";
type ProjectMode = "new" | "edit";

const calculationTimers = new Map<string, ReturnType<typeof setTimeout>>();
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;
const AUTO_SAVE_DELAY_MS = 3000;

function cloneProject(project: ProjectRecord): ProjectRecord {
  return JSON.parse(JSON.stringify(project)) as ProjectRecord;
}

function projectChangeSignature(project: ProjectRecord): string {
  return JSON.stringify({
    id: project.id,
    name: project.name,
    print_profile: project.print_profile,
    loops: [...project.loops]
      .sort((left, right) => left.sort_order - right.sort_order)
      .map((loop) => ({
        id: loop.id,
        project_id: loop.project_id,
        name: loop.name,
        sort_order: loop.sort_order,
        address_limit: loop.address_limit,
        max_current_ma: loop.max_current_ma,
        min_voltage_v: loop.min_voltage_v,
        cable_size: loop.cable_size,
        cable_resistance_ohm_per_km: loop.cable_resistance_ohm_per_km,
        aux_current_ma: loop.aux_current_ma,
        device_rows: [...loop.device_rows].sort((left, right) => left.sort_order - right.sort_order)
      }))
  });
}

function isSounder(row: Partial<LoopDeviceRow>): boolean {
  if (String(row.category || "").trim().toLowerCase() === "sounder") return true;
  const haystack = [row.display_name, row.product_name, row.customer_name, row.factory_name, row.device_type]
    .map(s => String(s || ""))
    .join(" ")
    .toUpperCase();
  return haystack.includes("LSM") || haystack.includes("620-003");
}

function normalizeLoop(loop: ProjectLoop): ProjectLoop {
  return {
    ...loop,
    device_rows: [...loop.device_rows].sort((left, right) => left.sort_order - right.sort_order),
    calculation_result: loop.calculation_result ? { ...loop.calculation_result, diagnostics: [...loop.calculation_result.diagnostics] } : null
  };
}

function normalizeProject(project: ProjectRecord): ProjectRecord {
  const loops = [...project.loops]
    .sort((left, right) => left.sort_order - right.sort_order)
    .slice(0, MAX_LOOPS)
    .map((loop, index) => normalizeLoop({ ...loop, sort_order: index + 1 }));
  const activeLoopId = loops.some((loop) => loop.id === project.active_loop_id)
    ? project.active_loop_id
    : loops[0]?.id ?? "";

  return {
    ...project,
    print_profile: project.print_profile ?? null,
    active_loop_id: activeLoopId,
    loops
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
    print_profile: null,
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

function loopCalculationSignature(loop: ProjectLoop): string {
  return JSON.stringify(toCalculationRequest(loop));
}

function snapshotResult(result: CalculationLoopResponse): CalculationLoopSnapshot {
  return { ...result };
}

function calculateLocalSnapshot(loop: ProjectLoop): CalculationLoopSnapshot {
  return snapshotResult(calculateLoopLocally(toCalculationRequest(loop)));
}

function hydrateMissingLoopCalculations(project: ProjectRecord): ProjectRecord {
  return {
    ...project,
    loops: project.loops.map((loop) => ({
      ...loop,
      calculation_result: loop.calculation_result ?? calculateLocalSnapshot(loop)
    }))
  };
}

function createDeviceRowFromProduct(product: ProductRecord, sortOrder: number): LoopDeviceRow {
  return mapProductToDeviceRow(product, sortOrder);
}

function getLocalProjects() {
  return readJson<ProjectRecord[]>(WORKSPACE_CACHE_KEY) ?? sampleWorkspaceProjects;
}

function isMissingBackendProject(cause: unknown): boolean {
  return typeof cause === "object" && cause !== null && "status" in cause && (cause as { status?: unknown }).status === 404;
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
  const baselineProject = ref<ProjectRecord | null>(null);

  const activeLoop = computed(() => activeProject.value?.loops.find((loop) => loop.id === activeLoopId.value) ?? null);

  const activeLoopIndex = computed(() => activeProject.value?.loops.findIndex((loop) => loop.id === activeLoopId.value) ?? 0);

  const canAddLoop = computed(() => (activeProject.value?.loops.length ?? 0) < MAX_LOOPS);

  const hasUnsavedChanges = computed(() => {
    if (!activeProject.value || !baselineProject.value) {
      return false;
    }
    return projectChangeSignature(activeProject.value) !== projectChangeSignature(baselineProject.value);
  });

  function canLeaveActiveProject() {
    if (!hasUnsavedChanges.value) {
      return true;
    }
    const dialog = useDialogStore();
    return dialog.confirm({
      title: "Unsaved changes",
      message: "This project has unsaved changes. Discard changes before leaving?",
      confirmLabel: "Discard changes"
    }).then((shouldDiscard) => {
      if (shouldDiscard) {
        discardActiveProjectChanges();
      }
      return shouldDiscard;
    });
  }

  function touchDirty() {
    if (saveState.value !== "saving") {
      saveState.value = hasUnsavedChanges.value ? "dirty" : "idle";
    }
    // Auto-save: debounce 3 seconds after last edit
    if (hasUnsavedChanges.value) {
      if (autoSaveTimer) clearTimeout(autoSaveTimer);
      autoSaveTimer = setTimeout(() => {
        autoSaveTimer = null;
        if (hasUnsavedChanges.value && saveState.value === "dirty") {
          void saveActiveProject();
        }
      }, AUTO_SAVE_DELAY_MS);
    }
  }

  function writeCache(project: ProjectRecord | null) {
    if (!project) {
      return;
    }
    const current = getLocalProjects();
    const index = current.findIndex((p) => p.id === project.id);
    if (index >= 0) {
      current[index] = cloneProject(project);
    } else {
      current.unshift(cloneProject(project));
    }
    writeJson(WORKSPACE_CACHE_KEY, current);
  }

  function setActiveProject(project: ProjectRecord, mode: ProjectMode = "edit") {
    const normalized = hydrateMissingLoopCalculations(normalizeProject(cloneProject(project)));
    activeProject.value = normalized;
    activeProjectId.value = normalized.id;
    activeLoopId.value = normalized.active_loop_id || normalized.loops[0]?.id || "";
    baselineProject.value = cloneProject(normalized);
    saveState.value = "idle";
    projectMode.value = mode;
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
        setActiveProject(project, "edit");
      } else {
        const fallback = getLocalProjects()[0] ?? createProjectDraft();
        setActiveProject(fallback, "edit");
      }
    } catch (cause) {
      const localProjects = getLocalProjects();
      projects.value = localProjects.map((p) => ({
        id: p.id,
        name: p.name,
        active_loop_id: p.active_loop_id,
        loop_count: p.loops.length,
        created_at: p.created_at,
        updated_at: p.updated_at
      }));
      const fallback = localProjects[0] ?? createProjectDraft();
      setActiveProject(fallback, "edit");
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
    
    // Force reactivity update in sidebar list
    projects.value = projects.value.map((p) => 
      p.id === activeProject.value?.id ? { ...p, name } : p
    );
    
    touchDirty();
  }

  async function selectProject(projectId: string) {
    if (activeProjectId.value === projectId) {
      return;
    }
    const canLeave = canLeaveActiveProject();
    if (canLeave !== true) {
      if (!(await canLeave)) {
        return;
      }
    }
    const found = projects.value.find((item) => item.id === projectId);
    if (!found) {
      return;
    }
    void openProject(projectId);
  }

  async function openProject(projectId: string) {
    const fallback = getLocalProjects().find((project) => project.id === projectId);
    if (fallback) {
      setActiveProject(fallback, "edit");
    }
    try {
      const project = await getProject(projectId);
      if (activeProjectId.value === projectId) {
        setActiveProject(project, "edit");
      }
    } catch {
      // Keep the optimistic local switch when backend data is slow or unavailable.
    }
  }

  async function createBlankProject() {
    const canLeave = canLeaveActiveProject();
    if (canLeave !== true) {
      if (!(await canLeave)) {
        return;
      }
    }
    let counter = projects.value.length + 1;
    let name = `Project ${counter}`;
    while (projects.value.some((p) => p.name.toLowerCase() === name.toLowerCase())) {
      counter++;
      name = `Project ${counter}`;
    }
    const project = createProjectDraft(name);
    setActiveProject(project, "new");
  }

  async function saveActiveProject() {
    if (!activeProject.value) {
      return;
    }
    const trimmed = activeProject.value.name.trim();
    const isDuplicate = projects.value.some(
      (p) => p.id !== activeProject.value?.id && p.name.toLowerCase() === trimmed.toLowerCase()
    );
    if (isDuplicate) {
      const dialog = useDialogStore();
      await dialog.alert({
        title: "Duplicate project name",
        message: "A project with this name already exists. Please choose a different name."
      });
      saveState.value = "error";
      return;
    }

    saveState.value = "saving";
    try {
      const previousProjectId = activeProjectId.value;
      const wasNewProject = projectMode.value === "new";
      let result: ProjectRecord;
      if (wasNewProject) {
        result = await createProject(activeProject.value);
      } else {
        try {
          result = await updateProject(activeProjectId.value, activeProject.value);
        } catch (cause) {
          if (!isMissingBackendProject(cause)) {
            throw cause;
          }
          result = await createProject(activeProject.value);
        }
      }
      setActiveProject(result, "edit");
      if (wasNewProject && previousProjectId && previousProjectId !== result.id) {
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

  async function savePrintProfile(profile: ProjectPrintProfile) {
    if (!activeProject.value) {
      return;
    }
    activeProject.value.print_profile = { ...profile };
    activeProject.value.updated_at = new Date().toISOString();
    touchDirty();
    await saveActiveProject();
  }

  async function removeProject(projectId: string) {
    try {
      await deleteProject(projectId);
    } catch {
      // Local-only deletion when the API is unavailable.
    }
    projects.value = [...projects.value.filter((project) => project.id !== projectId)];
    const currentCache = getLocalProjects().filter((p) => p.id !== projectId);
    writeJson(WORKSPACE_CACHE_KEY, currentCache);
    if (activeProjectId.value === projectId) {
      const next = projects.value[0];
      if (next) {
        await openProject(next.id);
      } else {
        await createBlankProject();
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
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) {
      return;
    }
    activeLoopId.value = loopId;
    activeProject.value.active_loop_id = loopId;
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
    activeProject.value.updated_at = new Date().toISOString();
    refreshLoopCalculation(loopId);
    touchDirty();
  }

  function addLoop() {
    if (!activeProject.value || !canAddLoop.value) {
      return;
    }
    const loop = createLoopFromIndex(activeProject.value.id, activeProject.value.loops.length + 1);
    loop.calculation_result = calculateLocalSnapshot(loop);
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
    refreshLoopCalculation(loopId);
    touchDirty();
  }

  function addDeviceRowForCategory(loopId: string, category: string, products: ProductRecord[]) {
    if (!activeProject.value) return false;
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) return false;

    const totalQuantity = loop.device_rows.reduce((sum, row) => sum + row.qty, 0);
    if (totalQuantity >= loop.address_limit) {
      error.value = "Address limit reached for this loop.";
      return false;
    }

    const row = createDeviceRowForCategory(products, category, loop.device_rows.length + 1);
    
    if (isSounder(row)) {
      const sounderTotal = loop.device_rows.reduce((sum, r) => isSounder(r) ? sum + r.qty : sum, 0);
      if (sounderTotal >= 32) {
        error.value = "Sounder limit (32) reached for this loop.";
        return false;
      }
    }

    loop.device_rows = [...loop.device_rows, row];
    error.value = null;
    refreshLoopCalculation(loopId);
    touchDirty();
    return true;
  }

  function updateDeviceRow(loopId: string, rowId: string, patch: Partial<LoopDeviceRow>) {
    if (!activeProject.value) return;
    const loop = activeProject.value.loops.find((item) => item.id === loopId);
    if (!loop) return;

    const rowIndex = loop.device_rows.findIndex((r) => r.id === rowId);
    if (rowIndex === -1) return;

    const currentRow = loop.device_rows[rowIndex];
    const nextRow = { ...currentRow, ...patch };

    // Enforce limits
    let newQty = nextRow.qty;
    
    // 1. Total limit check
    const otherTotal = loop.device_rows.reduce((sum, r) => sum + (r.id === rowId ? 0 : r.qty), 0);
    const maxAllowed = Math.max(1, loop.address_limit - otherTotal);
    
    // 2. Sounder limit check
    let maxSounderAllowed = newQty;
    if (isSounder(nextRow)) {
      const otherSounderTotal = loop.device_rows.reduce((sum, r) => {
        if (r.id !== rowId && isSounder(r)) return sum + r.qty;
        return sum;
      }, 0);
      maxSounderAllowed = Math.max(1, 32 - otherSounderTotal);
    }
    
    const finalAllowedQty = Math.min(maxAllowed, maxSounderAllowed);
    if (newQty > finalAllowedQty) {
      newQty = finalAllowedQty;
    }

    nextRow.qty = newQty;
    loop.device_rows = loop.device_rows.map((row) => (row.id === rowId ? nextRow : row));
    
    refreshLoopCalculation(loopId);
    touchDirty();
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
    refreshLoopCalculation(loopId);
    touchDirty();
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

  function refreshLoopCalculation(loopId: string) {
    const loop = activeProject.value?.loops.find((item) => item.id === loopId);
    if (!loop) {
      return;
    }
    loop.calculation_result = calculateLocalSnapshot(loop);
    scheduleCalculation(loopId);
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
    const requestSignature = loopCalculationSignature(loop);
    const applyIfCurrent = (result: CalculationLoopResponse) => {
      const currentLoop = activeProject.value?.loops.find((item) => item.id === loopId);
      if (!currentLoop || loopCalculationSignature(currentLoop) !== requestSignature) {
        return;
      }
      currentLoop.calculation_result = snapshotResult(result);
    };
    try {
      const result = await calculateLoop(request);
      applyIfCurrent(result);
    } catch {
      const localResult = calculateLoopLocally(request);
      applyIfCurrent(localResult);
    } finally {
      calculationBusyLoopIds.value = calculationBusyLoopIds.value.filter((id) => id !== loopId);
    }
  }

  function rowCount(loopId: string) {
    return activeProject.value?.loops.find((loop) => loop.id === loopId)?.device_rows.length ?? 0;
  }

  function isProjectUnsaved(projectId: string) {
    return activeProjectId.value === projectId && hasUnsavedChanges.value;
  }

  function discardActiveProjectChanges() {
    if (!baselineProject.value) {
      saveState.value = "idle";
      return;
    }
    const mode = projectMode.value;
    setActiveProject(baselineProject.value, mode);
    saveState.value = "idle";
  }

  function ensureInitialCalculation() {
    if (!activeProject.value) {
      return;
    }
    for (const loop of activeProject.value.loops) {
      if (!loop.calculation_result) {
        loop.calculation_result = calculateLocalSnapshot(loop);
      }
    }
  }

  function exportActiveProject() {
    if (!activeProject.value) return;
    const data = cloneProject(activeProject.value);
    // Strip calculation results for a clean export
    for (const loop of data.loops) {
      (loop as ProjectLoop & { calculation_result?: unknown }).calculation_result = undefined;
    }
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${data.name.replace(/[^a-zA-Z0-9_\- ]/g, "_")}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  }

  async function importProject(file: File) {
    try {
      const text = await file.text();
      const data = JSON.parse(text) as ProjectRecord;
      // Validate basic structure
      if (!data.name || !Array.isArray(data.loops)) {
        error.value = "Invalid project file: missing name or loops.";
        return;
      }
      if (data.loops.length > MAX_LOOPS) {
        error.value = `Import rejected: project contains ${data.loops.length} loops (max ${MAX_LOOPS}).`;
        return;
      }
      // Assign new IDs to avoid collisions
      const newProjectId = createId("project");
      data.id = newProjectId;
      data.created_at = new Date().toISOString();
      data.updated_at = new Date().toISOString();
      for (const loop of data.loops) {
        const newLoopId = createId("loop");
        if (data.active_loop_id === loop.id) {
          data.active_loop_id = newLoopId;
        }
        loop.id = newLoopId;
        loop.project_id = newProjectId;
        for (const row of loop.device_rows) {
          row.id = createId("row");
        }
        loop.calculation_result = calculateLocalSnapshot(loop);
      }
      if (!data.active_loop_id || !data.loops.some(l => l.id === data.active_loop_id)) {
        data.active_loop_id = data.loops[0]?.id ?? "";
      }
      setActiveProject(data, "new");
      error.value = null;
    } catch {
      error.value = "Failed to parse project file. Ensure it is valid JSON.";
    }
  }

  return {
    projects,
    activeProject,
    activeProjectId,
    activeLoopId,
    activeLoop,
    activeLoopIndex,
    canAddLoop,
    loading,
    error,
    saveState,
    lastSavedAt,
    hasUnsavedChanges,
    calculationBusyLoopIds,
    canLeaveActiveProject,
    discardActiveProjectChanges,
    bootstrap,
    setProjectName,
    selectProject,
    openProject,
    createBlankProject,
    saveActiveProject,
    savePrintProfile,
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
    isProjectUnsaved,
    getCurrentLoop,
    ensureInitialCalculation,
    exportActiveProject,
    importProject
  };
});
