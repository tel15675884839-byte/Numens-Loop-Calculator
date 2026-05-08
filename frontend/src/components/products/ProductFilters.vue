<template>
  <div class="panel">
    <div class="flex items-center justify-between flex-wrap gap-4 px-4 py-3">
      <!-- Title -->
      <div>
        <p
          class="text-xs font-semibold uppercase tracking-wide text-zinc-500 cursor-pointer select-none hover:text-zinc-700"
          @dblclick="$emit('adminUnlock')"
        >
          {{ t("products.libraryFilters") }}
        </p>
        <p class="text-sm text-zinc-600">{{ total }} {{ t("products.products") }}</p>
      </div>

      <!-- Controls group: Search and Category buttons -->
      <div class="flex items-center flex-wrap gap-6">
        <!-- Search -->
        <div class="flex items-center gap-2">
          <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ t("products.search") }}</span>
          <input
            class="field w-60 py-1.5 text-sm"
            :value="search"
            :placeholder="t('products.searchProducts')"
            @input="$emit('update:search', inputValue($event))"
          />
        </div>

        <!-- Category -->
        <div class="flex items-center gap-2">
          <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ t("common.category") }}</span>
          <div class="flex items-center gap-1.5">
            <button
              class="toolbar-button text-xs px-2.5 py-1"
              :class="{ 'border-blue-600 bg-blue-50 text-blue-700 font-semibold': category === 'All' }"
              @click="$emit('update:category', 'All')"
            >
              {{ t("products.all") }}
            </button>
            <button
              v-for="item in categories"
              :key="item"
              class="toolbar-button text-xs px-2.5 py-1"
              :class="{ 'border-blue-600 bg-blue-50 text-blue-700 font-semibold': category === item }"
              @click="$emit('update:category', item)"
            >
              {{ translateCurrentCategoryLabel(item) }}
            </button>
          </div>
        </div>
      </div>

      <!-- Admin Controls -->
      <div class="flex items-center gap-2">
        <button v-if="isAdmin" class="toolbar-button px-3 py-1.5 text-xs" @click="$emit('openDeletedProducts')">
          <RotateCcw class="h-4 w-4 text-zinc-500" />
          <span>{{ t("products.deleted") }}</span>
        </button>
        <button v-if="isAdmin" class="toolbar-button px-3 py-1.5 text-xs" @click="$emit('adminUnlock')">
          <Lock class="h-4 w-4 text-zinc-500" />
          <span>{{ t("products.lock") }}</span>
        </button>
        <button class="toolbar-button-primary px-3 py-1.5 text-xs" @click="$emit('create')">
          <CirclePlus class="h-4 w-4" />
          <span>{{ t("products.addProduct") }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CirclePlus, Lock, RotateCcw } from "lucide-vue-next";
import { translateCurrentCategoryLabel, translateMessage as t } from "../../i18n";

defineProps<{
  search: string;
  category: string;
  categories: string[];
  total: number;
  isAdmin: boolean;
}>();

defineEmits<{
  create: [];
  adminUnlock: [];
  openDeletedProducts: [];
  "update:search": [value: string];
  "update:category": [value: string];
}>();

function inputValue(event: Event) {
  return (event.target as HTMLInputElement | HTMLSelectElement).value;
}
</script>
