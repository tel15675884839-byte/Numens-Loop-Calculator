import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useOnboardingStore } from "../onboardingStore";

const WORKSPACE_STORAGE_KEY = "loop-calculator.onboarding.workspace.v1";
const PRINT_STORAGE_KEY = "loop-calculator.onboarding.print.v1";

describe("onboardingStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it("opens the workspace tour when no workspace completion is stored", () => {
    const store = useOnboardingStore();

    store.initialize("workspace");

    expect(store.isOpen).toBe(true);
    expect(store.activeScope).toBe("workspace");
    expect(store.currentStep?.target).toBe("project-settings");
    expect(store.currentStepNumber).toBe(1);
    expect(store.totalSteps).toBe(7);
  });

  it("opens the print tour when no print completion is stored", () => {
    const store = useOnboardingStore();

    store.initialize("print");

    expect(store.isOpen).toBe(true);
    expect(store.activeScope).toBe("print");
    expect(store.currentStep?.target).toBe("print-actions");
    expect(store.totalSteps).toBe(5);
  });

  it("stays closed after the workspace tutorial was completed", () => {
    localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify({ completed: true }));
    const store = useOnboardingStore();

    store.initialize("workspace");

    expect(store.isOpen).toBe(false);
  });

  it("tracks print completion separately from workspace completion", () => {
    localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify({ completed: true }));
    const store = useOnboardingStore();

    store.initialize("print");

    expect(store.isOpen).toBe(true);
    expect(store.activeScope).toBe("print");
    expect(store.currentStep?.target).toBe("print-actions");
  });

  it("persists completion when the final step is completed", () => {
    const store = useOnboardingStore();
    store.initialize("workspace");

    while (!store.isLastStep) {
      store.nextStep();
    }
    store.nextStep();

    expect(store.isOpen).toBe(false);
    expect(localStorage.getItem(WORKSPACE_STORAGE_KEY)).toBe(JSON.stringify({ completed: true }));
  });

  it("persists completion when skipped", () => {
    const store = useOnboardingStore();
    store.initialize("workspace");

    store.skip();

    expect(store.isOpen).toBe(false);
    expect(localStorage.getItem(WORKSPACE_STORAGE_KEY)).toBe(JSON.stringify({ completed: true }));
  });

  it("can replay the workspace tutorial even after completion", () => {
    localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify({ completed: true }));
    const store = useOnboardingStore();
    store.initialize("workspace");

    store.startReplay("workspace");

    expect(store.isOpen).toBe(true);
    expect(store.activeScope).toBe("workspace");
    expect(store.currentStepIndex).toBe(0);
    expect(store.currentStep?.target).toBe("project-settings");
  });

  it("can replay the print tutorial without showing workspace steps", () => {
    localStorage.setItem(PRINT_STORAGE_KEY, JSON.stringify({ completed: true }));
    const store = useOnboardingStore();
    store.initialize("print");

    store.startReplay("print");

    const targets = Array.from({ length: store.totalSteps }, () => {
      const target = store.currentStep?.target;
      store.nextStep();
      return target;
    });

    expect(store.activeScope).toBe("print");
    expect(targets).toEqual(["print-actions", "print-templates", "print-template-editor", "print-template-actions", "print-preview"]);
    expect(targets).not.toContain("project-actions");
  });

  it("keeps print guidance focused on templates and preview", () => {
    const store = useOnboardingStore();
    store.initialize("print");

    const targets = Array.from({ length: store.totalSteps }, () => {
      const target = store.currentStep?.target;
      store.nextStep();
      return target;
    });

    expect(targets).toContain("print-templates");
    expect(targets).toContain("print-template-editor");
    expect(targets).toContain("print-template-actions");
    expect(targets).toContain("print-preview");
  });
});
