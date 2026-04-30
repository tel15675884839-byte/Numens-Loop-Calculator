<template>
  <article class="print-page">
    <PrintWatermark />

    <header class="print-page-header">
      <div>
        <p class="print-kicker">Project Summary</p>
        <h2 class="text-2xl font-bold text-zinc-950">{{ project.name }}</h2>
      </div>
      <div class="text-right text-xs text-zinc-500">
        <p>Project No. {{ profile.project_no || "-" }}</p>
        <p>Revision {{ profile.revision || "-" }}</p>
      </div>
    </header>

    <section class="grid grid-cols-2 gap-x-8 gap-y-2 border border-zinc-300 p-4 text-sm">
      <div v-for="item in metadata" :key="item.label" class="grid grid-cols-[8rem_1fr] gap-3">
        <span class="font-semibold uppercase text-zinc-500">{{ item.label }}</span>
        <span class="text-zinc-900">{{ item.value || "-" }}</span>
      </div>
    </section>

    <section class="space-y-2 mb-6">
      <div class="grid grid-cols-3 gap-2">
        <div v-for="item in metrics.slice(0, 3)" :key="item.label" class="print-metric">
          <p class="print-metric-label">{{ item.label }}</p>
          <p class="print-metric-value">{{ item.value }}</p>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div v-for="item in metrics.slice(3, 5)" :key="item.label" class="print-metric">
          <p class="print-metric-label">{{ item.label }}</p>
          <p class="print-metric-value">{{ item.value }}</p>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div v-for="item in metrics.slice(5, 7)" :key="item.label" class="print-metric">
          <p class="print-metric-label">{{ item.label }}</p>
          <p class="print-metric-value">{{ item.value }}</p>
        </div>
      </div>
    </section>

    <section class="print-section">
      <h3 class="print-section-title">Loop Summary</h3>
      <table class="print-table">
        <thead>
          <tr>
            <th>Loop</th>
            <th class="text-right">Device Qty</th>
            <th class="text-right">Current Used / Limit</th>
            <th class="text-right">Distance</th>
            <th class="text-right">End Voltage</th>
            <th>Cable</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="loop in project.loops" :key="loop.id">
            <td>{{ loop.name }}</td>
            <td class="text-right tabular-nums">{{ loop.device_rows.reduce((sum, row) => sum + row.qty, 0) }}</td>
            <td class="text-right tabular-nums">{{ currentLabel(loop) }}</td>
            <td class="text-right tabular-nums">{{ distanceLabel(loop) }}</td>
            <td class="text-right tabular-nums">{{ voltageLabel(loop) }}</td>
            <td>{{ cableLabel(loop) }}</td>
            <td>{{ statusLabel(loop) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <footer class="print-page-footer">
      <span>Project Summary</span>
      <span>Page 1 of 1</span>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import PrintWatermark from "./PrintWatermark.vue";
import type { ProjectLoop, ProjectPrintProfile, ProjectRecord } from "../../types/project";
import { formatNumber } from "../../utils/format";
import { calculateGlobalBatteryRuntime } from "../../utils/power";

const props = defineProps<{
  project: ProjectRecord;
  profile: ProjectPrintProfile;
}>();

const metadata = computed(() => [
  { label: "Customer", value: props.profile.customer },
  { label: "Site", value: props.profile.site },
  { label: "Panel", value: props.profile.panel },
  { label: "Prepared By", value: props.profile.prepared_by },
  { label: "Issue Date", value: props.profile.issue_date },
  { label: "Notes", value: props.profile.notes }
]);

const battery = computed(() => calculateGlobalBatteryRuntime(props.project));

const metrics = computed(() => {
  const loops = props.project.loops;
  const totalDevices = loops.reduce((sum, loop) => sum + loop.device_rows.reduce((rowSum, row) => rowSum + row.qty, 0), 0);
  const worstAddress = Math.max(0, ...loops.map((loop) => {
    const result = loop.calculation_result;
    return result ? (result.total_addresses / result.addr_limit) * 100 : 0;
  }));
  const worstCurrent = Math.max(0, ...loops.map((loop) => {
    const result = loop.calculation_result;
    return result ? (result.total_current_ma / result.max_current_ma) * 100 : 0;
  }));
  const voltages = loops.map((loop) => loop.calculation_result?.end_voltage_v).filter((value): value is number => typeof value === "number");
  const lowestVoltage = voltages.length > 0 ? Math.min(...voltages) : NaN;

  return [
    { label: "Total Loops", value: String(loops.length) },
    { label: "Total Devices", value: String(totalDevices) },
    { label: "Lowest End Voltage", value: `${formatNumber(lowestVoltage, 2)} V` },
    { label: "Worst Address Utilization", value: `${formatNumber(worstAddress, 0)}%` },
    { label: "Worst Current Utilization", value: `${formatNumber(worstCurrent, 0)}%` },
    { label: "Global Battery Standby Runtime", value: `${formatNumber(battery.value.standby_hours, 1)} h` },
    { label: "Global Battery Alarm Runtime", value: `${formatNumber(battery.value.alarm_hours, 1)} h` }
  ];
});

function addressLabel(loop: ProjectLoop) {
  const result = loop.calculation_result;
  return result ? `${result.total_addresses} / ${result.addr_limit}` : "-";
}

function currentLabel(loop: ProjectLoop) {
  const result = loop.calculation_result;
  return result ? `${formatNumber(result.total_current_ma, 1)} / ${formatNumber(result.max_current_ma, 0)} mA` : "-";
}

function distanceLabel(loop: ProjectLoop) {
  return loop.calculation_result ? `${formatNumber(loop.calculation_result.total_distance_m, 1)} m` : "-";
}

function voltageLabel(loop: ProjectLoop) {
  return loop.calculation_result ? `${formatNumber(loop.calculation_result.end_voltage_v, 2)} V` : "-";
}

function cableLabel(loop: ProjectLoop) {
  const result = loop.calculation_result;
  return result ? `${result.recommended_cable_size} ${result.recommended_cable_unit}` : loop.cable_size;
}

function statusLabel(loop: ProjectLoop) {
  const diagnostics = loop.calculation_result?.diagnostics ?? [];
  return diagnostics.length > 0 ? "Attention" : "Within limits";
}
</script>
