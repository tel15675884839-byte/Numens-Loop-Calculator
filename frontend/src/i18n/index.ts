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

export function translateCategoryLabel(locale: LocaleCode, category: string) {
  const key = CATEGORY_KEYS[category.trim().toLowerCase()];
  return key ? translate(locale, key) : category;
}

export function translateProductNameLabel(locale: LocaleCode, productName: string) {
  const trimmed = productName.trim();
  const directKey = PRODUCT_NAME_KEYS[trimmed.toLowerCase()];
  if (directKey) return translate(locale, directKey);

  const sourceParts = trimmed.split(",").map((part) => part.trim());
  const translatedParts = sourceParts.map((part) => {
    const key = PRODUCT_NAME_KEYS[part.toLowerCase()];
    return key ? translate(locale, key) : part;
  });
  const hasTranslation = translatedParts.some((part, index) => part !== sourceParts[index]);
  return hasTranslation ? translatedParts.join(", ") : productName;
}

export function translateCurrentCategoryLabel(category: string) {
  return translateCategoryLabel(i18n.global.locale.value, category);
}

export function translateCurrentProductNameLabel(productName: string) {
  return translateProductNameLabel(i18n.global.locale.value, productName);
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

const CATEGORY_KEYS: Record<string, string> = {
  detector: "categories.detector",
  sounder: "categories.sounder",
  mcp: "categories.mcp",
  "i/o module": "categories.ioModule",
  isolator: "categories.isolator"
};

const PRODUCT_NAME_KEYS: Record<string, string> = {
  "alarm zone input module": "productNames.alarmZoneInputModule",
  "audio/visual alarm control module": "productNames.audioVisualAlarmControlModule",
  "audible alarm": "productNames.audibleAlarm",
  "audible/visual alarm": "productNames.audibleVisualAlarm",
  "audible/visual alarm device": "productNames.audibleVisualAlarmDevice",
  "audible/visual alarm/visual alarm device": "productNames.audibleVisualAlarmVisualAlarmDevice",
  "detector input": "productNames.detectorInput",
  "externally powered": "productNames.externallyPowered",
  "heat detector": "productNames.heatDetector",
  "isolator monitored input": "productNames.isolatorMonitoredInput",
  "input/output module": "productNames.inputOutputModule",
  "input module": "productNames.inputModule",
  "isolator": "productNames.isolator",
  lsm: "productNames.lsm",
  "loop isolator": "productNames.loopIsolator",
  "loop powered": "productNames.loopPowered",
  "mains switching input/output module": "productNames.mainsSwitchingInputOutputModule",
  "manual call point": "productNames.manualCallPoint",
  "mini input module": "productNames.miniInputModule",
  "mini output module": "productNames.miniOutputModule",
  "output module": "productNames.outputModule",
  red: "productNames.red",
  "red/white": "productNames.redWhite",
  "remote led output": "productNames.remoteLedOutput",
  "single contact input": "productNames.singleContactInput",
  "single detector input": "productNames.singleDetectorInput",
  "single input": "productNames.singleInput",
  "single input monitored": "productNames.singleInputMonitored",
  "single input/output": "productNames.singleInputOutput",
  "single output": "productNames.singleOutput",
  "smoke detector": "productNames.smokeDetector",
  "smoke/heat detector": "productNames.smokeHeatDetector",
  sounder: "productNames.sounder",
  "switched external dc supply": "productNames.switchedExternalDcSupply",
  "twin inputs": "productNames.twinInputs",
  "twin input/outputs": "productNames.twinInputOutputs",
  "visual alarm": "productNames.visualAlarm",
  "visual alarm/audio alarm device": "productNames.visualAlarmAudioAlarmDevice",
  weatherproof: "productNames.weatherproof",
  white: "productNames.white",
  "with isolator": "productNames.withIsolator",
  "with output relay": "productNames.withOutputRelay",
  "without enclosure": "productNames.withoutEnclosure"
};
