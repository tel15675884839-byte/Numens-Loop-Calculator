import { requestJson } from "./client";
import type { ProjectListItem, ProjectRecord } from "../types/project";

export function listProjects() {
  return requestJson<ProjectListItem[]>("/api/projects");
}

export function getProject(projectId: string) {
  return requestJson<ProjectRecord>(`/api/projects/${projectId}`);
}

export function createProject(project: ProjectRecord) {
  return requestJson<ProjectRecord>("/api/projects", {
    method: "POST",
    body: JSON.stringify(project)
  });
}

export function updateProject(projectId: string, project: ProjectRecord) {
  return requestJson<ProjectRecord>(`/api/projects/${projectId}`, {
    method: "PUT",
    body: JSON.stringify(project)
  });
}

export function deleteProject(projectId: string) {
  return requestJson<void>(`/api/projects/${projectId}`, {
    method: "DELETE"
  });
}

export function createLoop(projectId: string, payload: ProjectRecord["loops"][number]) {
  return requestJson<ProjectRecord["loops"][number]>(`/api/projects/${projectId}/loops`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateLoop(projectId: string, loopId: string, payload: ProjectRecord["loops"][number]) {
  return requestJson<ProjectRecord["loops"][number]>(`/api/projects/${projectId}/loops/${loopId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteLoop(projectId: string, loopId: string) {
  return requestJson<void>(`/api/projects/${projectId}/loops/${loopId}`, {
    method: "DELETE"
  });
}
