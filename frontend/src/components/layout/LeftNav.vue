<template>
  <aside class="flex h-full min-h-0 flex-col border-r border-zinc-200 bg-white">
    <div class="border-b border-zinc-200 px-3 py-3">
      <RouterLink class="nav-link mb-1" :class="{ 'nav-link-active': isWorkspace }" to="/">
        <Layers3 class="h-4 w-4" />
        <span>Loop Designer</span>
      </RouterLink>
      <RouterLink class="nav-link" :class="{ 'nav-link-active': isProducts }" to="/products">
        <LibraryBig class="h-4 w-4" />
        <span>Device Catalog</span>
      </RouterLink>
      <RouterLink v-if="workspace.activeProject" class="nav-link" :class="{ 'nav-link-active': isPrint }" to="/print">
        <Printer class="h-4 w-4" />
        <span>Print</span>
      </RouterLink>
      <button v-else class="nav-link w-full cursor-not-allowed text-zinc-400" disabled>
        <Printer class="h-4 w-4" />
        <span>Print</span>
      </button>
    </div>

    <div class="min-h-0 flex-1 overflow-auto">
      <div class="panel-title">Projects</div>
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
                Unsaved
              </span>
            </div>
            <p class="text-xs text-zinc-500">{{ project.loop_count }} {{ project.loop_count === 1 ? "loop" : "loops" }}</p>
          </div>
          
          <div class="flex items-center gap-1.5 ml-2">
            <button
              class="p-1.5 text-zinc-400 hover:text-blue-600 hover:bg-white rounded-none transition"
              title="Rename project"
              @click.stop="handleRename(project)"
            >
              <Pencil class="h-3.5 w-3.5" />
            </button>
            <button
              class="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-white rounded-none transition"
              title="Delete project"
              @click.stop="handleDelete(project)"
            >
              <Trash2 class="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { Layers3, LibraryBig, Pencil, Printer, Trash2 } from "lucide-vue-next";
import { useDialogStore } from "../../stores/dialogStore";
import { useWorkspaceStore } from "../../stores/workspaceStore";
import type { ProjectListItem } from "../../types/project";

const route = useRoute();
const dialog = useDialogStore();
const workspace = useWorkspaceStore();

const isWorkspace = computed(() => route.name === "workspace");
const isProducts = computed(() => route.name === "products");
const isPrint = computed(() => route.name === "print");

async function handleRename(project: ProjectListItem) {
  if (workspace.activeProjectId !== project.id && !(await workspace.canLeaveActiveProject())) {
    return;
  }

  const newName = await dialog.prompt({
    title: "Rename project",
    message: "Enter new project name:",
    initialValue: project.name,
    confirmLabel: "Rename"
  });
  if (newName !== null && newName.trim() !== "") {
    const trimmed = newName.trim();
    const isDuplicate = workspace.projects.some(
      (p) => p.id !== project.id && p.name.toLowerCase() === trimmed.toLowerCase()
    );
    if (isDuplicate) {
      await dialog.alert({
        title: "Duplicate project name",
        message: "A project with this name already exists. Please choose a different name."
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
    title: "Delete project",
    message: `Are you sure you want to delete project "${project.name}"?`,
    confirmLabel: "Delete"
  });
  if (confirmed) {
    void workspace.removeProject(project.id);
  }
}

onMounted(() => {
  void workspace.bootstrap();
});
</script>
