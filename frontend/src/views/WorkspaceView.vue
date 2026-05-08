<template>
  <div class="grid h-full min-h-0 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_22rem]">
    <section class="min-h-0 overflow-visible px-4 py-4 lg:overflow-hidden">
      <div class="flex h-full min-h-0 flex-col gap-4">
        <LoopTabs
          v-if="workspace.activeProject"
          :loops="workspace.activeProject.loops"
          :active-loop-id="workspace.activeLoopId"
          :can-add="workspace.canAddLoop"
          @select="workspace.setActiveLoop"
          @add="workspace.addLoop"
        />
        <SystemParameters
          v-if="workspace.activeLoop"
          :loop="workspace.activeLoop"
          :categories="deviceCategories"
          @update="workspace.updateSystemParameters(workspace.activeLoopId, $event)"
          @add-category="onAddCategory"
        />
        <DeviceTable
          v-if="workspace.activeLoop"
          class="min-h-[18rem] flex-1"
          :rows="workspace.activeLoop.device_rows"
          :products="productStore.products"
          :categories="deviceCategories"
          @add-category="onAddCategory"
          @remove-row="workspace.removeDeviceRow(workspace.activeLoopId, $event)"
          @update-row="onUpdateRow"
          @select-product="onSelectProduct"
        />
      </div>
    </section>

    <div class="border-t border-zinc-200 bg-zinc-50/60 p-4 lg:border-l lg:border-t-0">
      <div class="h-auto overflow-visible lg:sticky lg:top-20 lg:h-[calc(100vh-6rem)] lg:overflow-auto">
        <CalculationInspector
          :loop="workspace.activeLoop"
          :project="workspace.activeProject"
          :result="workspace.activeLoop?.calculation_result ?? null"
          :busy="Boolean(workspace.activeLoopId && workspace.calculationBusyLoopIds.includes(workspace.activeLoopId))"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import CalculationInspector from "../components/workspace/CalculationInspector.vue";
import DeviceTable from "../components/workspace/DeviceTable.vue";
import LoopTabs from "../components/workspace/LoopTabs.vue";
import SystemParameters from "../components/workspace/SystemParameters.vue";
import { useProductStore } from "../stores/productStore";
import { useWorkspaceStore } from "../stores/workspaceStore";
import type { ProductRecord } from "../types/product";

const workspace = useWorkspaceStore();
const productStore = useProductStore();

const deviceCategories = computed(() => {
  const priority = ["Detector", "Sounder", "MCP", "I/O Module", "Isolator"];
  const seen = new Set<string>();
  const categories = productStore.products
    .map((product) => product.category)
    .filter((category) => {
      if (seen.has(category)) {
        return false;
      }
      seen.add(category);
      return true;
    });

  return categories.sort((a, b) => {
    const indexA = priority.indexOf(a);
    const indexB = priority.indexOf(b);
    if (indexA === -1 && indexB === -1) return a.localeCompare(b);
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });
});

onMounted(() => {
  void productStore.bootstrap();
  workspace.ensureInitialCalculation();
});

function onUpdateRow(rowId: string, patch: Parameters<typeof workspace.updateDeviceRow>[2]) {
  workspace.updateDeviceRow(workspace.activeLoopId, rowId, patch);
}

function onSelectProduct(rowId: string, productId: string) {
  const product = productStore.getProduct(productId);
  if (!workspace.activeLoop) {
    return;
  }
  workspace.assignProductToRow(workspace.activeLoopId, rowId, product as ProductRecord | null);
}

function onAddCategory(category: string) {
  workspace.addDeviceRowForCategory(workspace.activeLoopId, category, productStore.products);
}
</script>
