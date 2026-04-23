<template>
  <div v-if="open" class="absolute inset-y-0 right-0 z-20 w-[24rem] border-l border-zinc-200 bg-white">
    <div class="flex h-full min-h-0 flex-col">
      <div class="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Product editor</p>
          <p class="text-sm text-zinc-600">{{ draft.id ?? "New product" }}</p>
        </div>
        <button class="toolbar-button-ghost" @click="$emit('close')">
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="min-h-0 flex-1 overflow-auto px-4 py-4">
        <div class="space-y-3">
          <label class="flex flex-col gap-1">
            <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Category</span>
            <select class="field" :value="draft.category" @change="patch({ category: inputValue($event) })">
              <option v-for="option in categoryOptions" :key="option" :value="option">{{ option }}</option>
            </select>
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Product name</span>
            <input class="field" :value="draft.product_name" @input="patch({ product_name: inputValue($event) })" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Customer name</span>
            <input class="field" :value="draft.customer_name" @input="patch({ customer_name: inputValue($event) })" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Factory name</span>
            <input class="field" :value="draft.factory_name" @input="patch({ factory_name: inputValue($event) })" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Type</span>
            <input class="field" :value="draft.type" @input="patch({ type: inputValue($event) })" />
          </label>

          <div class="grid grid-cols-3 gap-3">
            <label class="flex flex-col gap-1">
              <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Standby mA</span>
              <input class="field-number" inputmode="decimal" :value="draft.standby" @input="patchNumber('standby', $event)" />
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Alarm mA</span>
              <input class="field-number" inputmode="decimal" :value="draft.alarm" @input="patchNumber('alarm', $event)" />
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">LED cost</span>
              <input class="field-number" inputmode="numeric" :value="draft.ledCost" @input="patchInteger('ledCost', $event)" />
            </label>
          </div>

          <div class="border border-zinc-200 p-3 text-sm text-zinc-600">
            <p class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Protection</p>
            <p class="mt-2">
              {{ draft.built_in ? "Built-in products stay protected from deletion." : "Custom products can be deleted from the editor or table." }}
            </p>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between gap-2 border-t border-zinc-200 px-4 py-3">
        <button class="toolbar-button" @click="$emit('close')">Cancel</button>
        <div class="flex items-center gap-2">
          <button class="toolbar-button" :disabled="draft.built_in" @click="$emit('delete')">
            <Trash2 class="h-4 w-4" />
            <span>Delete</span>
          </button>
          <button class="toolbar-button-primary" @click="$emit('save')">
            <Save class="h-4 w-4" />
            <span>Save</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Save, Trash2, X } from "lucide-vue-next";
import type { ProductDraft } from "../../types/product";

const props = defineProps<{
  open: boolean;
  draft: ProductDraft & { id?: string };
  categories: string[];
}>();

const emit = defineEmits<{
  close: [];
  save: [];
  delete: [];
  patch: [patch: Partial<ProductDraft>];
}>();

const categoryOptions = computed(() => ["Detector", ...props.categories.filter((category) => category !== "Detector")]);

function inputValue(event: Event) {
  return (event.target as HTMLInputElement | HTMLSelectElement).value;
}

function patch(patchValue: Partial<ProductDraft>) {
  emit("patch", patchValue);
}

function patchNumber(key: "standby" | "alarm", event: Event) {
  const numeric = Number(inputValue(event));
  patch({ [key]: Number.isFinite(numeric) ? numeric : 0 } as Partial<ProductDraft>);
}

function patchInteger(key: "ledCost", event: Event) {
  const numeric = Math.round(Number(inputValue(event)));
  patch({ [key]: Number.isFinite(numeric) ? numeric : 0 } as Partial<ProductDraft>);
}
</script>
