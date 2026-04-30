import { computed, ref } from "vue";
import { defineStore } from "pinia";
import type { ProjectPrintProfile, ProjectRecord } from "../types/project";
import { createBlankPrintProfile, hasRequiredPrintProfileFields } from "../types/print";
import { useWorkspaceStore } from "./workspaceStore";
import { readJson, writeJson } from "../utils/storage";

const TEMPLATES_CACHE_KEY = "loop-calculator.report-templates.v1";

interface NamedTemplate extends ProjectPrintProfile {
  template_name: string;
  created_at?: string;
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

function sortTemplatesByCreatedAt(items: NamedTemplate[]) {
  return [...items].sort((first, second) => {
    const firstTime = first.created_at ? Date.parse(first.created_at) : 0;
    const secondTime = second.created_at ? Date.parse(second.created_at) : 0;
    return firstTime - secondTime;
  });
}



export const usePrintStore = defineStore("print", () => {
  const projectId = ref<string | null>(null);
  const savedProfile = ref<ProjectPrintProfile | null>(null);
  const draftProfile = ref<ProjectPrintProfile | null>(null);
  const editingProfile = ref<ProjectPrintProfile | null>(null);
  const calculationReady = ref(false);
  const templates = ref<NamedTemplate[]>([]);
  const selectedTemplateName = ref<string | null>(null);

  const canPrint = computed(() => calculationReady.value);

  function initializeFromProject(project: ProjectRecord | null, issueDate = localDateString()) {
    projectId.value = project?.id ?? null;
    templates.value = sortTemplatesByCreatedAt(readJson<NamedTemplate[]>(TEMPLATES_CACHE_KEY) ?? []);
    calculationReady.value = projectCalculationsAreReady(project);
    savedProfile.value = project?.print_profile
      ? cloneProfile(project.print_profile)
      : createBlankPrintProfile(issueDate);
    draftProfile.value = cloneProfile(savedProfile.value);
    editingProfile.value = cloneProfile(savedProfile.value);
    selectedTemplateName.value = null;
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

  function updateEditingProfile(patch: Partial<ProjectPrintProfile>) {
    if (!editingProfile.value) {
      return;
    }
    editingProfile.value = {
      ...editingProfile.value,
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
    if (!name.trim()) {
      return;
    }
    const templateName = name.trim();
    const existingTemplate = templates.value.find(t => t.template_name === templateName);
    const newTemplate: NamedTemplate = {
      ...createBlankPrintProfile(""),
      template_name: templateName,
      created_at: existingTemplate?.created_at ?? new Date().toISOString()
    };
    const filtered = templates.value.filter(t => t.template_name !== newTemplate.template_name);
    templates.value = sortTemplatesByCreatedAt([...filtered, newTemplate]);
    selectedTemplateName.value = newTemplate.template_name;
    editingProfile.value = cloneProfile(newTemplate);
    writeJson(TEMPLATES_CACHE_KEY, templates.value);
  }

  function selectTemplate(name: string) {
    const template = templates.value.find(t => t.template_name === name);
    if (!editingProfile.value) {
      return;
    }
    if (!template) {
      selectedTemplateName.value = null;
      return;
    }
    selectedTemplateName.value = template.template_name;
    editingProfile.value = cloneProfile(template);
  }

  function applyTemplate(template: NamedTemplate) {
    selectTemplate(template.template_name);
  }

  function saveSelectedTemplate() {
    if (!selectedTemplateName.value || !editingProfile.value) {
      return;
    }
    const existingTemplate = templates.value.find(t => t.template_name === selectedTemplateName.value);
    const updatedTemplate: NamedTemplate = {
      ...cloneProfile(editingProfile.value),
      template_name: selectedTemplateName.value,
      created_at: existingTemplate?.created_at ?? new Date().toISOString()
    };
    templates.value = sortTemplatesByCreatedAt(templates.value.map(t =>
      t.template_name === selectedTemplateName.value ? updatedTemplate : t
    ));
    writeJson(TEMPLATES_CACHE_KEY, templates.value);
  }

  function clearSelectedTemplateDraft() {
    if (!selectedTemplateName.value) {
      return;
    }
    editingProfile.value = createBlankPrintProfile("");
    draftProfile.value = cloneProfile(editingProfile.value);
  }

  function renameSelectedTemplate(newName: string) {
    if (!selectedTemplateName.value || !newName.trim()) return;
    const oldName = selectedTemplateName.value;
    const freshName = newName.trim();
    if (oldName === freshName) return;

    templates.value = templates.value.map(t => {
      if (t.template_name === oldName) {
        return { ...t, template_name: freshName };
      }
      return t;
    });
    selectedTemplateName.value = freshName;
    writeJson(TEMPLATES_CACHE_KEY, templates.value);
  }

  function deselectTemplate() {
    selectedTemplateName.value = null;
    editingProfile.value = draftProfile.value ? cloneProfile(draftProfile.value) : null;
  }

  function deleteSelectedTemplate() {
    if (!selectedTemplateName.value) {
      return;
    }
    deleteTemplate(selectedTemplateName.value);
    selectedTemplateName.value = null;
    draftProfile.value = savedProfile.value ? cloneProfile(savedProfile.value) : null;
    editingProfile.value = draftProfile.value ? cloneProfile(draftProfile.value) : null;
  }

  function deleteTemplate(name: string) {
    templates.value = templates.value.filter(t => t.template_name !== name);
    if (selectedTemplateName.value === name) {
      selectedTemplateName.value = null;
    }
    writeJson(TEMPLATES_CACHE_KEY, templates.value);
  }

  function printNow() {
    if (!calculationReady.value) {
      alert("Please wait for all loop calculations to complete before printing.");
      return;
    }
    window.print();
  }

  function applyToReport() {
    if (!editingProfile.value) return;
    draftProfile.value = cloneProfile(editingProfile.value);
    saveDefaults();
  }

  return {
    projectId,
    savedProfile,
    draftProfile,
    editingProfile,
    calculationReady,
    templates,
    selectedTemplateName,
    canPrint,
    initializeFromProject,
    refreshCalculationReady,
    updateDraft,
    updateEditingProfile,
    resetDraft,
    saveDefaults,
    saveAsTemplate,
    selectTemplate,
    applyTemplate,
    saveSelectedTemplate,
    clearSelectedTemplateDraft,
    renameSelectedTemplate,
    deselectTemplate,
    deleteSelectedTemplate,
    deleteTemplate,
    applyToReport,
    printNow
  };
});
