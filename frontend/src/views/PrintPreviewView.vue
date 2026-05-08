<template>
  <section class="h-full min-h-0 overflow-hidden bg-zinc-100 print:h-auto print:overflow-visible print:bg-white">
    <div class="flex h-full min-h-0 flex-col print:block print:h-auto print:overflow-visible">
      <div class="flex items-center justify-between border-b border-zinc-200 bg-white px-4 py-3 print:hidden">
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Print Preview</p>
          <h1 class="mt-1 text-lg font-semibold text-zinc-900">{{ workspace.activeProject?.name ?? "No active project" }}</h1>
          <p v-if="workspace.hasUnsavedChanges" class="mt-1 text-xs text-amber-700">Printing current unsaved working state.</p>
        </div>
        <div class="flex items-center gap-2">
          <RouterLink class="toolbar-button" to="/">
            <ArrowLeft class="h-4 w-4" />
            <span>Back to Workspace</span>
          </RouterLink>
          <button class="toolbar-button-primary" @click="print.printNow">
            <Printer class="h-4 w-4" />
            <span>Print</span>
          </button>
        </div>
      </div>

      <div v-if="workspace.activeProject && print.draftProfile" class="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[20rem_minmax(0,1fr)] print:block print:overflow-visible">
        <div class="min-h-0 overflow-auto border-r border-zinc-200 bg-white p-4 print:hidden">
          <PrintProfilePanel v-if="print.editingProfile" :profile="print.editingProfile" @update="print.updateEditingProfile" />
        </div>
        <div class="print-preview-pane min-h-0 overflow-auto p-6 print:overflow-visible print:p-0">
          <PrintPageStack :project="workspace.activeProject" :profile="print.draftProfile" />
        </div>
      </div>

      <div v-else class="flex flex-1 items-center justify-center p-8 text-sm text-zinc-500">
        No active project is available for printing.
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, watch } from "vue";
import { RouterLink } from "vue-router";
import { ArrowLeft, Printer } from "lucide-vue-next";
import PrintPageStack from "../components/print/PrintPageStack.vue";
import PrintProfilePanel from "../components/print/PrintProfilePanel.vue";
import { usePrintStore } from "../stores/printStore";
import { useWorkspaceStore } from "../stores/workspaceStore";

const workspace = useWorkspaceStore();
const print = usePrintStore();

function initPrintForCurrentProject() {
  const projectValue = workspace.activeProject;
  print.initializeFromProject(projectValue);
  print.refreshCalculationReady(projectValue);
}

onMounted(() => {
  initPrintForCurrentProject();
});

// Re-initialize when the user switches projects via the sidebar while staying on /print
watch(
  () => workspace.activeProjectId,
  () => {
    initPrintForCurrentProject();
  }
);
</script>
