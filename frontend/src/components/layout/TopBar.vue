<template>
  <header class="flex h-16 items-center justify-between border-b border-zinc-200 bg-white px-4">
    <div class="flex min-w-0 items-center gap-4">
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ sectionLabel }}</p>
        <div v-if="isWorkspace" class="flex min-w-0 items-center gap-3">
          <input
            class="field max-w-[18rem] border-transparent bg-transparent px-2 py-1 text-base font-semibold text-zinc-900 focus:border-blue-600 focus:bg-white"
            :value="projectName"
            @input="onProjectNameInput"
            aria-label="Project name"
          />
          <span class="text-xs text-zinc-500">{{ saveLabel }}</span>
        </div>
        <p v-else class="text-sm font-semibold text-zinc-900">Product library</p>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <template v-if="isWorkspace">
        <button class="toolbar-button" @click="workspace.createBlankProject">
          <CirclePlus class="h-4 w-4" />
          <span>New</span>
        </button>
        <button class="toolbar-button-primary" :disabled="workspace.saveState === 'saving'" @click="workspace.saveActiveProject">
          <Save class="h-4 w-4" />
          <span>Save</span>
        </button>
        <button class="toolbar-button" disabled>
          <FileDown class="h-4 w-4" />
          <span>Export</span>
        </button>
      </template>
      <template v-else>
        <RouterLink class="toolbar-button" to="/">
          <ArrowLeft class="h-4 w-4" />
          <span>Workspace</span>
        </RouterLink>
      </template>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { ArrowLeft, CirclePlus, FileDown, Save } from "lucide-vue-next";
import { useWorkspaceStore } from "../../stores/workspaceStore";

const route = useRoute();
const workspace = useWorkspaceStore();

const isWorkspace = computed(() => route.name === "workspace");
const sectionLabel = computed(() => (isWorkspace.value ? "Workspace" : "Library"));
const projectName = computed(() => workspace.activeProject?.name ?? "Untitled project");

const saveLabel = computed(() => {
  if (workspace.saveState === "saving") return "Saving";
  if (workspace.saveState === "saved") return workspace.lastSavedAt ? `Saved ${new Date(workspace.lastSavedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Saved";
  if (workspace.saveState === "dirty") return "Unsaved";
  if (workspace.saveState === "error") return "Save failed";
  return "Ready";
});

function onProjectNameInput(event: Event) {
  const target = event.target as HTMLInputElement;
  workspace.setProjectName(target.value);
}
</script>
