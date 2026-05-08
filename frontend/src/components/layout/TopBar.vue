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
            :aria-label="t('topBar.projectName')"
          />
          <p v-else class="px-2 py-1 text-base font-semibold text-zinc-900">{{ projectName }}</p>
        </div>
      </div>
    </div>

    <div class="flex min-w-0 flex-wrap items-center gap-2" :data-tour="isPrint ? 'print-actions' : undefined">
      <button class="toolbar-button" @click="onboarding.startReplay(currentTourScope)">
        <CircleHelp class="h-4 w-4" />
        <span>{{ t("topBar.help") }}</span>
      </button>
      <div ref="languageMenuRef" class="relative">
        <button
          type="button"
          data-testid="language-menu-trigger"
          class="toolbar-button h-full min-h-[38px] gap-1.5"
          :aria-label="t('topBar.language')"
          :aria-expanded="isLanguageMenuOpen"
          aria-haspopup="true"
          @click="toggleLanguageMenu"
          @keydown.escape.stop.prevent="closeLanguageMenu"
        >
          <span>{{ t("topBar.language") }}</span>
          <span class="text-sm font-semibold uppercase text-zinc-800">{{ selectedLocale.toUpperCase() }}</span>
          <ChevronDown class="h-3.5 w-3.5 text-zinc-400 transition-transform" :class="{ 'rotate-180': isLanguageMenuOpen }" />
        </button>
        <div
          v-if="isLanguageMenuOpen"
          data-testid="language-menu"
          class="absolute right-0 top-full z-40 mt-1 w-36 overflow-hidden border border-zinc-200 bg-white shadow-lg"
          @keydown.escape.stop.prevent="closeLanguageMenu"
        >
          <button
            v-for="locale in SUPPORTED_LOCALES"
            :key="locale.code"
            type="button"
            class="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide transition hover:bg-zinc-50 focus-visible:bg-blue-50 focus-visible:outline-none"
            :class="locale.code === selectedLocale ? 'bg-blue-50 text-blue-700' : 'text-zinc-700'"
            @click="selectLocale(locale.code)"
          >
            <span>{{ locale.code.toUpperCase() }}</span>
            <span class="truncate text-[11px] font-medium normal-case tracking-normal text-zinc-400">{{ locale.nativeLabel }}</span>
          </button>
        </div>
      </div>
      <button class="toolbar-button" :aria-label="themeToggleLabel" @click="theme.toggleTheme">
        <Sun v-if="theme.theme === 'dark'" class="h-4 w-4" />
        <Moon v-else class="h-4 w-4" />
        <span>{{ theme.theme === "dark" ? t("topBar.light") : t("topBar.dark") }}</span>
      </button>
      <template v-if="isWorkspace">
        <div class="flex min-w-0 flex-wrap items-center gap-2" data-tour="project-actions">
          <button class="toolbar-button" @click="workspace.createBlankProject">
            <CirclePlus class="h-4 w-4" />
            <span>{{ t("topBar.new") }}</span>
          </button>
          <button class="toolbar-button-primary" :disabled="workspace.saveState === 'saving'" @click="workspace.saveActiveProject">
            <Save class="h-4 w-4" />
            <span>{{ t("topBar.save") }}</span>
          </button>
          <button class="toolbar-button" @click="workspace.exportActiveProject">
            <FileDown class="h-4 w-4" />
            <span>{{ t("topBar.export") }}</span>
          </button>
          <button class="toolbar-button" @click="triggerImport">
            <FileUp class="h-4 w-4" />
            <span>{{ t("topBar.import") }}</span>
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
          <span>{{ t("topBar.loopDesigner") }}</span>
        </RouterLink>
      </template>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { ArrowLeft, ChevronDown, CircleHelp, CirclePlus, FileDown, FileUp, Moon, Save, Sun } from "lucide-vue-next";
import { SUPPORTED_LOCALES, setLocale, useTranslation, type LocaleCode } from "../../i18n";
import { useOnboardingStore } from "../../stores/onboardingStore";
import { useThemeStore } from "../../stores/themeStore";
import { useWorkspaceStore } from "../../stores/workspaceStore";

const route = useRoute();
const workspace = useWorkspaceStore();
const theme = useThemeStore();
const onboarding = useOnboardingStore();
const importInput = ref<HTMLInputElement | null>(null);
const languageMenuRef = ref<HTMLElement | null>(null);
const isLanguageMenuOpen = ref(false);
const { selectedLocale, t } = useTranslation();

const isWorkspace = computed(() => route.name === "workspace");
const isPrint = computed(() => route.name === "print");
const currentTourScope = computed(() => isPrint.value ? "print" : "workspace");
const sectionLabel = computed(() => {
  if (isWorkspace.value) return t("topBar.loopDesigner");
  if (isPrint.value) return t("topBar.projectPrint");
  return t("topBar.deviceCatalog");
});
const projectName = computed(() => workspace.activeProject?.name ?? t("topBar.untitledProject"));
const themeToggleLabel = computed(() => theme.theme === "dark" ? t("topBar.switchLight") : t("topBar.switchDark"));
const logoSrc = computed(() => theme.theme === "dark" ? "/logo-long.png" : "/logo-long-black.png");

const saveLabel = computed(() => {
  if (workspace.saveState === "saving") return t("topBar.saving");
  if (workspace.saveState === "saved") return workspace.lastSavedAt ? `${t("topBar.saved")} ${new Date(workspace.lastSavedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : t("topBar.saved");
  if (workspace.saveState === "dirty") return t("common.unsaved");
  if (workspace.saveState === "error") return t("topBar.saveFailed");
  return t("common.ready");
});

function onProjectNameInput(event: Event) {
  const target = event.target as HTMLInputElement;
  workspace.setProjectName(target.value);
}

function triggerImport() {
  importInput.value?.click();
}

function toggleLanguageMenu() {
  isLanguageMenuOpen.value = !isLanguageMenuOpen.value;
}

function closeLanguageMenu() {
  isLanguageMenuOpen.value = false;
}

function selectLocale(locale: LocaleCode) {
  setLocale(locale);
  closeLanguageMenu();
}

function onDocumentMouseDown(event: MouseEvent) {
  const target = event.target;
  if (!(target instanceof Node)) return;
  if (languageMenuRef.value && !languageMenuRef.value.contains(target)) {
    closeLanguageMenu();
  }
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

onMounted(() => {
  document.addEventListener("mousedown", onDocumentMouseDown);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocumentMouseDown);
});
</script>
