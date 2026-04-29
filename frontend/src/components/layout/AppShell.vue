<template>
  <div class="flex h-screen min-h-0 flex-col overflow-hidden bg-zinc-50 text-zinc-900">
    <TopBar />
    <div class="grid min-h-0 flex-1 grid-cols-[18rem_minmax(0,1fr)] border-t border-zinc-200">
      <LeftNav />
      <main class="min-h-0 min-w-0 overflow-hidden">
        <RouterView v-slot="{ Component }">
          <Transition name="ios-page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
    <DialogHost />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { RouterView } from "vue-router";
import { useThemeStore } from "../../stores/themeStore";
import DialogHost from "./DialogHost.vue";
import LeftNav from "./LeftNav.vue";
import TopBar from "./TopBar.vue";

const theme = useThemeStore();

onMounted(() => {
  theme.initializeTheme();
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
