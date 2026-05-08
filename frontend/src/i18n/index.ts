import { createI18n } from "vue-i18n";
import { computed } from "vue";
import { messages, type MessageSchema } from "./messages";

export type LocaleCode = keyof typeof messages;

export const DEFAULT_LOCALE: LocaleCode = "en";
export const LOCALE_STORAGE_KEY = "loop-calculator.locale";

export const SUPPORTED_LOCALES: Array<{ code: LocaleCode; label: string; nativeLabel: string }> = [
  { code: "en", label: "English", nativeLabel: "English" },
  { code: "ar", label: "Arabic", nativeLabel: "العربية" },
  { code: "ru", label: "Russian", nativeLabel: "Русский" },
  { code: "de", label: "German", nativeLabel: "Deutsch" },
  { code: "fr", label: "French", nativeLabel: "Français" },
  { code: "es", label: "Spanish", nativeLabel: "Español" }
];

export function normalizeLocale(locale: string | null | undefined): LocaleCode {
  if (!locale) return DEFAULT_LOCALE;
  const normalized = locale.toLowerCase().split("-")[0];
  return isLocaleCode(normalized) ? normalized : DEFAULT_LOCALE;
}

export function getTextDirection(locale: LocaleCode) {
  return locale === "ar" ? "rtl" : "ltr";
}

export const i18n = createI18n<[MessageSchema], LocaleCode>({
  legacy: false,
  locale: initialLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages
});

export function setLocale(locale: LocaleCode) {
  i18n.global.locale.value = locale;
  window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  applyDocumentLocale(locale);
}

export function applyDocumentLocale(locale: LocaleCode = i18n.global.locale.value) {
  document.documentElement.lang = locale;
  document.documentElement.dir = getTextDirection(locale);
}

export function translate(locale: LocaleCode, key: string) {
  return i18n.global.t(key, {}, { locale });
}

export function translateMessage(key: string, values?: Record<string, string | number>) {
  return i18n.global.t(key, values ?? {});
}

export function useTranslation() {
  return {
    locale: computed(() => i18n.global.locale.value),
    selectedLocale: computed({
      get: () => i18n.global.locale.value,
      set: (locale: LocaleCode) => setLocale(locale)
    }),
    t: translateMessage
  };
}

function initialLocale() {
  return normalizeLocale(window.localStorage.getItem(LOCALE_STORAGE_KEY) ?? navigator.language);
}

function isLocaleCode(locale: string): locale is LocaleCode {
  return Object.prototype.hasOwnProperty.call(messages, locale);
}
