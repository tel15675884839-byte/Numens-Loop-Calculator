<template>
  <div class="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_22rem]">
    <section class="min-h-0 overflow-hidden px-4 py-4">
      <div class="flex h-full min-h-0 flex-col gap-4">
        <LoopTabs
          v-if="workspace.activeProject"
          :loops="workspace.activeProject.loops"
          :active-loop-id="workspace.activeLoopId"
          @select="workspace.setActiveLoop"
          @add="workspace.addLoop"
        />
        <SystemParameters
          v-if="workspace.activeLoop"
          :loop="workspace.activeLoop"
          @update="workspace.updateSystemParameters(workspace.activeLoopId, $event)"
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

    <div class="border-l border-zinc-200 bg-zinc-50/60 p-4">
      <div class="sticky top-20 h-[calc(100vh-6rem)] overflow-auto">
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
  const seen = new Set<string>();
  return productStore.products
    .map((product) => product.category)
    .filter((category) => {
      if (seen.has(category)) {
        return false;
      }
      seen.add(category);
      return true;
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
