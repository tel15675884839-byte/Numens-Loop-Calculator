<template>
  <div class="panel border border-zinc-200 bg-white rounded-none shadow-sm">
    <div class="panel-title border-b border-zinc-200 bg-zinc-50 px-4 py-2 text-xs font-bold uppercase tracking-wider text-zinc-600">
      {{ t("systemParameters.systemParameters") }}
    </div>
    <div class="flex flex-wrap items-end justify-between gap-x-4 gap-y-3 px-4 py-4">
      <div class="flex flex-wrap items-end gap-x-3 gap-y-3">
        <!-- Cable Size Select -->
        <div ref="cableMenuRef" class="relative flex w-56 flex-col gap-1">
          <span :id="cableSizeLabelId" class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ t("systemParameters.cableSize") }}</span>
          <button
            type="button"
            data-testid="cable-size-trigger"
            class="flex h-[38px] w-full items-center justify-between gap-2 border border-zinc-200 bg-white px-3 text-left text-sm tabular-nums text-zinc-800 transition hover:border-zinc-300 hover:bg-zinc-50 focus-visible:border-blue-600 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-600"
            :aria-labelledby="cableSizeLabelId"
            :aria-expanded="isCableMenuOpen"
            :aria-controls="cableMenuId"
            aria-haspopup="true"
            @click="toggleCableMenu"
            @keydown.down.prevent="openCableMenu"
            @keydown.escape.stop.prevent="closeCableMenu"
          >
            <span class="min-w-0 truncate">{{ selectedCableLabel }}</span>
            <ChevronDown class="h-4 w-4 shrink-0 text-zinc-400 transition-transform" :class="{ 'rotate-180': isCableMenuOpen }" aria-hidden="true" />
          </button>

          <div
            v-if="isCableMenuOpen"
            :id="cableMenuId"
            data-testid="cable-size-menu"
            class="absolute left-0 top-full z-30 mt-1 w-full overflow-hidden border border-zinc-200 bg-white py-1 shadow-lg"
            @keydown.escape.stop.prevent="closeCableMenu"
          >
            <button
              v-for="opt in cableOptions"
              :key="opt.size"
              type="button"
              data-testid="cable-size-option"
              :data-size="opt.size"
              class="flex h-9 w-full items-center justify-between gap-2 px-3 text-left text-sm tabular-nums transition hover:bg-zinc-50 focus-visible:bg-blue-50 focus-visible:outline-none"
              :class="opt.size === selectedCableValue ? 'bg-blue-50 font-semibold text-blue-700' : 'text-zinc-700'"
              @click="selectCableSize(opt.size)"
            >
              <span class="min-w-0 truncate">{{ opt.label }}</span>
              <Check v-if="opt.size === selectedCableValue" class="h-4 w-4 shrink-0" aria-hidden="true" />
            </button>
          </div>
        </div>

        <!-- Custom Cable Inputs -->
        <template v-if="isCustomCable">
          <label class="flex w-24 flex-col gap-1">
            <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ t("systemParameters.area") }}</span>
            <input
              class="field-number h-[38px] px-2 text-center"
              :value="loop?.cable_size"
              inputmode="decimal"
              placeholder="e.g. 6.0"
              @input="onCustomAreaInput"
            />
          </label>
          <label class="flex w-28 flex-col gap-1">
            <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ t("systemParameters.resistance") }}</span>
            <input
              class="field-number h-[38px] px-2 text-center"
              :value="loop?.cable_resistance_ohm_per_km"
              inputmode="decimal"
              @input="onCustomResistanceInput"
            />
          </label>
        </template>

        <!-- AUX Current Input -->
        <label class="flex w-32 flex-col gap-1">
          <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">{{ t("systemParameters.auxCurrent") }}</span>
          <div class="relative" data-testid="aux-current-field">
            <input
              class="field-number h-[38px] pr-10 pl-3"
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
          class="toolbar-button h-[38px] justify-center px-3 text-sm font-medium"
          @click="$emit('add-category', category)"
        >
          {{ translateCurrentCategoryLabel(category) }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ChevronDown, Check } from "lucide-vue-next";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { translateCurrentCategoryLabel, translateMessage as t } from "../../i18n";
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

const cableMenuRef = ref<HTMLElement | null>(null);
const isCableMenuOpen = ref(false);
const cableMenuId = "system-cable-size-menu";
const cableSizeLabelId = "system-cable-size-label";

const isCustomCable = computed(() => {
  if (!props.loop) return false;
  const standardSizes = ["1.0", "1.5", "2.5", "4.0"];
  return !standardSizes.includes(props.loop.cable_size);
});

const cableOptions = [
  { size: "1.0", resistance: 18.1, label: "1.0 mm² (18.1 Ω/km)" },
  { size: "1.5", resistance: 12.1, label: "1.5 mm² (12.1 Ω/km)" },
  { size: "2.5", resistance: 7.41, label: "2.5 mm² (7.41 Ω/km)" },
  { size: "4.0", resistance: 4.61, label: "4.0 mm² (4.61 Ω/km)" },
  { size: "Custom", resistance: 0, label: "Custom..." },
];

const selectedCableValue = computed(() => (isCustomCable.value ? "Custom" : (props.loop?.cable_size || "1.5")));

const selectedCableLabel = computed(() => {
  if (selectedCableValue.value === "Custom") return t("systemParameters.customCable");
  return cableOptions.find((option) => option.size === selectedCableValue.value)?.label ?? t("systemParameters.selectCableSize");
});

function toggleCableMenu() {
  isCableMenuOpen.value = !isCableMenuOpen.value;
}

function openCableMenu() {
  isCableMenuOpen.value = true;
}

function closeCableMenu() {
  isCableMenuOpen.value = false;
}

function selectCableSize(selectedSize: string) {
  if (selectedSize === "Custom") {
    emit("update", {
      cable_size: "",
      cable_resistance_ohm_per_km: 0
    });
    closeCableMenu();
    return;
  }
  const option = cableOptions.find(o => o.size === selectedSize);
  if (option) {
    emit("update", {
      cable_size: selectedSize,
      cable_resistance_ohm_per_km: option.resistance
    });
  }
  closeCableMenu();
}

function onDocumentMouseDown(event: MouseEvent) {
  const target = event.target;
  if (!(target instanceof Node)) return;
  if (cableMenuRef.value && !cableMenuRef.value.contains(target)) {
    closeCableMenu();
  }
}

function onCustomAreaInput(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  const area = Number(value);
  if (value && !isNaN(area) && area > 0) {
    const calculatedRes = Number((18.1 / area).toFixed(2));
    emit("update", {
      cable_size: value,
      cable_resistance_ohm_per_km: calculatedRes
    });
  } else {
    emit("update", { cable_size: value });
  }
}

function onCustomResistanceInput(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  const res = Number(value);
  if (value && !isNaN(res)) {
    emit("update", { cable_resistance_ohm_per_km: res });
  }
}

function onAuxInput(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  const numeric = value === "" ? 0 : Number(value);
  emit("update", { 
    aux_current_ma: Number.isFinite(numeric) ? numeric : 0 
  });
}

onMounted(() => {
  document.addEventListener("mousedown", onDocumentMouseDown);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocumentMouseDown);
});
</script>
