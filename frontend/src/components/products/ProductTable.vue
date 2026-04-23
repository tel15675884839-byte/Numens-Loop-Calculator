<template>
  <div class="panel">
    <div class="overflow-auto">
      <table class="min-w-[68rem] w-full border-collapse">
        <thead>
          <tr>
            <th class="table-head px-2 py-2">Source</th>
            <th class="table-head px-2 py-2">Category</th>
            <th class="table-head px-2 py-2">Product</th>
            <th class="table-head px-2 py-2">Factory</th>
            <th class="table-head px-2 py-2">Customer</th>
            <th class="table-head w-24 px-2 py-2 text-right">Standby</th>
            <th class="table-head w-24 px-2 py-2 text-right">Alarm</th>
            <th class="table-head px-2 py-2">Type</th>
            <th class="table-head w-28 px-2 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in products" :key="product.id">
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
            <td class="table-cell">{{ product.customer_name }}</td>
            <td class="table-cell text-right tabular-nums">{{ product.standby.toFixed(2) }}</td>
            <td class="table-cell text-right tabular-nums">{{ product.alarm.toFixed(2) }}</td>
            <td class="table-cell">{{ product.type }}</td>
            <td class="table-cell">
              <button class="toolbar-button-ghost px-2 py-1 text-red-600 disabled:text-zinc-300" :disabled="product.built_in" @click="$emit('delete', product)">
                <Trash2 class="h-4 w-4" />
                <span>Delete</span>
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
import type { ProductRecord } from "../../types/product";

defineProps<{
  products: ProductRecord[];
}>();

defineEmits<{
  edit: [product: ProductRecord];
  delete: [product: ProductRecord];
}>();
</script>
