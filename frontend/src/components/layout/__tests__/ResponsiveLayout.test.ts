import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const appShell = readFileSync(resolve(process.cwd(), "src/components/layout/AppShell.vue"), "utf8");
const workspaceView = readFileSync(resolve(process.cwd(), "src/views/WorkspaceView.vue"), "utf8");
const printPreviewView = readFileSync(resolve(process.cwd(), "src/views/PrintPreviewView.vue"), "utf8");
const topBar = readFileSync(resolve(process.cwd(), "src/components/layout/TopBar.vue"), "utf8");

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
});
