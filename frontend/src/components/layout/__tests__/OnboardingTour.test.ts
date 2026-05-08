import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const tourPath = resolve(process.cwd(), "src/components/layout/OnboardingTour.vue");

describe("OnboardingTour", () => {
  it("renders a global spotlight overlay attached to the document body", () => {
    const source = readFileSync(tourPath, "utf8");

    expect(source).toContain('<Teleport to="body">');
    expect(source).toContain("tour-highlight");
    expect(source).toContain("tour-card");
    expect(source).toContain("aria-live");
  });

  it("positions itself from the active data-tour target", () => {
    const source = readFileSync(tourPath, "utf8");

    expect(source).toContain("[data-tour=\"");
    expect(source).toContain("getBoundingClientRect");
    expect(source).toContain("scrollIntoView");
    expect(source).toContain("resize");
  });

  it("keeps spotlight geometry reactive when viewport or scroll position changes", () => {
    const source = readFileSync(tourPath, "utf8");

    expect(source).toContain("const targetRect = ref<TourRect>");
    expect(source).toContain("measureCurrentTarget");
    expect(source).toContain("requestAnimationFrame");
    expect(source).toContain('window.addEventListener("scroll"');
    expect(source).toContain('document.addEventListener("scroll"');
  });

  it("does not block resize or page scrolling while the guide is open", () => {
    const source = readFileSync(tourPath, "utf8");

    expect(source).toContain("pointer-events-none fixed inset-0");
    expect(source).toContain("pointer-events-auto");
  });

  it("exposes skip, previous, and next controls", () => {
    const source = readFileSync(tourPath, "utf8");

    expect(source).toContain("onboarding.skip");
    expect(source).toContain("onboarding.previousStep");
    expect(source).toContain("onboarding.nextStep");
    expect(source).toContain("Done");
  });
});
