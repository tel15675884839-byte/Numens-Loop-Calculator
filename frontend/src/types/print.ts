import type { ProjectPrintProfile } from "./project";

export const REQUIRED_PRINT_PROFILE_FIELDS: Array<keyof ProjectPrintProfile> = [
  "project_no",
  "customer",
  "revision",
  "prepared_by",
  "issue_date"
];

export function createBlankPrintProfile(issueDate: string): ProjectPrintProfile {
  return {
    project_no: "",
    customer: "",
    site: "",
    panel: "",
    revision: "",
    prepared_by: "",
    issue_date: issueDate,
    notes: ""
  };
}

export function hasRequiredPrintProfileFields(profile: ProjectPrintProfile | null) {
  return profile !== null && REQUIRED_PRINT_PROFILE_FIELDS.every((field) => profile[field].trim().length > 0);
}
