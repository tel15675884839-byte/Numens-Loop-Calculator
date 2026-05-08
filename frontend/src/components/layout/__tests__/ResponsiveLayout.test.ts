import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const appShell = readFileSync(resolve(process.cwd(), "src/components/layout/AppShell.vue"), "utf8");
const workspaceView = readFileSync(resolve(process.cwd(), "src/views/WorkspaceView.vue"), "utf8");
const printPreviewView = readFileSync(resolve(process.cwd(), "src/views/PrintPreviewView.vue"), "utf8");
const printProfilePanel = readFileSync(resolve(process.cwd(), "src/components/print/PrintProfilePanel.vue"), "utf8");
const topBar = readFileSync(resolve(process.cwd(), "src/components/layout/TopBar.vue"), "utf8");
const leftNav = readFileSync(resolve(process.cwd(), "src/components/layout/LeftNav.vue"), "utf8");

describe("responsive app layout", () => {
  it("keeps desktop two-column shells behind the large-screen breakpoint", () => {
    expect(appShell).toContain("lg:grid-cols-[18rem_minmax(0,1fr)]");
    expect(workspaceView).toContain("lg:grid-cols-[minmax(0,1fr)_22rem]");
    expect(printPreviewView).toContain("lg:grid-cols-[20rem_minmax(0,1fr)]");
  });

  it("allows the top toolbar to wrap instead of forcing horizontal page overflow", () => {
    expect(topBar).toContain("flex-wrap");
    expect(topBar).toContain("min-h-16");
  });

  it("exposes language switching from the top toolbar", () => {
    expect(topBar).toContain("SUPPORTED_LOCALES");
    expect(topBar).toContain("selectedLocale");
    expect(topBar).toContain("setLocale");
  });

  it("uses a styled custom language menu instead of the native select popup", () => {
    expect(topBar).toContain('data-testid="language-menu-trigger"');
    expect(topBar).toContain('data-testid="language-menu"');
    expect(topBar).not.toContain("<select");
    expect(topBar).toContain("isLanguageMenuOpen");
  });

  it("exposes a fixed Numens website link in the app shell", () => {
    expect(appShell).toContain('href="https://www.numens.com"');
    expect(appShell).toContain('target="_blank"');
    expect(appShell).toContain('rel="noopener noreferrer"');
    expect(appShell).toContain("fixed bottom-3 right-4");
    expect(appShell).toContain("www.numens.com");
  });

  it("wires the first-use tutorial into the main workspace shell", () => {
    expect(appShell).toContain("<OnboardingTour />");
    expect(appShell).toContain("onboarding.initialize");
    expect(topBar).toContain('data-tour="project-actions"');
    expect(topBar).toContain("onboarding.startReplay");
    expect(leftNav).toContain("data-tour=\"project-list\"");
    expect(workspaceView).toContain("data-tour=\"loop-tabs\"");
    expect(workspaceView).toContain("data-tour=\"system-parameters\"");
    expect(workspaceView).toContain("data-tour=\"device-table\"");
    expect(workspaceView).toContain("data-tour=\"calculation-results\"");
    expect(topBar).toContain("currentTourScope");
    expect(appShell).toContain("onboarding.initialize(currentTourScope.value)");
    expect(topBar).toContain("'print-actions'");
    expect(printProfilePanel).toContain("data-tour=\"print-templates\"");
    expect(printProfilePanel).toContain("data-tour=\"print-template-editor\"");
    expect(printProfilePanel).toContain("data-tour=\"print-template-actions\"");
    expect(printPreviewView).toContain("data-tour=\"print-preview\"");
  });

  it("uses tight targets for the first two workspace tour steps", () => {
    expect(topBar).toContain('data-tour="project-actions"');
    expect(topBar).toContain("'project-settings'");
    expect(topBar).not.toContain(':data-tour="isPrint ? \'print-actions\' : \'project-actions\'"');
    expect(leftNav).toContain('data-tour="project-list"');
    expect(leftNav).not.toContain('class="min-h-0 flex-1 overflow-auto" data-tour="project-list"');
  });
});
