<template>
  <section class="print-section">
    <h3 class="print-section-title">{{ t("print.deviceSchedule") }}</h3>
    <table class="print-table">
      <thead>
        <tr>
          <th>#</th>
          <th>{{ t("common.category") }}</th>
          <th>{{ t("print.deviceModel") }}</th>
          <th class="text-right">{{ t("common.qty") }}</th>

          <th class="text-right">{{ t("common.standby") }}</th>
          <th class="text-right">{{ t("common.alarm") }}</th>
          <th class="text-right">{{ t("deviceTable.lead") }}</th>
          <th class="text-right">{{ t("deviceTable.interval") }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td>{{ row.sort_order }}</td>
          <td>{{ translateCurrentCategoryLabel(row.category) }}</td>
          <td>
            <div class="font-semibold text-zinc-900">{{ row.product_name || row.display_name || t("print.unassignedDevice") }}</div>
            <div class="text-[10px] text-zinc-500">{{ row.customer_name || row.factory_name || row.device_type }}</div>
          </td>
          <td class="text-right tabular-nums">{{ row.qty }}</td>

          <td class="text-right tabular-nums">{{ formatNumber(row.standby_ma, 1) }} mA</td>
          <td class="text-right tabular-nums">{{ formatNumber(row.alarm_ma, 1) }} mA</td>
          <td class="text-right tabular-nums">{{ formatNumber(row.lead_dist_m, 1) }} m</td>
          <td class="text-right tabular-nums">{{ formatNumber(row.interval_dist_m, 1) }} m</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import type { LoopDeviceRow } from "../../types/project";
import { translateCurrentCategoryLabel, translateMessage as t } from "../../i18n";
import { formatNumber } from "../../utils/format";

defineProps<{
  rows: LoopDeviceRow[];
}>();
</script>
