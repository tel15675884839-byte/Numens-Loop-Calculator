<template>
  <div class="panel flex items-center justify-between gap-4 px-4 py-2 min-h-[3rem]">
    <!-- 2. Loop Selection Pills -->
    <div class="flex flex-1 items-center gap-2 overflow-x-auto py-1 scrollbar-none">
      <button
        v-for="loop in loops"
        :key="loop.id"
        class="inline-flex items-center justify-center h-8 px-4 rounded-md text-xs font-semibold transition flex-shrink-0"
        :class="loop.id === activeLoopId 
          ? 'bg-blue-600 text-white shadow-sm' 
          : 'bg-white text-zinc-700 border border-zinc-200 hover:bg-zinc-50 hover:border-zinc-300'"
        :title="loop.name"
        @click="$emit('select', loop.id)"
      >
        <span>Loop {{ loop.sort_order }}</span>
      </button>
    </div>

    <!-- 3. Add Button -->
    <button
      class="toolbar-button h-8 py-0 px-3 text-xs flex-shrink-0 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white"
      :disabled="!canAdd"
      :title="canAdd ? 'Add loop' : 'Maximum 6 loops'"
      @click="$emit('add')"
    >
      <CirclePlus class="h-3.5 w-3.5" />
      <span>Add loop</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { CirclePlus } from "lucide-vue-next";
import type { ProjectLoop } from "../../types/project";

defineProps<{
  loops: ProjectLoop[];
  activeLoopId: string;
  canAdd: boolean;
}>();

defineEmits<{
  select: [loopId: string];
  add: [];
}>();
</script>
