<template>
  <div class="panel">
    <div class="panel-title">System parameters</div>
    <div class="flex flex-wrap items-end gap-3 px-4 py-4">
      <label v-for="field in fields" :key="field.key" class="flex w-36 flex-col gap-1">
        <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ field.label }}</span>
        <input class="field-number" :value="field.value" :inputmode="field.inputMode" @input="field.onInput" />
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ProjectLoop } from "../../types/project";

const props = defineProps<{
  loop: ProjectLoop | null;
}>();

const emit = defineEmits<{
  update: [patch: Partial<ProjectLoop>];
}>();

function updateNumber(key: keyof ProjectLoop, value: string) {
  const numeric = value === "" ? 0 : Number(value);
  emit("update", { [key]: Number.isFinite(numeric) ? numeric : 0 } as Partial<ProjectLoop>);
}

function updateText(key: keyof ProjectLoop, value: string) {
  emit("update", { [key]: value } as Partial<ProjectLoop>);
}

const fields = computed(() => [
  {
    key: "address_limit",
    label: "Address limit",
    value: props.loop?.address_limit ?? 0,
    inputMode: "numeric",
    onInput: (event: Event) => updateNumber("address_limit", (event.target as HTMLInputElement).value)
  },
  {
    key: "max_current_ma",
    label: "Max current mA",
    value: props.loop?.max_current_ma ?? 0,
    inputMode: "decimal",
    onInput: (event: Event) => updateNumber("max_current_ma", (event.target as HTMLInputElement).value)
  },
  {
    key: "min_voltage_v",
    label: "Min voltage V",
    value: props.loop?.min_voltage_v ?? 0,
    inputMode: "decimal",
    onInput: (event: Event) => updateNumber("min_voltage_v", (event.target as HTMLInputElement).value)
  },
  {
    key: "cable_size",
    label: "Cable size",
    value: props.loop?.cable_size ?? "",
    inputMode: "text",
    onInput: (event: Event) => updateText("cable_size", (event.target as HTMLInputElement).value)
  },
  {
    key: "cable_resistance_ohm_per_km",
    label: "Resistance Ω/km",
    value: props.loop?.cable_resistance_ohm_per_km ?? 0,
    inputMode: "decimal",
    onInput: (event: Event) => updateNumber("cable_resistance_ohm_per_km", (event.target as HTMLInputElement).value)
  },
  {
    key: "aux_current_ma",
    label: "AUX current mA",
    value: props.loop?.aux_current_ma ?? 0,
    inputMode: "decimal",
    onInput: (event: Event) => updateNumber("aux_current_ma", (event.target as HTMLInputElement).value)
  }
]);
</script>
