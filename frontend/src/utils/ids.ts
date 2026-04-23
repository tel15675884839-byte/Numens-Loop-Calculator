export function createId(prefix: string) {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  const stamp = Math.random().toString(36).slice(2, 10);
  return `${prefix}-${Date.now().toString(36)}-${stamp}`;
}
