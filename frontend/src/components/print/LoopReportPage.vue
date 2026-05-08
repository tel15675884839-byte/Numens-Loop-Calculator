<template>
  <template v-for="(pageData, index) in pages" :key="index">
    <article class="print-page print-page-break flex flex-col relative">
      <PrintWatermark />

      <header class="print-page-header">
        <div>
          <p class="print-kicker">{{ project.name }}</p>
          <h2 class="text-2xl font-bold text-zinc-950">
            {{ loop.name }} <span v-if="index > 0" class="text-lg font-normal text-zinc-500">({{ t("common.continue") }})</span>
          </h2>
        </div>
        <div class="text-right text-xs text-zinc-500">
          <p>{{ t("print.projectNo") }} {{ profile.project_no || "-" }}</p>
          <p>{{ t("print.revision") }} {{ profile.revision || "-" }}</p>
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
          <h3 class="print-section-title">{{ t("print.loopParameters") }}</h3>
          <div class="grid grid-cols-3 gap-2 text-xs">
            <div v-for="item in parameters" :key="item.label" class="border border-zinc-300 p-2">
              <p class="font-semibold uppercase text-zinc-500">{{ item.label }}</p>
              <p class="mt-1 font-semibold text-zinc-900">{{ item.value }}</p>
            </div>
          </div>
        </section>

        <section v-if="diagnostics.length" class="print-diagnostics mb-5">
          <h3 class="print-section-title">{{ t("inspector.diagnostics") }}</h3>
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
        <span>{{ t("print.page") }} {{ index + 1 }} of {{ pages.length }}</span>
      </footer>
    </article>
  </template>
</template>

<script setup lang="ts">
import { computed } from "vue";
import DeviceScheduleTable from "./DeviceScheduleTable.vue";
import PrintWatermark from "./PrintWatermark.vue";
import { translateMessage as t } from "../../i18n";
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
    { label: t("print.deviceQty"), value: result ? `${result.total_addresses} / ${result.addr_limit}` : "-" },
    { label: t("inspector.alarmLoad"), value: result ? `${formatNumber(result.total_current_ma, 1)} mA` : "-" },
    { label: t("common.distance"), value: result ? `${formatNumber(result.total_distance_m, 1)} m` : "-" },
    { label: t("print.voltageDrop"), value: result ? `${formatNumber(result.voltage_drop_v, 2)} V` : "-" },
    { label: t("inspector.endVoltage"), value: result ? `${formatNumber(result.end_voltage_v, 2)} V` : "-" },
    { label: t("print.cable"), value: props.loop.cable_size ? `${props.loop.cable_size} mm2` : "-" }
  ];
});

const parameters = computed(() => [
  { label: t("inspector.addressLimit"), value: `${props.loop.address_limit} ${t("common.devices")}` },
  { label: t("inspector.maxCurrent"), value: `${formatNumber(props.loop.max_current_ma, 0)} mA` },
  { label: t("inspector.minVoltage"), value: `${formatNumber(props.loop.min_voltage_v, 1)} V` },
  { label: t("inspector.cableSize"), value: `${props.loop.cable_size || "-"} mm2` },
  { label: t("inspector.cableResistance"), value: `${formatNumber(props.loop.cable_resistance_ohm_per_km, 2)} Ohm/km` },
  { label: t("inspector.auxCurrent"), value: `${formatNumber(props.loop.aux_current_ma, 1)} mA` }
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
