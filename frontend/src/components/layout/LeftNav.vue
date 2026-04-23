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
        <button
          v-for="project in workspace.projects"
          :key="project.id"
          class="flex w-full items-center justify-between px-3 py-3 text-left transition hover:bg-zinc-50"
          :class="{ 'bg-blue-50': project.id === workspace.activeProjectId }"
          @click="workspace.selectProject(project.id)"
        >
          <div class="min-w-0">
            <p class="truncate text-sm font-medium text-zinc-900">{{ project.name }}</p>
            <p class="text-xs text-zinc-500">{{ project.loop_count }} {{ project.loop_count === 1 ? "loop" : "loops" }}</p>
          </div>
          <span class="text-[11px] uppercase tracking-wide text-zinc-400">Open</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { Layers3, LibraryBig, Settings2 } from "lucide-vue-next";
import { useWorkspaceStore } from "../../stores/workspaceStore";

const route = useRoute();
const workspace = useWorkspaceStore();

const isWorkspace = computed(() => route.name === "workspace");
const isProducts = computed(() => route.name === "products");

onMounted(() => {
  void workspace.bootstrap();
});
</script>
