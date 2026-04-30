import { computed, ref } from "vue";
import { defineStore } from "pinia";
import type { ProjectPrintProfile, ProjectRecord } from "../types/project";
import { createBlankPrintProfile, hasRequiredPrintProfileFields } from "../types/print";
import { useWorkspaceStore } from "./workspaceStore";
import { readJson, writeJson } from "../utils/storage";

const TEMPLATES_CACHE_KEY = "loop-calculator.report-templates.v1";

interface NamedTemplate extends ProjectPrintProfile {
  template_name: string;
}

function cloneProfile(profile: ProjectPrintProfile): ProjectPrintProfile {
  return { ...profile };
}

function localDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function projectCalculationsAreReady(project: ProjectRecord | null) {
  return Boolean(project?.loops.length) && Boolean(project?.loops.every((loop) => loop.calculation_result));
}

export const usePrintStore = defineStore("print", () => {
  const projectId = ref<string | null>(null);
  const savedProfile = ref<ProjectPrintProfile | null>(null);
  const draftProfile = ref<ProjectPrintProfile | null>(null);
  const calculationReady = ref(false);
  const templates = ref<NamedTemplate[]>(readJson<NamedTemplate[]>(TEMPLATES_CACHE_KEY) ?? []);

  const canPrint = computed(() => calculationReady.value && hasRequiredPrintProfileFields(draftProfile.value));

  function initializeFromProject(project: ProjectRecord | null, issueDate = localDateString()) {
    projectId.value = project?.id ?? null;
    calculationReady.value = projectCalculationsAreReady(project);
    savedProfile.value = project?.print_profile
      ? cloneProfile(project.print_profile)
      : createBlankPrintProfile(issueDate);
    draftProfile.value = cloneProfile(savedProfile.value);
  }

  function refreshCalculationReady(project: ProjectRecord | null) {
    calculationReady.value = projectCalculationsAreReady(project);
  }

  function updateDraft(patch: Partial<ProjectPrintProfile>) {
    if (!draftProfile.value) {
      return;
    }
    draftProfile.value = {
      ...draftProfile.value,
      ...patch
    };
  }

  function resetDraft() {
    draftProfile.value = savedProfile.value ? cloneProfile(savedProfile.value) : null;
  }

  function saveDefaults() {
    if (!draftProfile.value) {
      return;
    }
    const workspace = useWorkspaceStore();
    void workspace.savePrintProfile(cloneProfile(draftProfile.value));
    savedProfile.value = cloneProfile(draftProfile.value);
  }

  function saveAsTemplate(name: string) {
    if (!draftProfile.value || !name.trim()) {
      return;
    }
    const newTemplate: NamedTemplate = {
      ...cloneProfile(draftProfile.value),
      template_name: name.trim()
    };
    // Remove if exists with same name
    const filtered = templates.value.filter(t => t.template_name !== newTemplate.template_name);
    templates.value = [newTemplate, ...filtered];
    writeJson(TEMPLATES_CACHE_KEY, templates.value);
  }

  function applyTemplate(template: NamedTemplate) {
    if (!draftProfile.value) {
      return;
    }
    // Apply all fields except possibly issue_date if user wants to keep current
    // But for "Template" it's usually better to apply everything and let user adjust
    draftProfile.value = cloneProfile(template);
  }

  function deleteTemplate(name: string) {
    templates.value = templates.value.filter(t => t.template_name !== name);
    writeJson(TEMPLATES_CACHE_KEY, templates.value);
  }

  function printNow() {
    if (!canPrint.value) {
      return;
    }
    window.print();
  }

  return {
    projectId,
    savedProfile,
    draftProfile,
    calculationReady,
    templates,
    canPrint,
    initializeFromProject,
    refreshCalculationReady,
    updateDraft,
    resetDraft,
    saveDefaults,
    saveAsTemplate,
    applyTemplate,
    deleteTemplate,
    printNow
  };
});
