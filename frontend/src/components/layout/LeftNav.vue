<template>
  <aside class="flex h-full min-h-0 flex-col border-r border-zinc-200 bg-white">
    <div class="border-b border-zinc-200 px-3 py-3">
      <RouterLink class="nav-link mb-1" :class="{ 'nav-link-active': isWorkspace }" to="/">
        <Layers3 class="h-4 w-4" />
        <span>{{ t("nav.loopDesigner") }}</span>
      </RouterLink>
      <RouterLink class="nav-link" :class="{ 'nav-link-active': isProducts }" to="/products">
        <LibraryBig class="h-4 w-4" />
        <span>{{ t("nav.deviceCatalog") }}</span>
      </RouterLink>
      <RouterLink v-if="workspace.activeProject" class="nav-link" :class="{ 'nav-link-active': isPrint }" to="/print">
        <Printer class="h-4 w-4" />
        <span>{{ t("common.print") }}</span>
      </RouterLink>
      <button v-else class="nav-link w-full cursor-not-allowed text-zinc-400" disabled>
        <Printer class="h-4 w-4" />
        <span>{{ t("common.print") }}</span>
      </button>
    </div>

    <div class="min-h-0 flex-1 overflow-auto">
      <div data-tour="project-list">
        <div class="panel-title">{{ t("nav.projects") }}</div>
        <div class="divide-y divide-zinc-200">
          <div
            v-for="project in workspace.projects"
            :key="project.id"
            class="flex items-center justify-between px-3 py-2.5 transition"
            :class="{ 'bg-blue-50': project.id === workspace.activeProjectId }"
          >
            <div class="min-w-0 flex-1 cursor-pointer" @click="workspace.selectProject(project.id)">
              <div class="flex min-w-0 items-center gap-2">
                <p class="truncate text-sm font-medium" :class="project.id === workspace.activeProjectId ? 'text-blue-700 font-semibold' : 'text-zinc-900'">{{ project.name }}</p>
                <span
                  v-if="workspace.isProjectUnsaved(project.id)"
                  class="shrink-0 border border-amber-300 bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase leading-none text-amber-700"
                >
                  {{ t("common.unsaved") }}
                </span>
              </div>
              <p class="text-xs text-zinc-500">{{ project.loop_count }} {{ project.loop_count === 1 ? t("common.loop") : t("common.loops") }}</p>
            </div>
            
            <div class="flex items-center gap-1.5 ml-2">
              <button
                class="p-1.5 text-zinc-400 hover:text-blue-600 hover:bg-white rounded-none transition"
                :title="t('dialogs.renameProject')"
                @click.stop="handleRename(project)"
              >
                <Pencil class="h-3.5 w-3.5" />
              </button>
              <button
                class="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-white rounded-none transition"
                :title="t('dialogs.deleteProjectTitle')"
                @click.stop="handleDelete(project)"
              >
                <Trash2 class="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="shrink-0 border-t border-zinc-200 px-3 py-2">
      <p class="text-[11px] text-zinc-400">v{{ appVersion }}</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { Layers3, LibraryBig, Pencil, Printer, Trash2 } from "lucide-vue-next";
import { translateMessage as t } from "../../i18n";
import { useDialogStore } from "../../stores/dialogStore";
import { useWorkspaceStore } from "../../stores/workspaceStore";
import { APP_VERSION } from "../../config/version";
import type { ProjectListItem } from "../../types/project";

const route = useRoute();
const dialog = useDialogStore();
const workspace = useWorkspaceStore();
const appVersion = APP_VERSION;

const isWorkspace = computed(() => route.name === "workspace");
const isProducts = computed(() => route.name === "products");
const isPrint = computed(() => route.name === "print");

async function handleRename(project: ProjectListItem) {
  if (workspace.activeProjectId !== project.id && !(await workspace.canLeaveActiveProject())) {
    return;
  }

    const newName = await dialog.prompt({
    title: t("dialogs.renameProjectTitle"),
    message: t("dialogs.enterProjectName"),
    initialValue: project.name,
    confirmLabel: t("common.rename")
  });
  if (newName !== null && newName.trim() !== "") {
    const trimmed = newName.trim();
    const isDuplicate = workspace.projects.some(
      (p) => p.id !== project.id && p.name.toLowerCase() === trimmed.toLowerCase()
    );
    if (isDuplicate) {
      await dialog.alert({
        title: t("dialogs.duplicateProjectTitle"),
        message: t("dialogs.duplicateProjectMessage")
      });
      return;
    }
    await workspace.openProject(project.id);
    workspace.setProjectName(trimmed);
    void workspace.saveActiveProject();
  }
}

async function handleDelete(project: ProjectListItem) {
  const confirmed = await dialog.confirm({
    title: t("dialogs.deleteProjectTitle"),
    message: t("dialogs.deleteProjectMessage", { name: project.name }),
    confirmLabel: t("common.delete")
  });
  if (confirmed) {
    void workspace.removeProject(project.id);
  }
}

onMounted(() => {
  void workspace.bootstrap();
});
</script>
