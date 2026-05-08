<template>
  <div class="flex h-screen min-h-0 flex-col overflow-hidden bg-zinc-50 text-zinc-900 print:h-auto print:overflow-visible print:bg-white">
    <TopBar class="print:hidden" />
    <div class="grid min-h-0 flex-1 grid-cols-1 border-t border-zinc-200 lg:grid-cols-[18rem_minmax(0,1fr)] print:block print:overflow-visible print:border-none">
      <LeftNav class="print:hidden" />
      <main class="min-h-0 min-w-0 overflow-auto lg:overflow-hidden print:overflow-visible">
        <RouterView v-slot="{ Component }">
          <Transition name="ios-page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
    <DialogHost />
    <OnboardingTour />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { RouterView, useRoute } from "vue-router";
import { useOnboardingStore } from "../../stores/onboardingStore";
import { useThemeStore } from "../../stores/themeStore";
import DialogHost from "./DialogHost.vue";
import LeftNav from "./LeftNav.vue";
import OnboardingTour from "./OnboardingTour.vue";
import TopBar from "./TopBar.vue";

const theme = useThemeStore();
const onboarding = useOnboardingStore();
const route = useRoute();

const currentTourScope = computed(() => route.name === "print" ? "print" : "workspace");

onMounted(() => {
  theme.initializeTheme();
  onboarding.initialize(currentTourScope.value);
});

watch(currentTourScope, (scope) => {
  onboarding.initialize(scope);
});
</script>

<style scoped>
.ios-page-enter-active,
.ios-page-leave-active {
  transition: opacity 0.25s cubic-bezier(0.25, 1, 0.5, 1), transform 0.3s cubic-bezier(0.25, 1, 0.5, 1);
}

.ios-page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.ios-page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
