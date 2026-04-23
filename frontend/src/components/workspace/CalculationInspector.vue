<template>
  <aside class="panel h-full">
    <div class="panel-title">Calculation inspector</div>
    <div class="space-y-4 p-4">
      <div class="rounded-none border border-zinc-200 bg-zinc-50 p-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Status</p>
        <p class="mt-1 text-sm font-semibold" :class="statusClass">{{ statusLabel }}</p>
      </div>

      <div class="grid grid-cols-2 gap-3 text-sm">
        <div v-for="item in metrics" :key="item.label" class="border border-zinc-200 p-3">
          <p class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ item.label }}</p>
          <p class="mt-1 text-right text-base font-semibold tabular-nums text-zinc-900">{{ item.value }}</p>
          <p v-if="item.unit" class="text-right text-[11px] text-zinc-500">{{ item.unit }}</p>
        </div>
      </div>

      <div class="border border-zinc-200 p-3">
        <p class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Battery runtime</p>
        <div class="mt-2 grid grid-cols-2 gap-3 text-sm">
          <div>
            <p class="text-[11px] uppercase tracking-wide text-zinc-500">Standby</p>
            <p class="text-right text-base font-semibold tabular-nums text-zinc-900">{{ formatNumber(battery.standby_hours, 1) }}</p>
            <p class="text-right text-[11px] text-zinc-500">h</p>
          </div>
          <div>
            <p class="text-[11px] uppercase tracking-wide text-zinc-500">Alarm</p>
            <p class="text-right text-base font-semibold tabular-nums text-zinc-900">{{ formatNumber(battery.alarm_hours, 1) }}</p>
            <p class="text-right text-[11px] text-zinc-500">h</p>
          </div>
        </div>
        <p class="mt-2 text-xs text-zinc-500">
          {{ formatNumber(battery.effective_capacity_ah, 2) }} Ah effective, {{ formatNumber(battery.total_standby_current_ma, 1) }} mA standby total
        </p>
      </div>

      <div class="border border-zinc-200 p-3">
        <p class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Suggestions</p>
        <p class="mt-2 text-sm text-zinc-700">{{ recommendation }}</p>
      </div>

      <div class="border border-zinc-200 p-3">
        <p class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Diagnostics</p>
        <ul class="mt-2 space-y-2 text-sm text-zinc-700">
          <li v-if="!diagnostics.length" class="text-emerald-700">No issues detected.</li>
          <li v-for="item in diagnostics" :key="item" class="border-l-2 border-amber-400 pl-2">{{ item }}</li>
        </ul>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CalculationLoopResponse } from "../../types/calculation";
import type { ProjectLoop, ProjectRecord } from "../../types/project";
import { formatNumber } from "../../utils/format";
import { calculateGlobalBatteryRuntime } from "../../utils/power";

const props = defineProps<{
  loop: ProjectLoop | null;
  project: ProjectRecord | null;
  result: CalculationLoopResponse | null;
  busy: boolean;
}>();

const diagnostics = computed(() => props.result?.diagnostics ?? []);
const battery = computed(() => calculateGlobalBatteryRuntime(props.project));

const statusLabel = computed(() => {
  if (!props.loop) return "No active loop";
  if (props.busy) return "Calculating";
  if (diagnostics.value.length > 0) return "Attention required";
  if (!props.result) return "Waiting for calculation";
  return "Within limits";
});

const statusClass = computed(() => {
  if (props.busy) return "text-blue-700";
  if (diagnostics.value.length > 0) return "text-amber-700";
  return "text-emerald-700";
});

const metrics = computed(() => [
  { label: "Addresses", value: props.result ? String(props.result.total_addresses) : "-", unit: props.result ? `/${props.result.addr_limit}` : "" },
  { label: "Current", value: props.result ? formatNumber(props.result.total_current_ma, 1) : "-", unit: "mA" },
  { label: "End voltage", value: props.result ? formatNumber(props.result.end_voltage_v, 2) : "-", unit: "V" },
  { label: "Distance", value: props.result ? formatNumber(props.result.total_distance_m, 1) : "-", unit: "m" },
  { label: "Cable", value: props.result ? props.result.recommended_cable_size : "-", unit: props.result?.recommended_cable_unit ?? "" },
  { label: "Drop", value: props.result ? formatNumber(props.result.voltage_drop_v, 2) : "-", unit: "V" }
]);

const recommendation = computed(() => {
  if (!props.result) {
    return "Run a calculation to populate loop metrics.";
  }
  if (diagnostics.value.length > 0) {
    return `Review the listed diagnostics before saving the final loop layout.`;
  }
  return `Recommended cable: ${props.result.recommended_cable_size || "N/A"} ${props.result.recommended_cable_unit}`.trim();
});
</script>
