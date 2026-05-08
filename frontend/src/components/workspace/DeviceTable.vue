<template>
  <div class="panel flex min-h-0 flex-col">
    <div class="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold uppercase tracking-wide text-zinc-500">{{ t("deviceTable.deviceList") }}</span>
        <span class="text-xs text-zinc-400">({{ rows.length }} {{ rows.length === 1 ? t('common.device') : t('common.devices') }})</span>
      </div>
    </div>

    <div data-testid="device-table-scroll" class="min-h-0 flex-1 overflow-auto">
      <table class="min-w-[58rem] w-full border-collapse">
        <thead class="sticky top-0 z-10">
          <tr>
            <th class="table-head w-12 px-2 py-2">#</th>
            <th class="table-head px-2 py-2">{{ t("deviceTable.category") }}</th>
            <th class="table-head px-2 py-2">{{ t("deviceTable.device") }}</th>
            <th class="table-head w-[105px] px-2 py-2" :title="t('deviceTable.leadTitle')">
              <div class="flex items-center justify-end gap-1 cursor-help">
                <span class="whitespace-nowrap">{{ t("deviceTable.lead") }}</span>
                <HelpCircle class="h-3.5 w-3.5 text-zinc-400" />
              </div>
            </th>
            <th class="table-head w-[105px] px-2 py-2" :title="t('deviceTable.intervalTitle')">
              <div class="flex items-center justify-end gap-1 cursor-help">
                <span class="whitespace-nowrap">{{ t("deviceTable.interval") }}</span>
                <HelpCircle class="h-3.5 w-3.5 text-zinc-400" />
              </div>
            </th>
            <th class="table-head w-20 px-2 py-2 text-right">{{ t("common.qty") }}</th>
            <th class="table-head w-24 px-2 py-2 text-right">{{ t("deviceTable.alarm") }}</th>
            <th class="table-head w-20 px-2 py-2 text-center">{{ t("common.actions") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <td class="table-cell !py-3 text-center text-xs text-zinc-500">{{ row.sort_order }}</td>
            <td class="table-cell !py-3">
              <input class="field cursor-not-allowed bg-zinc-50 text-zinc-400" disabled :value="translateCurrentCategoryLabel(row.category)" />
            </td>
            <td class="table-cell !py-3">
              <select class="field" :value="row.product_id ?? ''" @change="onProductSelect(row.id, inputValue($event))">
                <option v-for="product in productOptionsForRow(row)" :key="product.id" :value="product.id">
                  {{ translateCurrentCategoryLabel(product.category) }} - {{ product.customer_name }} - {{ product.product_name }}
                </option>
              </select>
            </td>
            <td class="table-cell !py-3">
              <div class="relative" data-testid="lead-field">
                <input class="field-number pr-8" :value="row.lead_dist_m" @focus="selectInputText" @mousedown.prevent="focusAndSelectInputText" @mouseup.prevent="focusAndSelectInputText" @click="focusAndSelectInputText" @input="updateNumber(row.id, 'lead_dist_m', inputValue($event))" />
                <span class="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs text-zinc-400">m</span>
              </div>
            </td>
            <td class="table-cell !py-3">
              <div class="relative" data-testid="interval-field">
                <input 
                  class="field-number pr-8" 
                  :disabled="row.qty <= 1"
                  :class="{ 'cursor-not-allowed bg-zinc-50 text-zinc-400': row.qty <= 1 }"
                  :value="row.qty <= 1 ? 0 : row.interval_dist_m" 
                  @focus="selectInputText"
                  @mousedown.prevent="focusAndSelectInputText"
                  @mouseup.prevent="focusAndSelectInputText"
                  @click="focusAndSelectInputText"
                  @input="updateNumber(row.id, 'interval_dist_m', inputValue($event))" 
                />
                <span class="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs text-zinc-400">m</span>
              </div>
            </td>
            <td class="table-cell !py-3">
              <input class="field-number" type="text" inputmode="numeric" pattern="[0-9]*" :value="row.qty" @focus="selectInputText" @mousedown.prevent="focusAndSelectInputText" @mouseup.prevent="focusAndSelectInputText" @click="focusAndSelectInputText" @input="updateInteger(row.id, 'qty', inputValue($event))" />
            </td>
            <td class="table-cell !py-3">
              <div class="relative" data-testid="alarm-field">
                <input class="field-number cursor-not-allowed bg-zinc-50 pr-10 text-zinc-400" disabled :value="row.alarm_ma" />
                <span class="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs text-zinc-400">mA</span>
              </div>
            </td>
            <td class="table-cell !py-3 text-center">
              <button class="toolbar-button-ghost p-1 text-zinc-500 hover:text-red-600 inline-flex items-center justify-center" @click="$emit('remove-row', row.id)">
                <Trash2 class="h-4 w-4" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Trash2, HelpCircle } from "lucide-vue-next";
import { translateCurrentCategoryLabel, translateMessage as t } from "../../i18n";
import type { LoopDeviceRow } from "../../types/project";
import type { ProductRecord } from "../../types/product";

const props = defineProps<{
  rows: LoopDeviceRow[];
  products: ProductRecord[];
  categories: string[];
}>();

const emit = defineEmits<{
  "add-row": [];
  "add-category": [category: string];
  "remove-row": [rowId: string];
  "update-row": [rowId: string, patch: Partial<LoopDeviceRow>];
  "select-product": [rowId: string, productId: string];
}>();

function inputValue(event: Event) {
  return (event.target as HTMLInputElement | HTMLSelectElement).value;
}

function selectInputText(event: FocusEvent) {
  const input = event.target as HTMLInputElement;
  input.select();
  window.setTimeout(() => input.select(), 0);
}

function focusAndSelectInputText(event: MouseEvent) {
  const input = event.currentTarget as HTMLInputElement;
  input.focus();
  input.select();
  window.setTimeout(() => input.select(), 0);
}

function updateRow(rowId: string, patch: Partial<LoopDeviceRow>) {
  emit("update-row", rowId, patch);
}

function updateNumber(rowId: string, key: keyof LoopDeviceRow, value: string) {
  const numeric = value === "" ? 0 : Number(value);
  emit("update-row", rowId, { [key]: Number.isFinite(numeric) ? numeric : 0 } as Partial<LoopDeviceRow>);
}

function updateInteger(rowId: string, key: keyof LoopDeviceRow, value: string) {
  let numeric = value === "" ? 0 : Math.round(Number(value));
  if (key === 'qty') {
    if (numeric < 1) numeric = 1;
    if (numeric === 1) {
      emit("update-row", rowId, { qty: 1, interval_dist_m: 0 } as Partial<LoopDeviceRow>);
      return;
    }
  }
  emit("update-row", rowId, { [key]: Number.isFinite(numeric) ? numeric : 0 } as Partial<LoopDeviceRow>);
}

function onProductSelect(rowId: string, productId: string) {
  emit("select-product", rowId, productId);
}

function productOptionsForRow(row: LoopDeviceRow) {
  return props.products.filter((product) => product.category === row.category);
}
</script>
