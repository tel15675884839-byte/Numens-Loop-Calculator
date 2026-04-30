<template>
  <aside class="panel h-full flex flex-col bg-zinc-50 border-l border-zinc-200">
    <div class="panel-title border-b border-zinc-200 bg-white px-4 py-3 text-xs font-bold uppercase tracking-wider text-zinc-600 flex items-center justify-between">
      <span>Calculation Inspector</span>
    </div>

    <div class="flex-1 overflow-y-auto space-y-4 p-4">
      <div class="rounded-none border border-zinc-200 shadow-sm overflow-hidden bg-white">
        <div class="status-strip" :class="statusToneClass">
          <span class="text-xs font-bold uppercase tracking-wider">System Status</span>
          <span class="flex h-2 w-2 relative">
            <span class="status-pulse animate-ping absolute inline-flex h-full w-full rounded-none opacity-75"></span>
            <span class="status-dot relative inline-flex rounded-none h-2 w-2"></span>
          </span>
        </div>
        <div class="p-3 text-center text-xl font-extrabold text-zinc-800">
          {{ statusLabel }}
        </div>
      </div>

      <div class="space-y-3">
        <div class="bg-white p-3 rounded-none border border-zinc-200 shadow-sm">
          <div class="flex justify-between items-end mb-1">
            <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Loop Addresses</span>
            <span class="text-xl font-extrabold text-zinc-800">{{ result ? `${result.total_addresses} / ${result.addr_limit}` : "0 / 125" }}</span>
          </div>
          <div class="w-full bg-zinc-100 rounded-none h-2">
            <div
              class="h-2 rounded-none transition-all duration-500"
              :class="{
                'bg-emerald-500': addressPercent <= 60,
                'bg-amber-500': addressPercent > 60 && addressPercent <= 85,
                'bg-orange-500': addressPercent > 85 && addressPercent <= 100,
                'bg-red-500 animate-pulse': addressPercent > 100
              }"
              :style="{ width: `${Math.min(addressPercent, 100)}%` }"
            ></div>
          </div>
        </div>

        <div class="bg-white p-3 rounded-none border border-zinc-200 shadow-sm flex justify-between items-center">
          <div>
            <p class="text-xs font-bold uppercase tracking-wider text-zinc-500">Current Load</p>
            <p class="text-xl font-extrabold mt-1 text-zinc-800">
              {{ result ? formatNumber(result.total_current_ma, 1) : "-" }}
              <span class="text-xs font-normal text-zinc-400">mA</span>
            </p>
          </div>

          <div
            class="h-12 w-12 rounded-none border-4 flex items-center justify-center font-bold text-xs transition-colors duration-300 relative overflow-hidden bg-zinc-50"
            :class="{
              'border-emerald-100 text-emerald-700': currentPercent <= 60,
              'border-amber-100 text-amber-700': currentPercent > 60 && currentPercent <= 85,
              'border-orange-100 text-orange-700': currentPercent > 85 && currentPercent <= 100,
              'border-red-200 text-red-700': currentPercent > 100
            }"
          >
            <div
              class="absolute inset-0 transition-colors duration-500"
              :class="{
                'bg-emerald-500/80': currentPercent <= 60,
                'bg-amber-500/80': currentPercent > 60 && currentPercent <= 85,
                'bg-orange-500/80': currentPercent > 85 && currentPercent <= 100,
                'bg-red-500/90 animate-pulse': currentPercent > 100
              }"
            ></div>

            <div class="fill-wave-mask" :style="{ bottom: `${Math.min(currentPercent, 100)}%` }"></div>

            <span class="gauge-percent relative z-10 font-bold tabular-nums text-zinc-900">
              {{ Math.round(currentPercent) }}%
            </span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-2 text-xs">
        <div v-for="item in metrics.slice(2)" :key="item.label" class="bg-white p-3 rounded-none border border-zinc-200 shadow-sm">
          <p class="text-xs font-bold uppercase tracking-wider text-zinc-500">{{ item.label }}</p>
          <p class="mt-1 text-base font-bold text-zinc-800 tabular-nums">
            {{ item.value }}
            <span v-if="item.unit" class="text-xs font-normal text-zinc-400 ml-0.5">{{ item.unit }}</span>
          </p>
        </div>
      </div>

      <div class="bg-zinc-50 p-3 rounded-none border border-zinc-200">
        <p class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 mb-2">Power Calculations</p>
        <div class="bg-white p-3 rounded-none border border-zinc-100">
          <div class="grid grid-cols-[1fr_auto] gap-3 items-center">
            <div class="space-y-3">
              <div class="flex items-end justify-between gap-3" data-testid="battery-standby">
                <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Standby</span>
                <span class="text-base font-bold text-zinc-800 tabular-nums">{{ formatNumber(battery.standby_hours, 1) }}h</span>
              </div>
              <div class="flex items-end justify-between gap-3 border-t border-zinc-100 pt-3" data-testid="battery-alarm">
                <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Alarm</span>
                <span class="text-base font-bold text-zinc-800 tabular-nums">{{ formatNumber(battery.alarm_hours, 1) }}h</span>
              </div>
            </div>
            <div class="battery-symbol" aria-hidden="true">
              <div class="battery-symbol__body">
                <div class="battery-symbol__cell"></div>
                <div class="battery-symbol__cell"></div>
                <div class="battery-symbol__cell"></div>
              </div>
              <div class="battery-symbol__cap"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-zinc-50 p-3 rounded-none border border-zinc-200">
        <p class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 mb-2">System Parameters</p>
        <div class="grid grid-cols-[1fr_auto_auto] gap-y-2 items-center bg-white p-3 border border-zinc-100">
          <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Address Limit</span>
          <span class="text-base font-bold text-zinc-800 tabular-nums text-right mr-2">{{ loop?.address_limit ?? 125 }}</span>
          <span class="text-xs font-normal text-zinc-400">Dev.</span>

          <div class="col-span-3 border-t border-zinc-100/60 my-0.5"></div>

          <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Max Current</span>
          <span class="text-base font-bold text-zinc-800 tabular-nums text-right mr-2">{{ loop?.max_current_ma ?? 400 }}</span>
          <span class="text-xs font-normal text-zinc-400">mA</span>

          <div class="col-span-3 border-t border-zinc-100/60 my-0.5"></div>

          <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Min Voltage</span>
          <span class="text-base font-bold text-zinc-800 tabular-nums text-right mr-2">{{ loop?.min_voltage_v ?? 17 }}</span>
          <span class="text-xs font-normal text-zinc-400">V</span>
        </div>
      </div>

      <div v-if="diagnostics.length" class="bg-amber-50/50 border border-amber-200 rounded-none p-3 text-xs shadow-sm">
        <p class="text-xs font-bold text-amber-800 uppercase tracking-wider mb-2 flex items-center gap-1">
          <span>!</span>
          <span>Diagnostics</span>
        </p>
        <ul class="space-y-1.5 text-amber-900">
          <li v-for="item in diagnostics" :key="item" class="flex items-start gap-1">
            <span class="text-amber-500 mt-0.5">•</span>
            <span>{{ item }}</span>
          </li>
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

const statusToneClass = computed(() => {
  if (!props.loop || props.busy || !props.result) return "status-strip-info";
  if (diagnostics.value.length > 0) return "status-strip-warning";
  return "status-strip-ok";
});

const metrics = computed(() => [
  { label: "Addresses", value: props.result ? `${props.result.total_addresses}/${props.result.addr_limit}` : "-", unit: "" },
  { label: "Current", value: props.result ? formatNumber(props.result.total_current_ma, 1) : "-", unit: "mA" },
  { label: "End voltage", value: props.result ? formatNumber(props.result.end_voltage_v, 2) : "-", unit: "V" },
  { label: "Distance", value: props.result ? formatNumber(props.result.total_distance_m, 1) : "-", unit: "m" },
  { label: "Cable", value: props.result ? props.result.recommended_cable_size : "-", unit: props.result?.recommended_cable_unit ?? "" },
  { label: "Drop", value: props.result ? formatNumber(props.result.voltage_drop_v, 2) : "-", unit: "V" }
]);

const addressPercent = computed(() => {
  if (!props.result) return 0;
  return (props.result.total_addresses / props.result.addr_limit) * 100;
});

const currentPercent = computed(() => {
  if (!props.result) return 0;
  const max = props.result.max_current_ma || 400;
  return (props.result.total_current_ma / max) * 100;
});

</script>

<style scoped>
.status-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--status-strip-border);
  padding: 0.5rem 0.75rem;
  background: var(--status-strip-bg);
  color: var(--status-strip-text);
}

.status-strip-ok {
  --status-strip-bg: var(--status-ok-bg);
  --status-strip-border: var(--status-ok-border);
  --status-strip-text: var(--status-ok-text);
  --status-dot-color: var(--status-ok-dot);
}

.status-strip-warning {
  --status-strip-bg: var(--status-warning-bg);
  --status-strip-border: var(--status-warning-border);
  --status-strip-text: var(--status-warning-text);
  --status-dot-color: var(--status-warning-dot);
}

.status-strip-info {
  --status-strip-bg: var(--status-info-bg);
  --status-strip-border: var(--status-info-border);
  --status-strip-text: var(--status-info-text);
  --status-dot-color: var(--status-info-dot);
}

.status-pulse,
.status-dot {
  background: var(--status-dot-color);
}

.fill-wave-mask {
  position: absolute;
  width: 250%;
  height: 250%;
  background: var(--gauge-empty-bg);
  border-radius: 42%;
  left: -75%;
  animation: spin 4s linear infinite;
  transition: bottom 0.3s ease-out;
  pointer-events: none;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

.gauge-percent {
  color: var(--gauge-percent-text);
  filter: var(--gauge-percent-shadow);
}

.battery-symbol {
  display: inline-flex;
  align-items: center;
  gap: 0.125rem;
  color: #10b981;
}

.battery-symbol__body {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.2rem;
  width: 3.8rem;
  height: 2.2rem;
  padding: 0 0.35rem;
  border: 2px solid currentColor;
  background: linear-gradient(180deg, rgba(236, 253, 245, 0.95) 0%, rgba(209, 250, 229, 0.7) 100%);
}

.battery-symbol__cap {
  width: 0.35rem;
  height: 0.9rem;
  background: currentColor;
  opacity: 0.8;
}

.battery-symbol__cell {
  flex: 1;
  height: 0.95rem;
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.95) 0%, rgba(52, 211, 153, 0.75) 100%);
}
</style>
