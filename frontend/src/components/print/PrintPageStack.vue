<template>
  <div class="print-page-stack">
    <ProjectSummaryPage :project="project" :profile="profile" />
    <LoopReportPage
      v-for="loop in project.loops"
      :key="loop.id"
      :project="project"
      :loop="loop"
      :profile="profile"
    />
  </div>
</template>

<script setup lang="ts">
import LoopReportPage from "./LoopReportPage.vue";
import ProjectSummaryPage from "./ProjectSummaryPage.vue";
import type { ProjectPrintProfile, ProjectRecord } from "../../types/project";

defineProps<{
  project: ProjectRecord;
  profile: ProjectPrintProfile;
}>();
</script>
