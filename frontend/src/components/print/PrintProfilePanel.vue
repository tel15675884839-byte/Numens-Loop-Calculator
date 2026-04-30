<template>
  <aside class="panel bg-white flex flex-col h-full relative">
    <div class="panel-title border-b border-zinc-100 pb-2">Report Profile</div>
    
    <!-- Template Selection -->
    <div class="px-4 pt-3 pb-1">
      <div class="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-2">Saved Templates</div>
      <div v-if="print.templates.length > 0" class="grid gap-2">
        <button 
          v-for="t in print.templates" 
          :key="t.template_name"
          type="button"
          :data-template-name="t.template_name"
          class="group flex min-h-11 w-full items-center justify-between gap-2 rounded-lg border px-3 py-2 text-left transition-all duration-200"
          :class="print.selectedTemplateName === t.template_name ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-zinc-200 bg-zinc-50 text-zinc-700 hover:border-zinc-300'"
          @click="print.selectTemplate(t.template_name)"
        >
          <span class="truncate text-sm font-medium">{{ t.template_name }}</span>
          <div class="flex items-center gap-2">
            <span v-if="print.selectedTemplateName === t.template_name" class="text-[10px] font-bold uppercase tracking-wider">Selected</span>
            <button 
              v-if="print.selectedTemplateName === t.template_name"
              class="rounded-full p-1 hover:bg-blue-100 transition-colors"
              title="Exit Template"
              @click.stop="print.deselectTemplate()"
            >
              <X class="h-3 w-3" />
            </button>
          </div>
        </button>
      </div>
      <div v-else class="rounded-lg border border-dashed border-zinc-200 bg-zinc-50 px-3 py-4 text-sm text-zinc-500">
        No templates yet.
      </div>
    </div>

    <div class="flex-1 overflow-hidden relative">
      <Transition name="fade-slide">
        <div v-if="print.selectedTemplateName" :key="print.selectedTemplateName" class="absolute inset-0 p-4 space-y-3 overflow-auto">
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
        <div v-else class="absolute inset-0 px-4 py-6 text-sm text-zinc-500 flex flex-col items-center justify-center text-center">
          <Bookmark class="h-12 w-12 text-zinc-100 mb-2" />
          <p>Select a template above to edit its report fields.</p>
        </div>
      </Transition>
    </div>

    <div class="border-t border-zinc-200 bg-zinc-50 p-4 space-y-2">
      <!-- Actions when a template is selected -->
      <template v-if="print.selectedTemplateName">
        <button 
          class="flex w-full items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-semibold transition-all duration-200" 
          :class="activeFeedback === 'apply' ? 'border-emerald-200 bg-emerald-50 text-emerald-600' : 'border-blue-600 bg-blue-600 text-white hover:bg-blue-700 shadow-sm'"
          @click="handleApply"
        >
          <Zap v-if="activeFeedback !== 'apply'" class="h-4 w-4" />
          <CheckCircle2 v-else class="h-4 w-4" />
          <span>{{ activeFeedback === 'apply' ? 'Applied!' : 'Apply' }}</span>
        </button>

        <div class="grid grid-cols-2 gap-2">
          <button 
            class="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-semibold transition-all duration-200" 
            :class="activeFeedback === 'save' ? 'border-emerald-200 bg-emerald-50 text-emerald-600' : 'border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 hover:border-zinc-300'"
            @click="handleSave"
          >
            <Save v-if="activeFeedback !== 'save'" class="h-4 w-4" />
            <CheckCircle2 v-else class="h-4 w-4" />
            <span>{{ activeFeedback === 'save' ? 'Saved!' : 'Save' }}</span>
          </button>

          <button 
            class="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-semibold transition-all duration-200" 
            :class="activeFeedback === 'rename' ? 'border-emerald-200 bg-emerald-50 text-emerald-600' : 'border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 hover:border-zinc-300'"
            @click="handleRename"
          >
            <Type v-if="activeFeedback !== 'rename'" class="h-4 w-4" />
            <CheckCircle2 v-else class="h-4 w-4" />
            <span>{{ activeFeedback === 'rename' ? 'Renamed!' : 'Rename' }}</span>
          </button>
        </div>

        <!-- Delete Button (Danger) -->
        <button 
          class="flex w-full items-center justify-center gap-2 rounded-lg border border-red-200 bg-white px-4 py-2.5 text-sm font-semibold text-red-500 transition-all duration-200 hover:bg-red-50 hover:border-red-300 hover:text-red-600"
          @click="print.deleteSelectedTemplate"
        >
          <Trash2 class="h-4 w-4" />
          <span>Delete</span>
        </button>
      </template>

      <!-- Action when NO template is selected -->
      <template v-else>
        <button 
          class="flex w-full items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-semibold transition-all duration-200" 
          :class="activeFeedback === 'new' ? 'border-emerald-200 bg-emerald-50 text-emerald-600' : 'border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 hover:border-zinc-300'"
          @click="handleCreateNew"
        >
          <Plus v-if="activeFeedback !== 'new'" class="h-4 w-4" />
          <CheckCircle2 v-else class="h-4 w-4" />
          <span>{{ activeFeedback === 'new' ? 'Created!' : 'New Template' }}</span>
        </button>
      </template>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Plus, Save, Trash2, X, Bookmark, CheckCircle2, Type, Zap } from "lucide-vue-next";
import { usePrintStore } from "../../stores/printStore";
import { useDialogStore } from "../../stores/dialogStore";
import type { ProjectPrintProfile } from "../../types/project";

const print = usePrintStore();
const dialog = useDialogStore();

const activeFeedback = ref<string | null>(null);
let feedbackTimer: ReturnType<typeof setTimeout> | null = null;

function triggerFeedback(key: string) {
  if (feedbackTimer) clearTimeout(feedbackTimer);
  activeFeedback.value = key;
  feedbackTimer = setTimeout(() => {
    activeFeedback.value = null;
  }, 1500);
}

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

function handleApply() {
  print.applyToReport();
  triggerFeedback("apply");
}

function handleSave() {
  print.saveSelectedTemplate();
  triggerFeedback("save");
}

async function handleRename() {
  const newName = await dialog.prompt({
    title: "Rename Template",
    message: "Enter a new name for this template:",
    initialValue: print.selectedTemplateName || ""
  });
  
  if (newName) {
    print.renameSelectedTemplate(newName);
    triggerFeedback("rename");
  }
}

async function handleCreateNew() {
  const name = await dialog.prompt({
    title: "New Template",
    message: "Enter a name for this new report profile template:",
    initialValue: ""
  });
  
  if (name) {
    print.saveAsTemplate(name);
    triggerFeedback("new");
  }
}
</script>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>
