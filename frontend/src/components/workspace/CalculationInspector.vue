<template>
  <aside class="panel h-full flex flex-col bg-zinc-50 border-l border-zinc-200">
    <!-- Main Title -->
    <div class="panel-title border-b border-zinc-200 bg-white px-4 py-3 text-xs font-bold uppercase tracking-wider text-zinc-600 flex items-center justify-between">
      <span>Calculation Inspector</span>
      <span class="text-[10px] font-normal uppercase tracking-wider text-zinc-400">v1.0</span>
    </div>

    <div class="flex-1 overflow-y-auto space-y-4 p-4">
      <!-- System Status Card -->
      <div class="rounded-none border border-zinc-200 shadow-sm overflow-hidden bg-white">
        <div class="px-3 py-2 border-b border-zinc-100 flex justify-between items-center"
             :class="statusClass.includes('emerald') ? 'bg-emerald-50 text-emerald-800' : statusClass.includes('amber') ? 'bg-amber-50 text-amber-800' : 'bg-blue-50 text-blue-800'">
          <span class="text-xs font-bold uppercase tracking-wider">System Status</span>
          <span class="flex h-2 w-2 relative">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-none opacity-75" :class="statusClass.includes('emerald') ? 'bg-emerald-400' : 'bg-amber-400'"></span>
            <span class="relative inline-flex rounded-none h-2 w-2" :class="statusClass.includes('emerald') ? 'bg-emerald-500' : 'bg-amber-500'"></span>
          </span>
        </div>
        <div class="p-3 text-center text-xl font-extrabold text-zinc-800">
          {{ statusLabel }}
        </div>
      </div>

      <!-- Progress Metrics -->
      <div class="space-y-3">
        <!-- Addresses Progress -->
        <div class="bg-white p-3 rounded-none border border-zinc-200 shadow-sm">
          <div class="flex justify-between items-end mb-1">
            <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Loop Addresses</span>
            <span class="text-xl font-extrabold text-zinc-800">{{ result ? `${result.total_addresses} / ${result.addr_limit}` : '0 / 125' }}</span>
          </div>
          <div class="w-full bg-zinc-100 rounded-none h-2">
            <div class="h-2 rounded-none transition-all duration-500" 
                 :class="{
                   'bg-emerald-500': addressPercent <= 60,
                   'bg-amber-500': addressPercent > 60 && addressPercent <= 85,
                   'bg-orange-500': addressPercent > 85 && addressPercent <= 100,
                   'bg-red-500 animate-pulse': addressPercent > 100
                 }" 
                 :style="{ width: `${Math.min(addressPercent, 100)}%` }"></div>
          </div>
        </div>

        <!-- Current Metric -->
        <div class="bg-white p-3 rounded-none border border-zinc-200 shadow-sm flex justify-between items-center">
          <div>
            <p class="text-xs font-bold uppercase tracking-wider text-zinc-500">Current Load</p>
            <p class="text-xl font-extrabold mt-1 text-zinc-800">{{ result ? formatNumber(result.total_current_ma, 1) : '-' }} <span class="text-xs font-normal text-zinc-400">mA</span></p>
          </div>

          <!-- Fill Gauge (Classic Liquid Wave) -->
          <div class="h-12 w-12 rounded-none border-4 flex items-center justify-center font-bold text-xs transition-colors duration-300 relative overflow-hidden bg-zinc-50"
               :class="{
                 'border-emerald-100 text-emerald-700': currentPercent <= 60,
                 'border-amber-100 text-amber-700': currentPercent > 60 && currentPercent <= 85,
                 'border-orange-100 text-orange-700': currentPercent > 85 && currentPercent <= 100,
                 'border-red-200 text-red-700': currentPercent > 100
               }">
            
            <!-- 底色层：铺满 -->
            <div class="absolute inset-0 transition-colors duration-500"
                 :class="{
                   'bg-emerald-500/80': currentPercent <= 60,
                   'bg-amber-500/80': currentPercent > 60 && currentPercent <= 85,
                   'bg-orange-500/80': currentPercent > 85 && currentPercent <= 100,
                   'bg-red-500/90 animate-pulse': currentPercent > 100
                 }">
            </div>

            <!-- 旋转的波浪遮罩：白色 -->
            <div class="fill-wave-mask"
                 :style="{ bottom: `${Math.min(currentPercent, 100)}%` }">
            </div>

            <!-- 前景数字 -->
            <span class="relative z-10 font-bold tabular-nums text-zinc-900 drop-shadow-[0_1.5px_1px_rgba(255,255,255,1)]">
              {{ Math.round(currentPercent) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Other Metrics Grid -->
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div v-for="item in metrics.slice(2)" :key="item.label" class="bg-white p-3 rounded-none border border-zinc-200 shadow-sm">
          <p class="text-xs font-bold uppercase tracking-wider text-zinc-500">{{ item.label }}</p>
          <p class="mt-1 text-base font-bold text-zinc-800 tabular-nums">
            {{ item.value }} 
            <span v-if="item.unit" class="text-xs font-normal text-zinc-400 ml-0.5">{{ item.unit }}</span>
          </p>
        </div>
      </div>

      <!-- Power Calculations Card -->
      <div class="bg-zinc-50 p-3 rounded-none border border-zinc-200">
        <p class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 mb-2 flex items-center gap-1">
          <span>⚡</span> Power Calculations
        </p>
        <div class="grid grid-cols-2 gap-2 bg-white p-2 rounded-none border border-zinc-100">
          <div class="flex items-end justify-between px-1">
            <span class="text-xs font-bold uppercase text-zinc-500">Standby</span>
            <span class="text-base font-bold text-zinc-800 tabular-nums">{{ formatNumber(battery.standby_hours, 1) }}h</span>
          </div>
          <div class="flex items-end justify-between px-1">
            <span class="text-xs font-bold uppercase text-zinc-500">Alarm</span>
            <span class="text-base font-bold text-zinc-800 tabular-nums">{{ formatNumber(battery.alarm_hours, 1) }}h</span>
          </div>
        </div>
      </div>

      <!-- System Parameters Reference Card -->
      <div class="bg-zinc-50 p-3 rounded-none border border-zinc-200">
        <p class="text-[11px] font-bold uppercase tracking-wider text-zinc-500 mb-2 flex items-center gap-1">
          <span>ℹ️</span> System Parameters
        </p>
        <div class="grid grid-cols-[1fr_auto_auto] gap-y-2 items-center bg-white p-3 border border-zinc-100">
          <!-- Row 1 -->
          <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Address Limit</span>
          <span class="text-base font-bold text-zinc-800 tabular-nums text-right mr-2">{{ loop?.address_limit ?? 125 }}</span>
          <span class="text-xs font-normal text-zinc-400">Dev.</span>

          <div class="col-span-3 border-t border-zinc-100/60 my-0.5"></div>

          <!-- Row 2 -->
          <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Max Current</span>
          <span class="text-base font-bold text-zinc-800 tabular-nums text-right mr-2">{{ loop?.max_current_ma ?? 400 }}</span>
          <span class="text-xs font-normal text-zinc-400">mA</span>

          <div class="col-span-3 border-t border-zinc-100/60 my-0.5"></div>

          <!-- Row 3 -->
          <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Min Voltage</span>
          <span class="text-base font-bold text-zinc-800 tabular-nums text-right mr-2">{{ loop?.min_voltage_v ?? 17 }}</span>
          <span class="text-xs font-normal text-zinc-400">V</span>
        </div>
      </div>


      <!-- Diagnostics Card -->
      <div v-if="diagnostics.length" class="bg-amber-50/50 border border-amber-200 rounded-none p-3 text-xs shadow-sm">
        <p class="text-xs font-bold text-amber-800 uppercase tracking-wider mb-2 flex items-center gap-1">
          <span>⚠️</span> Diagnostics
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

const statusClass = computed(() => {
  if (props.busy) return "text-blue-700";
  if (diagnostics.value.length > 0) return "text-amber-700";
  return "text-emerald-700";
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
  const max = (props.result as any).max_current_ma || 400;
  return (props.result.total_current_ma / max) * 100;
});

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


<style scoped>
.fill-wave-mask {
    position: absolute;
    width: 250%; height: 250%;
    background: white; /* 遮罩层使用白色模拟空白区域 */
    border-radius: 42%; /* 制造波浪形边缘 */
    left: -75%;
    animation: spin 4s linear infinite;
    transition: bottom 0.3s ease-out;
    pointer-events: none;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

</style>




