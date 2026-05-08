import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { applyDocumentLocale, i18n } from "./i18n";
import router from "./router";
import { registerServiceWorker } from "./pwa";
import "./styles.css";

const app = createApp(App);

app.use(createPinia());
app.use(i18n);
app.use(router);
applyDocumentLocale();
app.mount("#app");

registerServiceWorker();
