<template>
  <template v-for="(pageData, index) in pages" :key="index">
    <article class="print-page print-page-break flex flex-col relative">
      <PrintWatermark />

      <header class="print-page-header">
        <div>
          <p class="print-kicker">{{ project.name }}</p>
          <h2 class="text-2xl font-bold text-zinc-950">
            {{ loop.name }} <span v-if="index > 0" class="text-lg font-normal text-zinc-500">(Continued)</span>
          </h2>
        </div>
        <div class="text-right text-xs text-zinc-500">
          <p>Project No. {{ profile.project_no || "-" }}</p>
          <p>Revision {{ profile.revision || "-" }}</p>
          <p>{{ profile.issue_date || "-" }}</p>
        </div>
      </header>

      <template v-if="index === 0">
        <section class="print-metric-grid">
          <div v-for="item in resultMetrics" :key="item.label" class="print-metric">
            <p class="print-metric-label">{{ item.label }}</p>
            <p class="print-metric-value">{{ item.value }}</p>
          </div>
        </section>

        <section class="print-section">
          <h3 class="print-section-title">Loop Parameters</h3>
          <div class="grid grid-cols-3 gap-2 text-xs">
            <div v-for="item in parameters" :key="item.label" class="border border-zinc-300 p-2">
              <p class="font-semibold uppercase text-zinc-500">{{ item.label }}</p>
              <p class="mt-1 font-semibold text-zinc-900">{{ item.value }}</p>
            </div>
          </div>
        </section>

        <section v-if="diagnostics.length" class="print-diagnostics mb-5">
          <h3 class="print-section-title">Diagnostics</h3>
          <ul class="space-y-1">
            <li v-for="item in diagnostics" :key="item">{{ item }}</li>
          </ul>
        </section>
      </template>

      <!-- Table content wrapper to fill space if needed -->
      <div class="flex-1">
        <DeviceScheduleTable :rows="pageData.rows" />
      </div>

      <footer class="print-page-footer">
        <span>{{ loop.name }}</span>
        <span>Page {{ index + 1 }} of {{ pages.length }}</span>
      </footer>
    </article>
  </template>
</template>

<script setup lang="ts">
import { computed } from "vue";
import DeviceScheduleTable from "./DeviceScheduleTable.vue";
import PrintWatermark from "./PrintWatermark.vue";
import type { ProjectLoop, ProjectPrintProfile, ProjectRecord } from "../../types/project";
import { formatNumber } from "../../utils/format";

const props = defineProps<{
  project: ProjectRecord;
  loop: ProjectLoop;
  profile: ProjectPrintProfile;
}>();

const diagnostics = computed(() => props.loop.calculation_result?.diagnostics ?? []);

const resultMetrics = computed(() => {
  const result = props.loop.calculation_result;
  return [
    { label: "Devices", value: result ? `${result.total_addresses} / ${result.addr_limit}` : "-" },
    { label: "Current", value: result ? `${formatNumber(result.total_current_ma, 1)} mA` : "-" },
    { label: "Distance", value: result ? `${formatNumber(result.total_distance_m, 1)} m` : "-" },
    { label: "Voltage Drop", value: result ? `${formatNumber(result.voltage_drop_v, 2)} V` : "-" },
    { label: "End Voltage", value: result ? `${formatNumber(result.end_voltage_v, 2)} V` : "-" },
    { label: "Recommended Cable", value: result ? `${result.recommended_cable_size} ${result.recommended_cable_unit}` : "-" }
  ];
});

const parameters = computed(() => [
  { label: "Address Limit", value: `${props.loop.address_limit} devices` },
  { label: "Max Current", value: `${formatNumber(props.loop.max_current_ma, 0)} mA` },
  { label: "Min Voltage", value: `${formatNumber(props.loop.min_voltage_v, 1)} V` },
  { label: "Cable Size", value: `${props.loop.cable_size || "-"} mm2` },
  { label: "Cable Resistance", value: `${formatNumber(props.loop.cable_resistance_ohm_per_km, 2)} Ohm/km` },
  { label: "AUX Current", value: `${formatNumber(props.loop.aux_current_ma, 1)} mA` }
]);

// Virtual Pagination Logic
const PAGE1_ROW_LIMIT = 11; // First page has metrics and parameters, fits ~11 rows
const PAGE_N_ROW_LIMIT = 28; // Subsequent pages only have header and table, fits ~28 rows

const pages = computed(() => {
  const rows = props.loop.device_rows || [];
  if (rows.length <= PAGE1_ROW_LIMIT) {
    return [{ rows }];
  }

  const pagedList = [];
  // Page 1
  pagedList.push({ rows: rows.slice(0, PAGE1_ROW_LIMIT) });
  
  // Page 2+
  let remaining = rows.slice(PAGE1_ROW_LIMIT);
  while (remaining.length > 0) {
    pagedList.push({ rows: remaining.slice(0, PAGE_N_ROW_LIMIT) });
    remaining = remaining.slice(PAGE_N_ROW_LIMIT);
  }

  return pagedList;
});
</script>
