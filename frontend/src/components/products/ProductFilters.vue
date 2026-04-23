<template>
  <div class="panel">
    <div class="flex items-center justify-between gap-3 border-b border-zinc-200 px-4 py-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Library filters</p>
        <p class="text-sm text-zinc-600">{{ total }} products</p>
      </div>
      <button class="toolbar-button-primary" @click="$emit('create')">
        <CirclePlus class="h-4 w-4" />
        <span>Add product</span>
      </button>
    </div>
    <div class="grid gap-3 px-4 py-4 md:grid-cols-2">
      <label class="flex flex-col gap-1">
        <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Search</span>
        <input class="field" :value="search" placeholder="Search products" @input="$emit('update:search', inputValue($event))" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Category</span>
        <select class="field" :value="category" @change="$emit('update:category', inputValue($event))">
          <option value="All">All</option>
          <option v-for="item in categories" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CirclePlus } from "lucide-vue-next";

defineProps<{
  search: string;
  category: string;
  categories: string[];
  total: number;
}>();

defineEmits<{
  create: [];
  "update:search": [value: string];
  "update:category": [value: string];
}>();

function inputValue(event: Event) {
  return (event.target as HTMLInputElement | HTMLSelectElement).value;
}
</script>
