<template>
  <header class="flex min-h-16 flex-wrap items-center justify-between gap-3 border-b border-zinc-200 bg-white px-4 py-2 lg:h-16 lg:flex-nowrap lg:py-0">
    <div class="flex min-w-0 items-center gap-4">
      <img :src="logoSrc" class="h-8 w-auto object-contain" alt="Numens Logo" />
      <div v-if="isWorkspace || isPrint" class="min-w-0" :data-tour="isWorkspace ? 'project-settings' : undefined">
        <p class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ sectionLabel }}</p>
        <div class="flex min-w-0 items-center gap-3">
          <input
            v-if="isWorkspace"
            class="field max-w-[12rem] border-transparent bg-transparent px-2 py-1 text-base font-semibold text-zinc-900 focus:border-blue-600 focus:bg-white sm:max-w-[18rem]"
            :value="projectName"
            @input="onProjectNameInput"
            aria-label="Project name"
          />
          <p v-else class="px-2 py-1 text-base font-semibold text-zinc-900">{{ projectName }}</p>
        </div>
      </div>
    </div>

    <div class="flex min-w-0 flex-wrap items-center gap-2" :data-tour="isPrint ? 'print-actions' : undefined">
      <button class="toolbar-button" @click="onboarding.startReplay(currentTourScope)">
        <CircleHelp class="h-4 w-4" />
        <span>Help</span>
      </button>
      <button class="toolbar-button" :aria-label="themeToggleLabel" @click="theme.toggleTheme">
        <Sun v-if="theme.theme === 'dark'" class="h-4 w-4" />
        <Moon v-else class="h-4 w-4" />
        <span>{{ theme.theme === "dark" ? "Light" : "Dark" }}</span>
      </button>
      <template v-if="isWorkspace">
        <div class="flex min-w-0 flex-wrap items-center gap-2" data-tour="project-actions">
          <button class="toolbar-button" @click="workspace.createBlankProject">
            <CirclePlus class="h-4 w-4" />
            <span>New</span>
          </button>
          <button class="toolbar-button-primary" :disabled="workspace.saveState === 'saving'" @click="workspace.saveActiveProject">
            <Save class="h-4 w-4" />
            <span>Save</span>
          </button>
          <button class="toolbar-button" @click="workspace.exportActiveProject">
            <FileDown class="h-4 w-4" />
            <span>Export</span>
          </button>
          <button class="toolbar-button" @click="triggerImport">
            <FileUp class="h-4 w-4" />
            <span>Import</span>
          </button>
          <input
            ref="importInput"
            type="file"
            accept=".json"
            class="hidden"
            @change="handleImportFile"
          />
        </div>
      </template>
      <template v-else>
        <RouterLink class="toolbar-button" to="/">
          <ArrowLeft class="h-4 w-4" />
          <span>Loop Designer</span>
        </RouterLink>
      </template>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { ArrowLeft, CircleHelp, CirclePlus, FileDown, FileUp, Moon, Save, Sun } from "lucide-vue-next";
import { useOnboardingStore } from "../../stores/onboardingStore";
import { useThemeStore } from "../../stores/themeStore";
import { useWorkspaceStore } from "../../stores/workspaceStore";

const route = useRoute();
const workspace = useWorkspaceStore();
const theme = useThemeStore();
const onboarding = useOnboardingStore();
const importInput = ref<HTMLInputElement | null>(null);

const isWorkspace = computed(() => route.name === "workspace");
const isPrint = computed(() => route.name === "print");
const currentTourScope = computed(() => isPrint.value ? "print" : "workspace");
const sectionLabel = computed(() => {
  if (isWorkspace.value) return "Loop Designer";
  if (isPrint.value) return "Project Print";
  return "Device Catalog";
});
const projectName = computed(() => workspace.activeProject?.name ?? "Untitled project");
const themeToggleLabel = computed(() => theme.theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
const logoSrc = computed(() => theme.theme === "dark" ? "/logo-long.png" : "/logo-long-black.png");

const saveLabel = computed(() => {
  if (workspace.saveState === "saving") return "Auto-saving...";
  if (workspace.saveState === "saved") return workspace.lastSavedAt ? `Saved ${new Date(workspace.lastSavedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Saved";
  if (workspace.saveState === "dirty") return "Unsaved";
  if (workspace.saveState === "error") return "Save failed";
  return "Ready";
});

function onProjectNameInput(event: Event) {
  const target = event.target as HTMLInputElement;
  workspace.setProjectName(target.value);
}

function triggerImport() {
  importInput.value?.click();
}

function handleImportFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) {
    void workspace.importProject(file);
  }
  // Reset so user can re-import the same file
  input.value = "";
}
</script>
