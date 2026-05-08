<template>
  <Teleport to="body">
    <Transition name="tour-fade">
      <div v-if="onboarding.isOpen && onboarding.currentStep" class="pointer-events-none fixed inset-0 z-[70] print:hidden" aria-live="polite">
        <div class="absolute inset-0 bg-zinc-950/55" />
        <div
          class="tour-highlight pointer-events-none fixed border-2 border-blue-400 bg-transparent shadow-[0_0_0_9999px_rgba(9,9,11,0.58),0_0_0_6px_rgba(37,99,235,0.22)] transition-all duration-200"
          :style="highlightStyle"
        />
        <section
          class="tour-card pointer-events-auto fixed w-[min(22rem,calc(100vw-2rem))] border border-zinc-700 bg-zinc-950 p-4 text-white shadow-2xl transition-all duration-200"
          :style="cardStyle"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
        >
          <p class="text-[11px] font-semibold uppercase tracking-wide text-blue-300">
            Step {{ onboarding.currentStepNumber }} of {{ onboarding.totalSteps }}
          </p>
          <h2 :id="titleId" class="mt-1 text-base font-semibold text-white">{{ onboarding.currentStep.title }}</h2>
          <p class="mt-2 text-sm leading-6 text-zinc-300">{{ onboarding.currentStep.description }}</p>
          <div class="mt-4 flex items-center justify-between gap-2">
            <button class="text-sm font-medium text-zinc-400 transition hover:text-white" @click="onboarding.skip">
              Skip
            </button>
            <div class="flex items-center gap-2">
              <button class="toolbar-button border-zinc-700 bg-zinc-900 text-zinc-200 hover:bg-zinc-800" :disabled="onboarding.isFirstStep" @click="onboarding.previousStep">
                Back
              </button>
              <button class="toolbar-button-primary" @click="onboarding.nextStep">
                {{ onboarding.isLastStep ? "Done" : "Next" }}
              </button>
            </div>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { useOnboardingStore } from "../../stores/onboardingStore";

const onboarding = useOnboardingStore();
const titleId = "onboarding-tour-title";
const viewportPadding = 16;
const targetPadding = 8;
const cardWidth = 352;
const cardHeight = 220;
const cardGap = 14;

interface TourRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

const targetRect = ref<TourRect>({ top: 96, left: 16, width: 360, height: 80 });
let pendingFrame: number | null = null;

function fallbackRect(): TourRect {
  return { top: 96, left: 16, width: Math.max(0, Math.min(360, window.innerWidth - 32)), height: 80 };
}

function measureCurrentTarget() {
  const fallback = { top: 96, left: 16, width: Math.min(360, window.innerWidth - 32), height: 80 };
  const target = onboarding.currentStep?.target;
  if (!target || typeof document === "undefined") {
    targetRect.value = fallbackRect();
    return;
  }
  const element = document.querySelector(`[data-tour="${target}"]`);
  if (!element) {
    targetRect.value = fallbackRect();
    return;
  }
  const rect = element.getBoundingClientRect();
  const top = Math.max(viewportPadding, rect.top - targetPadding);
  const left = Math.max(viewportPadding, rect.left - targetPadding);
  targetRect.value = {
    top,
    left,
    width: Math.max(0, Math.min(window.innerWidth - left - viewportPadding, rect.width + targetPadding * 2)),
    height: Math.max(0, Math.min(window.innerHeight - top - viewportPadding, rect.height + targetPadding * 2))
  };
}

const highlightStyle = computed(() => ({
  top: `${targetRect.value.top}px`,
  left: `${targetRect.value.left}px`,
  width: `${targetRect.value.width}px`,
  height: `${targetRect.value.height}px`
}));

const cardStyle = computed(() => {
  const rect = targetRect.value;
  const placement = onboarding.currentStep?.placement ?? "bottom";
  const maxLeft = Math.max(viewportPadding, window.innerWidth - cardWidth - viewportPadding);
  const maxTop = Math.max(viewportPadding, window.innerHeight - cardHeight - viewportPadding);
  let left = rect.left;
  let top = rect.top + rect.height + cardGap;

  if (placement === "top") {
    top = rect.top - cardHeight - cardGap;
  } else if (placement === "left") {
    left = rect.left - cardWidth - cardGap;
    top = rect.top;
  } else if (placement === "right") {
    left = rect.left + rect.width + cardGap;
    top = rect.top;
  }

  return {
    top: `${Math.min(Math.max(viewportPadding, top), maxTop)}px`,
    left: `${Math.min(Math.max(viewportPadding, left), maxLeft)}px`
  };
});

function scrollCurrentTargetIntoView() {
  const target = onboarding.currentStep?.target;
  if (!target || typeof document === "undefined") {
    return;
  }
  document.querySelector(`[data-tour="${target}"]`)?.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
}

function refreshPosition() {
  if (pendingFrame !== null) {
    window.cancelAnimationFrame(pendingFrame);
  }
  pendingFrame = window.requestAnimationFrame(() => {
    pendingFrame = null;
    measureCurrentTarget();
  });
}

function revealAndMeasureCurrentTarget() {
  scrollCurrentTargetIntoView();
  refreshPosition();
}

watch(
  () => [onboarding.isOpen, onboarding.currentStepIndex],
  async () => {
    if (!onboarding.isOpen) {
      return;
    }
    await nextTick();
    revealAndMeasureCurrentTarget();
  },
  { immediate: true }
);

if (typeof window !== "undefined") {
  window.addEventListener("resize", refreshPosition);
  window.addEventListener("scroll", refreshPosition, true);
  document.addEventListener("scroll", refreshPosition, true);
}

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", refreshPosition);
    window.removeEventListener("scroll", refreshPosition, true);
    document.removeEventListener("scroll", refreshPosition, true);
    if (pendingFrame !== null) {
      window.cancelAnimationFrame(pendingFrame);
    }
  }
});
</script>

<style scoped>
.tour-fade-enter-active,
.tour-fade-leave-active {
  transition: opacity 0.2s ease-out;
}

.tour-fade-enter-from,
.tour-fade-leave-to {
  opacity: 0;
}
</style>
