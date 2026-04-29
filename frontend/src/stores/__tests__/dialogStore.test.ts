import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useDialogStore } from "../dialogStore";

describe("dialogStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("resolves confirm dialogs from the app modal state", async () => {
    const store = useDialogStore();

    const result = store.confirm({
      title: "Unsaved changes",
      message: "The current project has unsaved changes. Continue anyway?"
    });

    expect(store.activeDialog?.kind).toBe("confirm");
    expect(store.activeDialog?.title).toBe("Unsaved changes");

    store.resolve(true);

    await expect(result).resolves.toBe(true);
    expect(store.activeDialog).toBeNull();
  });

  it("resolves prompt dialogs with entered text", async () => {
    const store = useDialogStore();

    const result = store.prompt({
      title: "Rename project",
      message: "Enter new project name:",
      initialValue: "Project 1"
    });

    expect(store.activeDialog?.kind).toBe("prompt");
    store.updatePromptValue("Project 2");
    store.resolve(true);

    await expect(result).resolves.toBe("Project 2");
    expect(store.activeDialog).toBeNull();
  });
});
