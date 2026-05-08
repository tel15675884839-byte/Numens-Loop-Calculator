import { describe, expect, it, vi } from "vitest";

import {
  DEFAULT_LOCALE,
  LOCALE_STORAGE_KEY,
  SUPPORTED_LOCALES,
  getTextDirection,
  translateCategoryLabel,
  translateProductNameLabel,
  normalizeLocale,
  setLocale,
  translate
} from "../index";

describe("i18n", () => {
  it("supports the approved language set with English as the default", () => {
    expect(DEFAULT_LOCALE).toBe("en");
    expect(SUPPORTED_LOCALES.map((locale) => locale.code)).toEqual(["en", "ar", "ru", "de", "fr", "es"]);
  });

  it("normalizes unsupported locales to English", () => {
    expect(normalizeLocale("ar-EG")).toBe("ar");
    expect(normalizeLocale("de-DE")).toBe("de");
    expect(normalizeLocale("zh-CN")).toBe("en");
    expect(normalizeLocale(null)).toBe("en");
  });

  it("uses RTL only for Arabic", () => {
    expect(getTextDirection("ar")).toBe("rtl");
    expect(getTextDirection("ru")).toBe("ltr");
    expect(getTextDirection("de")).toBe("ltr");
  });

  it("persists selected locale and updates the document direction", () => {
    const setItem = vi.spyOn(Storage.prototype, "setItem");

    setLocale("ar");

    expect(setItem).toHaveBeenCalledWith(LOCALE_STORAGE_KEY, "ar");
    expect(document.documentElement.lang).toBe("ar");
    expect(document.documentElement.dir).toBe("rtl");
  });

  it("translates core labels for long-language UI checks", () => {
    expect(translate("de", "inspector.standbyLoad")).toBe("Ruhestrom");
    expect(translate("fr", "topBar.language")).toBe("Langue");
    expect(translate("es", "nav.deviceCatalog")).toBe("Catálogo");
    expect(translate("ru", "inspector.endVoltage")).toBe("Конечное напряжение");
    expect(translate("ar", "inspector.alarmLoad")).toBe("حمل الإنذار");
  });

  it("translates built-in category labels without changing their source values", () => {
    expect(translateCategoryLabel("de", "Detector")).toBe("Melder");
    expect(translateCategoryLabel("fr", "Sounder")).toBe("Sirène");
    expect(translateCategoryLabel("es", "I/O Module")).toBe("Módulo E/S");
    expect(translateCategoryLabel("ru", "Isolator")).toBe("Изолятор");
    expect(translateCategoryLabel("ar", "MCP")).toBe("نقطة نداء");
    expect(translateCategoryLabel("de", "Custom Category")).toBe("Custom Category");
  });

  it("translates built-in product names without changing model codes", () => {
    expect(translateProductNameLabel("de", "Manual Call Point")).toBe("Handmelder");
    expect(translateProductNameLabel("fr", "Heat Detector")).toBe("Détecteur de chaleur");
    expect(translateProductNameLabel("es", "Smoke Detector")).toBe("Detector de humo");
    expect(translateProductNameLabel("ru", "Input Module")).toBe("Модуль ввода");
    expect(translateProductNameLabel("ar", "Output Module")).toBe("وحدة إخراج");
    expect(translateProductNameLabel("de", "Custom Product 660-001")).toBe("Custom Product 660-001");
  });

  it("translates compound built-in product names by phrase", () => {
    expect(translateProductNameLabel("ru", "Heat Detector, Remote LED Output")).toBe("Тепловой детектор, выносной светодиодный выход");
    expect(translateProductNameLabel("ru", "Smoke/Heat Detector, Remote LED Output")).toBe("Дымовой/тепловой детектор, выносной светодиодный выход");
    expect(translateProductNameLabel("ru", "Alarm Zone Input Module, Externally Powered")).toBe("Модуль входа зоны тревоги, внешнее питание");
    expect(translateProductNameLabel("ru", "Input/Output Module, Twin Input/Outputs, Isolator")).toBe("Модуль ввода/вывода, два входа/выхода, изолятор");
    expect(translateProductNameLabel("ru", "Mains Switching Input/Output Module, Twin Input/Outputs, Isolator")).toBe("Модуль ввода/вывода коммутации сети, два входа/выхода, изолятор");
    expect(translateProductNameLabel("ru", "Mini Input Module, Single Contact Input")).toBe("Мини-модуль ввода, один контактный вход");
    expect(translateProductNameLabel("ru", "Sounder, Audible/Visual Alarm, Weatherproof")).toBe("Оповещатель, звуковая/световая тревога, погодозащищенный");
    expect(translateProductNameLabel("ru", "Manual Call Point, with Isolator")).toBe("Ручной извещатель, с изолятором");
    expect(translateProductNameLabel("ru", "Mini Input Module, Detector Input, without Enclosure")).toBe("Мини-модуль ввода, вход детектора, без корпуса");
    expect(translateProductNameLabel("ru", "Sounder, Audible Alarm, Red")).toBe("Оповещатель, звуковая тревога, красный");
    expect(translateProductNameLabel("ru", "Sounder, Audible/Visual Alarm Device, Red/White")).toBe("Оповещатель, устройство звуковой/световой тревоги, красный/белый");
  });
});
