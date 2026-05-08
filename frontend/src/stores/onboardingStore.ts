import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { readJson, writeJson } from "../utils/storage";

type OnboardingScope = "workspace" | "print";

const ONBOARDING_STORAGE_KEYS: Record<OnboardingScope, string> = {
  workspace: "loop-calculator.onboarding.workspace.v1",
  print: "loop-calculator.onboarding.print.v1"
};

interface OnboardingStorageState {
  completed: boolean;
}

export interface OnboardingStep {
  target: string;
  title: string;
  description: string;
  placement: "top" | "right" | "bottom" | "left";
}

const workspaceSteps: OnboardingStep[] = [
  {
    target: "project-settings",
    title: "Project settings",
    description: "Name the current project here so exported files and printed reports are easy to identify.",
    placement: "bottom"
  },
  {
    target: "project-list",
    title: "Projects",
    description: "Use this list to switch between saved projects or delete projects you no longer need.",
    placement: "right"
  },
  {
    target: "project-actions",
    title: "Project actions",
    description: "Create a new project, save changes, or import and export project JSON files from this compact action group.",
    placement: "bottom"
  },
  {
    target: "loop-tabs",
    title: "Loop tabs",
    description: "Create and switch between loops. Each project can contain up to 6 loops.",
    placement: "bottom"
  },
  {
    target: "system-parameters",
    title: "System parameters",
    description: "Set address limits, current limit, voltage threshold, cable resistance, and auxiliary current.",
    placement: "bottom"
  },
  {
    target: "device-table",
    title: "Device table",
    description: "Add devices by category, choose products, then adjust quantities and distances for the active loop.",
    placement: "top"
  },
  {
    target: "calculation-results",
    title: "Live results",
    description: "Review device quantity, current demand, voltage drop, cable recommendation, and diagnostics in real time.",
    placement: "left"
  }
];

const printSteps: OnboardingStep[] = [
  {
    target: "print-actions",
    title: "Print actions",
    description: "Return to the workspace, switch theme, or send the current report preview to the printer.",
    placement: "bottom"
  },
  {
    target: "print-templates",
    title: "Saved templates",
    description: "Choose saved report profile templates here. Templates let you reuse customer, site, revision, and prepared-by details across reports.",
    placement: "right"
  },
  {
    target: "print-template-editor",
    title: "Template fields",
    description: "After selecting or creating a template, edit report fields such as Project No, Customer, Site, Panel, Revision, Prepared By, Issue Date, and Notes.",
    placement: "right"
  },
  {
    target: "print-template-actions",
    title: "Template actions",
    description: "Create a new template, apply selected template data to the report, save edits, rename a template, or delete one you no longer need.",
    placement: "top"
  },
  {
    target: "print-preview",
    title: "Print preview",
    description: "Check the paged report preview, then use Print to generate the final project document.",
    placement: "left"
  }
];

export const onboardingSteps = workspaceSteps;

const stepsByScope: Record<OnboardingScope, OnboardingStep[]> = {
  workspace: workspaceSteps,
  print: printSteps
};

export const useOnboardingStore = defineStore("onboarding", () => {
  const isOpen = ref(false);
  const currentStepIndex = ref(0);
  const activeScope = ref<OnboardingScope>("workspace");

  const activeSteps = computed(() => stepsByScope[activeScope.value]);
  const currentStep = computed(() => activeSteps.value[currentStepIndex.value] ?? null);
  const currentStepNumber = computed(() => currentStepIndex.value + 1);
  const totalSteps = computed(() => activeSteps.value.length);
  const isFirstStep = computed(() => currentStepIndex.value === 0);
  const isLastStep = computed(() => currentStepIndex.value === activeSteps.value.length - 1);

  function hasCompleted(scope: OnboardingScope) {
    return readJson<OnboardingStorageState>(ONBOARDING_STORAGE_KEYS[scope])?.completed === true;
  }

  function persistCompleted() {
    writeJson(ONBOARDING_STORAGE_KEYS[activeScope.value], { completed: true });
  }

  function openAtStart(scope: OnboardingScope) {
    activeScope.value = scope;
    currentStepIndex.value = 0;
    isOpen.value = true;
  }

  function initialize(scope: OnboardingScope = "workspace") {
    activeScope.value = scope;
    currentStepIndex.value = 0;
    isOpen.value = false;
    if (!hasCompleted(scope)) {
      openAtStart(scope);
    }
  }

  function closeAndComplete() {
    persistCompleted();
    isOpen.value = false;
    currentStepIndex.value = 0;
  }

  function nextStep() {
    if (isLastStep.value) {
      closeAndComplete();
      return;
    }
    currentStepIndex.value += 1;
  }

  function previousStep() {
    if (!isFirstStep.value) {
      currentStepIndex.value -= 1;
    }
  }

  function skip() {
    closeAndComplete();
  }

  function startReplay(scope: OnboardingScope = activeScope.value) {
    openAtStart(scope);
  }

  return {
    isOpen,
    currentStepIndex,
    activeScope,
    currentStep,
    currentStepNumber,
    totalSteps,
    isFirstStep,
    isLastStep,
    initialize,
    nextStep,
    previousStep,
    skip,
    startReplay
  };
});
