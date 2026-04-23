<template>
  <div class="panel flex min-h-0 flex-col">
    <div class="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Device table</p>
        <p class="text-sm text-zinc-600">{{ rows.length }} rows</p>
      </div>
      <div class="flex flex-wrap justify-end gap-2">
        <button
          v-for="category in categories"
          :key="category"
          class="toolbar-button px-2.5 py-1.5 text-xs"
          @click="$emit('add-category', category)"
        >
          {{ category }}
        </button>
      </div>
    </div>

    <div data-testid="device-table-scroll" class="min-h-0 flex-1 overflow-auto">
      <table class="min-w-[64rem] w-full border-collapse">
        <thead class="sticky top-0 z-10">
          <tr>
            <th class="table-head w-12 px-2 py-2">#</th>
            <th class="table-head px-2 py-2">Category</th>
            <th class="table-head px-2 py-2">Device</th>
            <th class="table-head w-24 px-2 py-2 text-right">Lead m</th>
            <th class="table-head w-24 px-2 py-2 text-right">Interval m</th>
            <th class="table-head w-20 px-2 py-2 text-right">Qty</th>
            <th class="table-head w-24 px-2 py-2 text-right">Standby mA</th>
            <th class="table-head w-24 px-2 py-2 text-right">Alarm mA</th>
            <th class="table-head w-24 px-2 py-2 text-right">LED</th>
            <th class="table-head w-20 px-2 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <td class="table-cell text-center text-xs text-zinc-500">{{ row.sort_order }}</td>
            <td class="table-cell">
              <input class="field" :value="row.category" @input="updateRow(row.id, { category: inputValue($event) })" />
            </td>
            <td class="table-cell">
              <select class="field" :value="row.product_id ?? ''" @change="onProductSelect(row.id, inputValue($event))">
                <option value="">Manual row</option>
                <option v-for="product in productOptionsForRow(row)" :key="product.id" :value="product.id">
                  {{ product.category }} - {{ product.customer_name }} - {{ product.product_name }}
                </option>
              </select>
            </td>
            <td class="table-cell">
              <input class="field-number" :value="row.lead_dist_m" @input="updateNumber(row.id, 'lead_dist_m', inputValue($event))" />
            </td>
            <td class="table-cell">
              <input class="field-number" :value="row.interval_dist_m" @input="updateNumber(row.id, 'interval_dist_m', inputValue($event))" />
            </td>
            <td class="table-cell">
              <input class="field-number" :value="row.qty" @input="updateInteger(row.id, 'qty', inputValue($event))" />
            </td>
            <td class="table-cell">
              <input class="field-number" :value="row.standby_ma" @input="updateNumber(row.id, 'standby_ma', inputValue($event))" />
            </td>
            <td class="table-cell">
              <input class="field-number" :value="row.alarm_ma" @input="updateNumber(row.id, 'alarm_ma', inputValue($event))" />
            </td>
            <td class="table-cell">
              <input class="field-number" :value="row.led_cost" @input="updateInteger(row.id, 'led_cost', inputValue($event))" />
            </td>
            <td class="table-cell">
              <button class="toolbar-button-ghost p-1 text-zinc-500 hover:text-red-600" @click="$emit('remove-row', row.id)">
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
import { Trash2 } from "lucide-vue-next";
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

function updateRow(rowId: string, patch: Partial<LoopDeviceRow>) {
  emit("update-row", rowId, patch);
}

function updateNumber(rowId: string, key: keyof LoopDeviceRow, value: string) {
  const numeric = value === "" ? 0 : Number(value);
  emit("update-row", rowId, { [key]: Number.isFinite(numeric) ? numeric : 0 } as Partial<LoopDeviceRow>);
}

function updateInteger(rowId: string, key: keyof LoopDeviceRow, value: string) {
  const numeric = value === "" ? 0 : Math.round(Number(value));
  emit("update-row", rowId, { [key]: Number.isFinite(numeric) ? numeric : 0 } as Partial<LoopDeviceRow>);
}

function onProductSelect(rowId: string, productId: string) {
  emit("select-product", rowId, productId);
}

function productOptionsForRow(row: LoopDeviceRow) {
  return props.products.filter((product) => product.category === row.category);
}
</script>
