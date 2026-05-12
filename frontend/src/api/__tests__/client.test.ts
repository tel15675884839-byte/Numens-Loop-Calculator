import { describe, expect, it } from "vitest";
import { resolveApiBaseUrl } from "../client";

describe("resolveApiBaseUrl", () => {
  it("uses the local desktop backend inside Tauri", () => {
    expect(resolveApiBaseUrl({ isDev: false, origin: "tauri://localhost", isTauri: true })).toBe("http://127.0.0.1:8765");
  });

  it("uses the current web origin for production web builds", () => {
    expect(resolveApiBaseUrl({ isDev: false, origin: "https://example.com", isTauri: false })).toBe("https://example.com");
  });
});
