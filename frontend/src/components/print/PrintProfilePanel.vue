<template>
  <aside class="panel bg-white flex flex-col h-full">
    <div class="panel-title border-b border-zinc-100 pb-2">Report Profile</div>
    
    <!-- Template Selection -->
    <div v-if="print.templates.length > 0" class="px-4 pt-3 pb-1">
      <div class="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-2">Saved Templates</div>
      <div class="flex flex-wrap gap-1.5">
        <div 
          v-for="t in print.templates" 
          :key="t.template_name"
          class="group flex items-center gap-1 px-2 py-1 bg-zinc-50 border border-zinc-200 rounded-md hover:border-zinc-300 transition-colors cursor-pointer"
          @click="print.applyTemplate(t)"
        >
          <span class="text-xs text-zinc-600 truncate max-w-[120px]">{{ t.template_name }}</span>
          <button 
            class="opacity-0 group-hover:opacity-100 hover:text-red-500 transition-opacity" 
            @click.stop="print.deleteTemplate(t.template_name)"
          >
            <X class="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>

    <div class="space-y-3 p-4 flex-1 overflow-auto">
      <label v-for="field in fields" :key="field.key" class="block">
        <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500">{{ field.label }}</span>
        <textarea
          v-if="field.key === 'notes'"
          class="field mt-1 min-h-24 resize-none"
          :value="profile[field.key]"
          @input="emitUpdate(field.key, ($event.target as HTMLTextAreaElement).value)"
        />
        <input
          v-else
          class="field mt-1"
          :value="profile[field.key]"
          @input="emitUpdate(field.key, ($event.target as HTMLInputElement).value)"
        />
      </label>
    </div>

    <div class="border-t border-zinc-200 bg-zinc-50 p-4 space-y-2">
      <button class="toolbar-button w-full justify-center" @click="print.saveDefaults">
        <Save class="h-4 w-4" />
        <span>Save as Project Defaults</span>
      </button>
      <button class="toolbar-button w-full justify-center bg-white border border-zinc-200 hover:bg-zinc-50" @click="handleSaveTemplate">
        <Bookmark class="h-4 w-4 text-zinc-500" />
        <span class="text-zinc-600">Save as New Template</span>
      </button>
      <button class="toolbar-button w-full justify-center text-zinc-400 hover:text-zinc-600" @click="print.resetDraft">
        <RotateCcw class="h-4 w-4" />
        <span>Reset to Defaults</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { RotateCcw, Save, X, Bookmark } from "lucide-vue-next";
import { usePrintStore } from "../../stores/printStore";
import { useDialogStore } from "../../stores/dialogStore";
import type { ProjectPrintProfile } from "../../types/project";

const print = usePrintStore();
const dialog = useDialogStore();

defineProps<{
  profile: ProjectPrintProfile;
}>();

const emit = defineEmits<{
  update: [patch: Partial<ProjectPrintProfile>];
}>();

const fields: Array<{ key: keyof ProjectPrintProfile; label: string }> = [
  { key: "project_no", label: "Project No" },
  { key: "customer", label: "Customer" },
  { key: "site", label: "Site" },
  { key: "panel", label: "Panel" },
  { key: "revision", label: "Revision" },
  { key: "prepared_by", label: "Prepared By" },
  { key: "issue_date", label: "Issue Date" },
  { key: "notes", label: "Notes" }
];

function emitUpdate(key: keyof ProjectPrintProfile, value: string) {
  emit("update", { [key]: value });
}

async function handleSaveTemplate() {
  const name = await dialog.prompt({
    title: "Save as Template",
    message: "Enter a name for this report profile template:",
    initialValue: ""
  });
  
  if (name) {
    print.saveAsTemplate(name);
  }
}
</script>
