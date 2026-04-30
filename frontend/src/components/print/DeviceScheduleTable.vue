<template>
  <section class="print-section">
    <h3 class="print-section-title">Device Schedule</h3>
    <table class="print-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Category</th>
          <th>Device / Model</th>
          <th class="text-right">Qty</th>

          <th class="text-right">SBY / ea</th>
          <th class="text-right">ALM / ea</th>
          <th class="text-right">Lead</th>
          <th class="text-right">Interval</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td>{{ row.sort_order }}</td>
          <td>{{ row.category }}</td>
          <td>
            <div class="font-semibold text-zinc-900">{{ row.product_name || row.display_name || "Manual row" }}</div>
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
import { formatNumber } from "../../utils/format";

defineProps<{
  rows: LoopDeviceRow[];
}>();
</script>
