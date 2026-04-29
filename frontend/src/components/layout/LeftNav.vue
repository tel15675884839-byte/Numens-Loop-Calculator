<template>
  <aside class="flex h-full min-h-0 flex-col border-r border-zinc-200 bg-white">
    <div class="border-b border-zinc-200 px-3 py-3">
      <RouterLink class="nav-link mb-1" :class="{ 'nav-link-active': isWorkspace }" to="/">
        <Layers3 class="h-4 w-4" />
        <span>Workspace</span>
      </RouterLink>
      <RouterLink class="nav-link" :class="{ 'nav-link-active': isProducts }" to="/products">
        <LibraryBig class="h-4 w-4" />
        <span>Product library</span>
      </RouterLink>
      <button class="nav-link w-full cursor-not-allowed text-zinc-400" disabled>
        <Settings2 class="h-4 w-4" />
        <span>Settings</span>
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
            <p class="truncate text-sm font-medium" :class="project.id === workspace.activeProjectId ? 'text-blue-700 font-semibold' : 'text-zinc-900'">{{ project.name }}</p>
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
import { Layers3, LibraryBig, Pencil, Settings2, Trash2 } from "lucide-vue-next";
import { useWorkspaceStore } from "../../stores/workspaceStore";

const route = useRoute();
const workspace = useWorkspaceStore();

const isWorkspace = computed(() => route.name === "workspace");
const isProducts = computed(() => route.name === "products");

async function handleRename(project: any) {
  const newName = prompt("Enter new project name:", project.name);
  if (newName !== null && newName.trim() !== "") {
    const trimmed = newName.trim();
    // Check if duplicate
    const isDuplicate = workspace.projects.some(
      (p) => p.id !== project.id && p.name.toLowerCase() === trimmed.toLowerCase()
    );
    if (isDuplicate) {
      alert("A project with this name already exists. Please choose a different name.");
      return;
    }
    await workspace.openProject(project.id);
    workspace.setProjectName(trimmed);
    void workspace.saveActiveProject();
  }
}

function handleDelete(project: any) {
  if (confirm(`Are you sure you want to delete project "${project.name}"?`)) {
    void workspace.removeProject(project.id);
  }
}

onMounted(() => {
  void workspace.bootstrap();
});
</script>
