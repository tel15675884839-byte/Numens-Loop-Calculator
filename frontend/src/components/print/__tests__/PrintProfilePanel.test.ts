import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";

import PrintProfilePanel from "../PrintProfilePanel.vue";
import { usePrintStore } from "../../../stores/printStore";
import type { ProjectPrintProfile } from "../../../types/project";

const profile: ProjectPrintProfile = {
  project_no: "NUM-2401",
  customer: "North Plant",
  site: "Zone A",
  panel: "FACP-01",
  revision: "A",
  prepared_by: "Engineering",
  issue_date: "2026-04-30",
  notes: "Issued for review"
};

describe("PrintProfilePanel", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.localStorage.clear();
  });

  it("shows only larger template choices until a template is selected", async () => {
    const print = usePrintStore();
    print.draftProfile = { ...profile };
    print.editingProfile = { ...profile };
    print.saveAsTemplate("First Template");
    print.editingProfile = { ...profile, project_no: "NUM-2402" };
    print.saveAsTemplate("Second Template");
    print.selectedTemplateName = null;

    const wrapper = mount(PrintProfilePanel, {
      props: { profile }
    });

    expect(wrapper.text()).toContain("Saved Templates");
    expect(wrapper.text()).toContain("First Template");
    expect(wrapper.text()).toContain("Second Template");
    expect(wrapper.text()).not.toContain("Project No");
    expect(wrapper.text()).toContain("新增");
    expect(wrapper.text()).not.toContain("保存");

    await wrapper.get("button[data-template-name='First Template']").trigger("click");

    expect(wrapper.text()).toContain("Project No");
    expect(wrapper.text()).toContain("保存");
    expect(wrapper.text()).toContain("清空");
    expect(wrapper.text()).toContain("删除");
  });
});
