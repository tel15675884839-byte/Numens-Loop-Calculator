import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useThemeStore } from "../themeStore";

describe("themeStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    document.documentElement.className = "";
    document.documentElement.removeAttribute("data-theme");
    vi.restoreAllMocks();
  });

  it("applies and persists dark mode", () => {
    const store = useThemeStore();

    store.setTheme("dark");

    expect(store.theme).toBe("dark");
    expect(localStorage.getItem("loop-calculator.theme")).toBe("dark");
    expect(document.documentElement.classList.contains("theme-dark")).toBe(true);
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("toggles back to light mode", () => {
    const store = useThemeStore();
    store.setTheme("dark");

    store.toggleTheme();

    expect(store.theme).toBe("light");
    expect(localStorage.getItem("loop-calculator.theme")).toBe("light");
    expect(document.documentElement.classList.contains("theme-dark")).toBe(false);
    expect(document.documentElement.dataset.theme).toBe("light");
  });
});
