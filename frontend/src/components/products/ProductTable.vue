<template>
  <div class="panel">
    <div class="overflow-auto">
      <table class="w-full border-collapse">
        <thead class="sticky top-0 z-10">
          <tr>
            <th class="table-head w-[8%] min-w-[80px] px-2 py-2">{{ t("products.source") }}</th>
            <th class="table-head w-[12%] min-w-[100px] px-2 py-2">{{ t("common.category") }}</th>
            <th class="table-head w-[36%] min-w-[200px] px-2 py-2">{{ t("products.product") }}</th>
            <th class="table-head w-[16%] min-w-[140px] px-2 py-2">{{ t("products.factory") }}</th>
            <th class="table-head w-[8%] min-w-[70px] px-2 py-2 text-right">{{ t("common.standby") }}</th>
            <th class="table-head w-[8%] min-w-[70px] px-2 py-2 text-right">{{ t("common.alarm") }}</th>
            <th class="table-head w-[12%] min-w-[100px] px-2 py-2 text-right">{{ t("common.actions") }}</th>
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
                  {{ translateCurrentCategoryLabel(category as string) }}
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
                  {{ product.built_in ? t("products.builtIn") : t("products.custom") }}
                </span>
              </td>
              <td class="table-cell">
                <input
                  v-if="isAdmin || !product.built_in"
                  class="field px-2 py-1 text-sm w-full"
                  :value="product.category"
                  @change="updateField(product, 'category', $event)"
                />
                <span v-else>{{ translateCurrentCategoryLabel(product.category) }}</span>
              </td>
              <td class="table-cell">
                <input
                  v-if="isAdmin || !product.built_in"
                  class="field px-2 py-1 text-sm w-full"
                  :value="product.product_name"
                  @change="updateField(product, 'product_name', $event)"
                />
                <span v-else class="text-left font-medium text-zinc-900">{{ translateCurrentProductNameLabel(product.product_name) }}</span>
              </td>
              <td class="table-cell">
                <input
                  v-if="isAdmin || !product.built_in"
                  class="field px-2 py-1 text-sm w-full"
                  :value="product.factory_name"
                  @change="updateField(product, 'factory_name', $event)"
                />
                <span v-else>{{ product.factory_name }}</span>
              </td>
              <td class="table-cell text-right tabular-nums">
                <input
                  v-if="isAdmin || !product.built_in"
                  type="number"
                  step="0.01"
                  class="field-number px-2 py-1 text-sm w-24 text-right"
                  :value="product.standby"
                  @change="updateNumberField(product, 'standby', $event)"
                />
                <span v-else>{{ product.standby.toFixed(2) }}</span>
              </td>
              <td class="table-cell text-right tabular-nums">
                <input
                  v-if="isAdmin || !product.built_in"
                  type="number"
                  step="0.01"
                  class="field-number px-2 py-1 text-sm w-24 text-right"
                  :value="product.alarm"
                  @change="updateNumberField(product, 'alarm', $event)"
                />
                <span v-else>{{ product.alarm.toFixed(2) }}</span>
              </td>
              <td class="table-cell text-right">
                <button
                  class="toolbar-button-ghost px-2 py-1 text-red-600 disabled:text-zinc-300"
                  :disabled="product.built_in && !isAdmin"
                  @click="$emit('delete', product)"
                >
                  <Trash2 class="h-4 w-4" />
                  <span>{{ t("common.delete") }}</span>
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
import { translateCurrentCategoryLabel, translateCurrentProductNameLabel, translateMessage as t } from "../../i18n";
import type { ProductRecord } from "../../types/product";

const props = defineProps<{
  products: ProductRecord[];
  isAdmin: boolean;
}>();

const emit = defineEmits<{
  save: [product: ProductRecord];
  delete: [product: ProductRecord];
}>();

function updateField(product: ProductRecord, field: string, event: Event) {
  const value = (event.target as HTMLInputElement).value;
  const updatedProduct = { ...product, [field]: value };
  emit("save", updatedProduct);
}

function updateNumberField(product: ProductRecord, field: string, event: Event) {
  const value = Number((event.target as HTMLInputElement).value);
  const updatedProduct = { ...product, [field]: Number.isFinite(value) ? value : 0 };
  emit("save", updatedProduct);
}

const groupedProducts = computed(() => {
  const groups: Record<string, ProductRecord[]> = {};
  for (const product of props.products) {
    const cat = product.category || "-";
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
