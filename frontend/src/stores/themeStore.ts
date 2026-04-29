import { ref } from "vue";
import { defineStore } from "pinia";

type ThemeMode = "light" | "dark";

const THEME_KEY = "loop-calculator.theme";

function isThemeMode(value: string | null): value is ThemeMode {
  return value === "light" || value === "dark";
}

function applyThemeClass(mode: ThemeMode) {
  document.documentElement.classList.toggle("theme-dark", mode === "dark");
  document.documentElement.classList.toggle("theme-light", mode === "light");
  document.documentElement.dataset.theme = mode;
  document.documentElement.style.colorScheme = mode;
}

export const useThemeStore = defineStore("theme", () => {
  const theme = ref<ThemeMode>("light");

  function initializeTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    const preferred = window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    setTheme(isThemeMode(saved) ? saved : preferred);
  }

  function setTheme(mode: ThemeMode) {
    theme.value = mode;
    localStorage.setItem(THEME_KEY, mode);
    applyThemeClass(mode);
  }

  function toggleTheme() {
    setTheme(theme.value === "dark" ? "light" : "dark");
  }

  return {
    theme,
    initializeTheme,
    setTheme,
    toggleTheme
  };
});
