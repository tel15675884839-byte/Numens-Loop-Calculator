import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import router from "../index";
import { useWorkspaceStore } from "../../stores/workspaceStore";

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

describe("router", () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.restoreAllMocks();
    localStorage.clear();
    await router.push("/");
  });

  it("blocks route changes when unsaved navigation is cancelled", async () => {
    const store = useWorkspaceStore();
    store.createBlankProject();
    store.setProjectName("Unsaved configuration");

    const navigation = router.push("/products").catch(() => undefined);
    const dialogStore = (await import("../../stores/dialogStore")).useDialogStore();
    expect(dialogStore.activeDialog?.message).toBe("This project has unsaved changes. Discard changes before leaving?");
    expect(dialogStore.activeDialog?.confirmLabel).toBe("Discard changes");
    dialogStore.resolve(false);
    await navigation;

    expect(router.currentRoute.value.name).toBe("workspace");
  });

  it("allows route changes when unsaved navigation is confirmed", async () => {
    const store = useWorkspaceStore();
    store.createBlankProject();
    store.setProjectName("Unsaved configuration");

    const navigation = router.push("/products");
    const dialogStore = (await import("../../stores/dialogStore")).useDialogStore();
    expect(dialogStore.activeDialog?.message).toBe("This project has unsaved changes. Discard changes before leaving?");
    expect(dialogStore.activeDialog?.confirmLabel).toBe("Discard changes");
    dialogStore.resolve(true);
    await navigation;

    expect(router.currentRoute.value.name).toBe("products");
    expect(store.hasUnsavedChanges).toBe(false);
  });

  it("does not block route changes when the active project has no edits", async () => {
    const store = useWorkspaceStore();
    store.createBlankProject();

    const navigation = router.push("/products");
    const dialogStore = (await import("../../stores/dialogStore")).useDialogStore();

    expect(dialogStore.activeDialog).toBeNull();
    await navigation;

    expect(router.currentRoute.value.name).toBe("products");
  });

  it("does not block navigation when leaving non-workspace pages", async () => {
    const store = useWorkspaceStore();
    store.createBlankProject();
    store.setProjectName("Unsaved configuration");

    const toProducts = router.push("/products");
    const dialogStore = (await import("../../stores/dialogStore")).useDialogStore();
    dialogStore.resolve(true);
    await toProducts;

    const backToWorkspace = router.push("/");
    expect(dialogStore.activeDialog).toBeNull();
    await backToWorkspace;

    expect(router.currentRoute.value.name).toBe("workspace");
  });
});
