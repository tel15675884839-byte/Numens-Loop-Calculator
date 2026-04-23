<template>
  <div class="panel">
    <div class="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Loops</p>
        <p class="text-sm text-zinc-600">{{ loops.length }} configured</p>
      </div>
      <button class="toolbar-button" @click="$emit('add')">
        <CirclePlus class="h-4 w-4" />
        <span>Add loop</span>
      </button>
    </div>
    <div class="flex gap-2 overflow-x-auto px-3 py-3">
      <button
        v-for="loop in loops"
        :key="loop.id"
        class="inline-flex min-w-[10rem] flex-col border px-3 py-2 text-left transition"
        :class="loop.id === activeLoopId ? 'border-blue-600 bg-blue-50 text-blue-800' : 'border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300 hover:bg-zinc-50'"
        @click="$emit('select', loop.id)"
      >
        <span class="text-[11px] uppercase tracking-wide text-zinc-500">Loop {{ loop.sort_order }}</span>
        <span class="truncate text-sm font-semibold">{{ loop.name }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CirclePlus } from "lucide-vue-next";
import type { ProjectLoop } from "../../types/project";

defineProps<{
  loops: ProjectLoop[];
  activeLoopId: string;
}>();

defineEmits<{
  select: [loopId: string];
  add: [];
}>();
</script>
