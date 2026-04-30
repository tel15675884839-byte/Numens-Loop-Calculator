<template>
  <div class="panel border border-zinc-200 bg-white rounded-none shadow-sm">
    <div class="panel-title border-b border-zinc-200 bg-zinc-50 px-4 py-2 text-xs font-bold uppercase tracking-wider text-zinc-600">
      System Parameters
    </div>
    <div class="flex flex-wrap items-end justify-between gap-3 px-4 py-4">
      <div class="flex flex-wrap items-end gap-3">
        <!-- Cable Size Select -->
        <label class="flex w-44 flex-col gap-1">
          <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400">Cable Size</span>
          <select 
            class="field-number !text-center rounded-none h-[38px] bg-white border border-zinc-200 px-3 text-sm text-zinc-800 focus:outline-none focus:border-zinc-400"
            style="text-align-last: center; padding-left: 24px;"
            :value="loop?.cable_size || '1.5'"
            @change="onCableSizeChange"
          >
            <option v-for="opt in cableOptions" :key="opt.size" :value="opt.size" class="text-center">
              {{ opt.label }}
            </option>
          </select>
        </label>

        <!-- AUX Current Input -->
        <label class="flex w-32 flex-col gap-1">
          <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400">AUX current</span>
          <div class="relative" data-testid="aux-current-field">
            <input
              class="field-number rounded-none h-[38px] border border-zinc-200 pr-10 pl-3 text-sm text-zinc-800 focus:outline-none focus:border-zinc-400"
              :value="loop?.aux_current_ma ?? 0"
              inputmode="decimal"
              @input="onAuxInput"
            />
            <span class="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs text-zinc-400">mA</span>
          </div>
        </label>
      </div>

      <!-- Device Creation Buttons -->
      <div class="flex flex-wrap items-end gap-2">
        <button
          v-for="category in categories"
          :key="category"
          class="toolbar-button px-3 text-sm h-[38px] flex items-center justify-center font-medium rounded-none"
          @click="$emit('add-category', category)"
        >
          {{ category }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import type { ProjectLoop } from "../../types/project";

const props = withDefaults(
  defineProps<{
    loop: ProjectLoop | null;
    categories?: string[];
  }>(),
  {
    categories: () => []
  }
);

const emit = defineEmits<{
  update: [patch: Partial<ProjectLoop>];
  "add-category": [category: string];
}>();

const cableOptions = [
  { size: "1.0", resistance: 18.1, label: "1.0 mm² (18.1 Ω/km)" },
  { size: "1.5", resistance: 12.1, label: "1.5 mm² (12.1 Ω/km)" },
  { size: "2.5", resistance: 7.41, label: "2.5 mm² (7.41 Ω/km)" },
  { size: "4.0", resistance: 4.61, label: "4.0 mm² (4.61 Ω/km)" },
];

function onCableSizeChange(event: Event) {
  const selectedSize = (event.target as HTMLSelectElement).value;
  const option = cableOptions.find(o => o.size === selectedSize);
  if (option) {
    emit("update", {
      cable_size: selectedSize,
      cable_resistance_ohm_per_km: option.resistance
    });
  }
}

function onAuxInput(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  const numeric = value === "" ? 0 : Number(value);
  emit("update", { 
    aux_current_ma: Number.isFinite(numeric) ? numeric : 0 
  });
}
</script>
