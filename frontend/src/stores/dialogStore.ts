import { ref } from "vue";
import { defineStore } from "pinia";

type DialogKind = "alert" | "confirm" | "prompt";

interface DialogOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  initialValue?: string;
}

interface ActiveDialog {
  kind: DialogKind;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  promptValue: string;
}

type DialogResolver = (value: boolean | string | null | void) => void;

export const useDialogStore = defineStore("dialog", () => {
  const activeDialog = ref<ActiveDialog | null>(null);
  let resolver: DialogResolver | null = null;

  function open(kind: DialogKind, options: DialogOptions) {
    if (resolver) {
      resolver(kind === "prompt" ? null : false);
    }

    activeDialog.value = {
      kind,
      title: options.title,
      message: options.message,
      confirmLabel: options.confirmLabel ?? (kind === "alert" ? "OK" : "Continue"),
      cancelLabel: options.cancelLabel ?? "Cancel",
      promptValue: options.initialValue ?? ""
    };

    return new Promise<boolean | string | null | void>((resolve) => {
      resolver = resolve;
    });
  }

  function alert(options: DialogOptions) {
    return open("alert", options) as Promise<void>;
  }

  function confirm(options: DialogOptions) {
    return open("confirm", options) as Promise<boolean>;
  }

  function prompt(options: DialogOptions) {
    return open("prompt", options) as Promise<string | null>;
  }

  function updatePromptValue(value: string) {
    if (activeDialog.value) {
      activeDialog.value.promptValue = value;
    }
  }

  function resolve(confirmed: boolean) {
    if (!activeDialog.value || !resolver) {
      return;
    }

    const current = activeDialog.value;
    const complete = resolver;
    activeDialog.value = null;
    resolver = null;

    if (current.kind === "alert") {
      complete(undefined);
      return;
    }

    if (current.kind === "prompt") {
      complete(confirmed ? current.promptValue : null);
      return;
    }

    complete(confirmed);
  }

  return {
    activeDialog,
    alert,
    confirm,
    prompt,
    updatePromptValue,
    resolve
  };
});
