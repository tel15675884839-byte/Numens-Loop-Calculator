<template>
  <Teleport to="body">
    <Transition name="ios-dialog">
      <div
        v-if="dialog.activeDialog"
        class="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/45 px-4"
        @keydown.esc="cancel"
      >
        <div
          class="panel w-full max-w-md shadow-2xl"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
        >
          <div class="border-b border-zinc-200 px-4 py-3">
            <h2 :id="titleId" class="text-sm font-semibold text-zinc-900">{{ dialog.activeDialog.title }}</h2>
          </div>
          <div class="space-y-4 px-4 py-4">
            <p class="text-sm leading-6 text-zinc-600">{{ dialog.activeDialog.message }}</p>
            <input
              v-if="dialog.activeDialog.kind === 'prompt'"
              ref="promptInput"
              class="field"
              :value="dialog.activeDialog.promptValue"
              @input="onInput"
              @keydown.enter="confirm"
              aria-label="Dialog input"
            />
          </div>
          <div class="flex items-center justify-end gap-2 border-t border-zinc-200 px-4 py-3">
            <button
              v-if="dialog.activeDialog.kind !== 'alert'"
              class="toolbar-button"
              @click="cancel"
            >
              {{ dialog.activeDialog.cancelLabel }}
            </button>
            <button class="toolbar-button-primary" @click="confirm">
              {{ dialog.activeDialog.confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { useDialogStore } from "../../stores/dialogStore";

const dialog = useDialogStore();
const titleId = "app-dialog-title";
const promptInput = ref<HTMLInputElement | null>(null);

watch(
  () => dialog.activeDialog,
  async (newVal) => {
    if (newVal?.kind === "prompt") {
      await nextTick();
      promptInput.value?.focus();
    }
  },
  { deep: true }
);

function onInput(event: Event) {
  dialog.updatePromptValue((event.target as HTMLInputElement).value);
}

function cancel() {
  dialog.resolve(false);
}

function confirm() {
  dialog.resolve(true);
}
</script>

<style scoped>
.ios-dialog-enter-active,
.ios-dialog-leave-active {
  transition: opacity 0.3s ease-out;
}

.ios-dialog-enter-active .panel,
.ios-dialog-leave-active .panel {
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease-out;
}

.ios-dialog-enter-from {
  opacity: 0;
}

.ios-dialog-enter-from .panel {
  transform: scale(0.85);
  opacity: 0;
}

.ios-dialog-leave-to {
  opacity: 0;
}

.ios-dialog-leave-to .panel {
  transform: scale(0.95);
  opacity: 0;
}
</style>
