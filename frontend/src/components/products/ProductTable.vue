<template>
  <div class="panel">
    <div class="overflow-auto">
      <table class="w-full border-collapse">
        <thead class="sticky top-0 z-10">
          <tr>
            <th class="table-head w-[8%] min-w-[80px] px-2 py-2">Source</th>
            <th class="table-head w-[12%] min-w-[100px] px-2 py-2">Category</th>
            <th class="table-head w-[36%] min-w-[200px] px-2 py-2">Product</th>
            <th class="table-head w-[16%] min-w-[140px] px-2 py-2">Factory</th>
            <th class="table-head w-[8%] min-w-[70px] px-2 py-2 text-right">Standby</th>
            <th class="table-head w-[8%] min-w-[70px] px-2 py-2 text-right">Alarm</th>
            <th class="table-head w-[12%] min-w-[100px] px-2 py-2 text-right">Actions</th>
          </tr>
        </thead>
        <template v-for="(groupProducts, category) in groupedProducts" :key="category">
          <!-- Group Header Row -->
          <tbody>
            <tr class="bg-zinc-50 font-bold text-zinc-700">
              <td colspan="7" class="px-4 py-3 border-b border-zinc-200">
                <button
                  class="flex items-center gap-2 w-full text-left font-bold uppercase tracking-wider text-zinc-600 hover:text-blue-600 text-xs"
                  @click="toggleSection(category as string)"
                >
                  <ChevronDown
                    class="h-4 w-4 transition-transform"
                    :class="{ '-rotate-90': collapsedSections[category as string] }"
                  />
                  {{ category }}
                  <span class="ml-1 rounded-full bg-zinc-200/60 px-2 py-0.5 text-[10px] font-normal normal-case text-zinc-500">
                    {{ groupProducts.length }}
                  </span>
                </button>
              </td>
            </tr>
          </tbody>
          <!-- Group Data Rows -->
          <tbody v-show="!collapsedSections[category as string]">
            <tr v-for="product in groupProducts" :key="product.id">
              <td class="table-cell">
                <span class="inline-flex border px-2 py-1 text-[11px] font-semibold uppercase tracking-wide" :class="product.built_in ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-zinc-200 bg-zinc-50 text-zinc-600'">
                  {{ product.built_in ? "Built-in" : "Custom" }}
                </span>
              </td>
              <td class="table-cell">{{ product.category }}</td>
              <td class="table-cell">
                <button class="text-left font-medium text-zinc-900 hover:text-blue-700" @click="$emit('edit', product)">{{ product.product_name }}</button>
              </td>
              <td class="table-cell">{{ product.factory_name }}</td>
              <td class="table-cell text-right tabular-nums">{{ product.standby.toFixed(2) }}</td>
              <td class="table-cell text-right tabular-nums">{{ product.alarm.toFixed(2) }}</td>
              <td class="table-cell text-right">
                <button class="toolbar-button-ghost px-2 py-1 text-red-600 disabled:text-zinc-300" :disabled="product.built_in" @click="$emit('delete', product)">
                  <Trash2 class="h-4 w-4" />
                  <span>Delete</span>
                </button>
              </td>
            </tr>
          </tbody>
        </template>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { ChevronDown, Trash2 } from "lucide-vue-next";
import type { ProductRecord } from "../../types/product";

const props = defineProps<{
  products: ProductRecord[];
}>();

defineEmits<{
  edit: [product: ProductRecord];
  delete: [product: ProductRecord];
}>();

const groupedProducts = computed(() => {
  const groups: Record<string, ProductRecord[]> = {};
  for (const product of props.products) {
    const cat = product.category || "Unknown";
    if (!groups[cat]) {
      groups[cat] = [];
    }
    groups[cat].push(product);
  }
  return groups;
});

const collapsedSections = ref<Record<string, boolean>>({});

function toggleSection(category: string) {
  collapsedSections.value[category] = !collapsedSections.value[category];
}
</script>
