import { mount } from "@vue/test-utils";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import PrintPageStack from "../PrintPageStack.vue";
import type { ProjectPrintProfile, ProjectRecord } from "../../../types/project";

const styles = readFileSync(resolve(process.cwd(), "src/styles.css"), "utf8");

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

const project: ProjectRecord = {
  id: "project-1",
  name: "Print Project",
  active_loop_id: "loop-1",
  print_profile: profile,
  loops: [
    {
      id: "loop-1",
      project_id: "project-1",
      name: "Loop 1",
      sort_order: 1,
      address_limit: 125,
      max_current_ma: 400,
      min_voltage_v: 17,
      cable_size: "1.5",
      cable_resistance_ohm_per_km: 12.1,
      aux_current_ma: 25,
      device_rows: [
        {
          id: "row-1",
          sort_order: 1,
          product_id: "product-0001",
          category: "MCP",
          display_name: "Manual Call Point",
          customer_name: "MCP-001",
          factory_name: "MCP-001",
          product_name: "Manual Call Point",
          standby_ma: 0.5,
          alarm_ma: 2.1,
          led_cost: 1,
          device_type: "MCP",
          lead_dist_m: 10,
          interval_dist_m: 0,
          qty: 2
        }
      ],
      calculation_result: {
        total_addresses: 2,
        total_current_ma: 29.2,
        total_distance_m: 10,
        voltage_drop_v: 0.01,
        end_voltage_v: 27.99,
        max_install_distance_m: 1000,
        recommended_cable_size: "1.0",
        recommended_cable_unit: "mm2",
        standby_current_ma: 26,
        alarm_current_ma: 29.2,
        diagnostics: ["Voltage margin is low"],
        addr_limit: 125,
        max_current_ma: 400,
        min_voltage_v: 17,
        cable_resistance_ohm_per_km: 12.1,
        panel_voltage_v: 28,
        max_cable_length_m: 1000
      }
    }
  ]
};

describe("PrintPageStack", () => {
  it("renders a project summary, loop report, diagnostics, and device schedule columns", () => {
    const wrapper = mount(PrintPageStack, {
      props: {
        project,
        profile
      }
    });

    expect(wrapper.text()).toContain("Project Summary");
    expect(wrapper.text()).toContain("NUM-2401");
    expect(wrapper.text()).toContain("North Plant");
    expect(wrapper.text()).toContain("Loop 1");
    expect(wrapper.text()).toContain("Voltage margin is low");
    expect(wrapper.text()).toContain("Device Schedule");
    expect(wrapper.text()).toContain("SBY / ea");
    expect(wrapper.text()).toContain("ALM / ea");
    expect(wrapper.text()).toContain("Lead");
    expect(wrapper.text()).toContain("Interval");
    expect(wrapper.text()).toContain("Manual Call Point");
  });

  it("keeps print pages and footers fixed inside the browser print page", () => {
    expect(styles).toContain("@page {\n  size: A4 portrait;\n  margin: 0;");
    expect(styles).toContain("height: 297mm;");
    expect(styles).toContain("padding: 12mm 12mm 25mm 12mm;");
    expect(styles).toContain(".print-page-footer");
    expect(styles).toContain("position: absolute;");
    expect(styles).toContain("bottom: 12mm;");
    expect(styles).not.toContain("width: auto;");
    expect(styles).not.toContain("min-height: auto;");
  });

  it("only enables two-column preview when the preview container can fit two A4 pages", () => {
    expect(styles).toContain("container-type: inline-size;");
    expect(styles).not.toContain("@media (min-width: 1440px)");
    expect(styles).toContain("@container print-preview (min-width: 450mm)");
    expect(styles).toContain("grid-template-columns: repeat(2, 210mm);");
  });
});
