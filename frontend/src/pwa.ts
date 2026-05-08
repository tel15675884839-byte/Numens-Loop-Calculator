export function registerServiceWorker() {
  if (import.meta.env.DEV || !("serviceWorker" in navigator)) {
    return;
  }

  const isSecureContext = window.location.protocol === "https:" || window.location.hostname === "localhost";
  if (!isSecureContext) {
    return;
  }

  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Offline support is best-effort; the app still works without service worker support.
    });
  });
}
