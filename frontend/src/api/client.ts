const isDev = import.meta.env.DEV;
const DESKTOP_API_BASE_URL = "http://127.0.0.1:8765";

interface ApiBaseContext {
  isDev: boolean;
  origin: string;
  isTauri: boolean;
}

export function resolveApiBaseUrl(context: ApiBaseContext) {
  if (context.isTauri) {
    return DESKTOP_API_BASE_URL;
  }
  return context.isDev ? "http://127.0.0.1:8000" : context.origin;
}

const isTauri = window.location.protocol === "tauri:" || "__TAURI_INTERNALS__" in window;
const DEFAULT_API_BASE_URL = resolveApiBaseUrl({ isDev, origin: window.location.origin, isTauri });

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/+$/, "");

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {})
    }
  });

  if (!response.ok) {
    let details: unknown = null;
    try {
      details = await response.json();
    } catch {
      details = await response.text().catch(() => null);
    }
    throw new ApiError(`Request failed with status ${response.status}`, response.status, details);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
