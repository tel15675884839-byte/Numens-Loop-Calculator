import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { ApiError } from "../api/client";
import { createCategory, createProduct, deleteProduct, listCategories, listProducts, restoreProduct, updateProduct, verifyAdminPassword } from "../api/products";
import { defaultProducts } from "../data/defaultProducts";
import type { ProductDraft, ProductFilters, ProductRecord } from "../types/product";
import { readJson, writeJson } from "../utils/storage";
import { createId } from "../utils/ids";

const PRODUCTS_CACHE_KEY = "loop-calculator.products";
const CATEGORIES_CACHE_KEY = "loop-calculator.categories";
const PRODUCTS_META_CACHE_KEY = "loop-calculator.products.meta";
const RETIRED_BUILT_IN_PRODUCT_IDS = new Set(["product-0013", "product-0014", "product-0015", "product-0016", "product-0017", "product-0018"]);
const RETIRED_BUILT_IN_PRODUCT_CODES = new Set(["600-001", "600-002", "600-003", "600-004", "600-005", "600-006"]);

interface ProductsCacheMeta {
  source: "api" | "seed";
  seedSignature: string | null;
}

const bundledCatalogSignature = JSON.stringify(defaultProducts);

function normalizeDraft(product: ProductDraft): ProductDraft {
  return {
    ...product,
    category: product.category.trim(),
    factory_name: product.factory_name.trim(),
    customer_name: product.customer_name.trim(),
    product_name: product.product_name.trim(),
    type: product.type.trim()
  };
}

function cloneProducts(products: ProductRecord[]) {
  return products.map((product) => ({ ...product }));
}

function isRetiredBuiltInProduct(product: ProductRecord) {
  return product.built_in
    && (RETIRED_BUILT_IN_PRODUCT_IDS.has(product.id)
      || RETIRED_BUILT_IN_PRODUCT_CODES.has(product.factory_name)
      || RETIRED_BUILT_IN_PRODUCT_CODES.has(product.customer_name));
}

function removeRetiredBuiltInProducts(items: ProductRecord[]) {
  return items.filter((product) => !isRetiredBuiltInProduct(product));
}

function mergeBundledProducts(cachedProducts: ProductRecord[]) {
  const customProducts = cachedProducts.filter((product) => !product.built_in);
  const bundledIds = new Set(defaultProducts.map((product) => product.id));
  const customOnly = customProducts.filter((product) => !bundledIds.has(product.id));
  return [...cloneProducts(removeRetiredBuiltInProducts(defaultProducts)), ...customOnly.map((product) => ({ ...product }))];
}

function shouldRefreshBundledProducts(meta: ProductsCacheMeta | null) {
  return !meta || (meta.source === "seed" && meta.seedSignature !== bundledCatalogSignature);
}

function isRejectedDelete(cause: unknown) {
  return typeof cause === "object"
    && cause !== null
    && "status" in cause
    && ((cause as { status?: unknown }).status === 403 || (cause as { status?: unknown }).status === 409);
}

function isHttpError(cause: unknown) {
  return cause instanceof ApiError;
}

export const useProductStore = defineStore("products", () => {
  const products = ref<ProductRecord[]>(cloneProducts(defaultProducts));
  const deletedProducts = ref<ProductRecord[]>([]);
  const categories = ref<string[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const filters = ref<ProductFilters>({ search: "", category: "All" });
  const editorOpen = ref(false);
  const activeId = ref<string | null>(null);
  const editorMode = ref<"new" | "edit">("edit");
  const statusMessage = ref<string>("Ready");
  const isAdmin = ref(false);
  const adminPassword = ref<string | null>(null);

  function setAdminAccess(password: string | null) {
    adminPassword.value = password;
    isAdmin.value = Boolean(password);
  }

  async function unlockAdmin(password: string) {
    await verifyAdminPassword(password);
    setAdminAccess(password);
  }

  const activeProduct = computed(() => products.value.find((product) => product.id === activeId.value) ?? null);

  const filteredProducts = computed(() => {
    const search = filters.value.search.trim().toLowerCase();
    const category = filters.value.category;
    return products.value.filter((product) => {
      if (category !== "All" && product.category !== category) {
        return false;
      }
      if (!search) {
        return true;
      }
      const haystack = [
        product.category,
        product.customer_name,
        product.factory_name,
        product.product_name,
        product.type
      ].join(" ").toLowerCase();
      return haystack.includes(search);
    });
  });

  function categoriesFromProducts(items: ProductRecord[]) {
    const seen = new Set<string>();
    const values: string[] = [];
    for (const item of items) {
      if (!seen.has(item.category)) {
        seen.add(item.category);
        values.push(item.category);
      }
    }
    return values;
  }

  function hydrateProducts(items: ProductRecord[], source: "api" | "cache" | "seed", metaSource: ProductsCacheMeta["source"] | null = source === "api" ? "api" : source === "seed" ? "seed" : null) {
    const activeItems = removeRetiredBuiltInProducts(items);
    products.value = cloneProducts(activeItems);
    categories.value = categoriesFromProducts(activeItems);
    statusMessage.value = source === "api" ? "Loaded" : source === "cache" ? "Cache" : "Seeded";
    writeJson(PRODUCTS_CACHE_KEY, activeItems);
    writeJson(CATEGORIES_CACHE_KEY, categories.value);
    if (metaSource) {
      writeJson(PRODUCTS_META_CACHE_KEY, {
        source: metaSource,
        seedSignature: metaSource === "seed" ? bundledCatalogSignature : null
      });
    }
  }

  async function bootstrap() {
    loading.value = true;
    error.value = null;

    const cachedProducts = readJson<ProductRecord[]>(PRODUCTS_CACHE_KEY);
    const cachedCategories = readJson<string[]>(CATEGORIES_CACHE_KEY);
    const cachedMeta = readJson<ProductsCacheMeta>(PRODUCTS_META_CACHE_KEY);

    try {
      const [remoteProducts, remoteCategories] = await Promise.all([
        listProducts(),
        listCategories().catch(() => null)
      ]);
      hydrateProducts(remoteProducts, "api");
      categories.value = remoteCategories?.length ? remoteCategories : categoriesFromProducts(remoteProducts);
      if (categories.value.length === 0 && cachedCategories?.length) {
        categories.value = cachedCategories;
      }
    } catch (cause) {
      if (cachedProducts?.length) {
        if (shouldRefreshBundledProducts(cachedMeta)) {
          hydrateProducts(mergeBundledProducts(cachedProducts), "cache", "seed");
        } else {
          hydrateProducts(cachedProducts, "cache", cachedMeta?.source ?? null);
        }
        if (cachedMeta?.source !== "seed" && cachedCategories?.length) {
          categories.value = categoriesFromProducts(products.value);
        }
      } else {
        hydrateProducts(defaultProducts, "seed");
      }
      error.value = cause instanceof Error ? cause.message : "Unable to load product library";
    } finally {
      loading.value = false;
    }
  }

  function setSearch(search: string) {
    filters.value.search = search;
  }

  function setCategory(category: string) {
    filters.value.category = category;
  }

  function openEditor(product: ProductRecord | null = null) {
    activeId.value = product?.id ?? createId("product");
    editorMode.value = "edit";
    editorOpen.value = true;
  }

  function closeEditor() {
    editorOpen.value = false;
    activeId.value = null;
  }

  function beginNewProduct(category = "") {
    const draft: ProductDraft = {
      category,
      factory_name: "",
      customer_name: "",
      product_name: "",
      standby: 0.5,
      alarm: 2,
      ledCost: 1,
      type: "",
      built_in: false
    };
    const tempId = createId("product");
    editorMode.value = "new";
    activeId.value = tempId;
    products.value = [
      ...products.value,
      {
        id: tempId,
        ...draft
      }
    ];
    editorOpen.value = true;
  }

  async function saveProduct(draft: ProductDraft) {
    const normalized = normalizeDraft(draft);
    try {
      const payload = { ...normalized };
      const isUpdate = editorMode.value === "edit" && Boolean(normalized.id) && products.value.some((product) => product.id === normalized.id);
      const result = isUpdate && normalized.id
        ? await updateProduct(normalized.id, payload, adminPassword.value)
        : await createProduct(payload, adminPassword.value);
      if (isUpdate && normalized.id) {
        products.value = products.value.map((product) => (product.id === normalized.id ? result : product));
      } else if (normalized.id && products.value.some((product) => product.id === normalized.id)) {
        products.value = products.value.map((product) => (product.id === normalized.id ? result : product));
      } else {
        products.value = [...products.value.filter((product) => product.id !== normalized.id), result];
      }
      categories.value = categoriesFromProducts(products.value);
      writeJson(PRODUCTS_CACHE_KEY, products.value);
      writeJson(CATEGORIES_CACHE_KEY, categories.value);
      activeId.value = result.id;
      editorMode.value = "edit";
      editorOpen.value = true;
      statusMessage.value = "Saved";
      return result;
    } catch (cause) {
      if (isHttpError(cause)) {
        statusMessage.value = "Save rejected";
        error.value = cause.message;
        throw cause;
      }
      const record: ProductRecord = {
        id: normalized.id ?? createId("product"),
        ...normalized
      };
      products.value = products.value.some((product) => product.id === record.id)
        ? products.value.map((product) => (product.id === record.id ? record : product))
        : [...products.value.filter((product) => product.id !== record.id), record];
      categories.value = categoriesFromProducts(products.value);
      writeJson(PRODUCTS_CACHE_KEY, products.value);
      writeJson(CATEGORIES_CACHE_KEY, categories.value);
      activeId.value = record.id;
      editorMode.value = "edit";
      editorOpen.value = true;
      statusMessage.value = "Saved locally";
      error.value = "Backend unavailable; product saved locally only.";
      return record;
    }
  }

  async function removeProduct(product: ProductRecord, force = false) {
    if (product.built_in && !force) {
      return { removed: false, message: "Built-in products are protected." };
    }
    try {
      await deleteProduct(product.id, force, adminPassword.value);
    } catch (cause) {
      if (isRejectedDelete(cause)) {
        statusMessage.value = "Delete rejected";
        return { removed: false, message: "Backend rejected product deletion." };
      }
      if (isHttpError(cause)) {
        statusMessage.value = "Delete rejected";
        error.value = cause.message;
        return { removed: false, message: "Backend rejected product deletion." };
      }
      error.value = "Backend unavailable; product deleted locally only.";
    }
    products.value = products.value.filter((item) => item.id !== product.id);
    deletedProducts.value = [
      { ...product, deleted_at: product.deleted_at || new Date().toISOString() },
      ...deletedProducts.value.filter((item) => item.id !== product.id)
    ];
    categories.value = categoriesFromProducts(products.value);
    writeJson(PRODUCTS_CACHE_KEY, products.value);
    writeJson(CATEGORIES_CACHE_KEY, categories.value);
    if (activeId.value === product.id) {
      closeEditor();
    }
    statusMessage.value = "Deleted";
    return { removed: true, message: "Product removed." };
  }

  async function loadDeletedProducts() {
    deletedProducts.value = await listProducts({ deleted: "only" });
    statusMessage.value = "Deleted products loaded";
    return deletedProducts.value;
  }

  async function restoreProductRecord(productId: string) {
    const restored = await restoreProduct(productId, adminPassword.value);
    products.value = products.value.some((product) => product.id === restored.id)
      ? products.value.map((product) => (product.id === restored.id ? restored : product))
      : [...products.value, restored];
    deletedProducts.value = deletedProducts.value.filter((product) => product.id !== restored.id);
    categories.value = categoriesFromProducts(products.value);
    writeJson(PRODUCTS_CACHE_KEY, products.value);
    writeJson(CATEGORIES_CACHE_KEY, categories.value);
    statusMessage.value = "Restored";
    return { restored: true, message: "Product restored." };
  }

  async function addCategory(name: string) {
    const trimmed = name.trim();
    if (!trimmed || categories.value.includes(trimmed)) {
      return trimmed;
    }
    try {
      await createCategory(trimmed, adminPassword.value);
    } catch (cause) {
      if (isHttpError(cause)) {
        statusMessage.value = "Category rejected";
        error.value = cause.message;
        throw cause;
      }
      error.value = "Backend unavailable; category cached locally only.";
    }
    categories.value = [...categories.value, trimmed];
    writeJson(CATEGORIES_CACHE_KEY, categories.value);
    return trimmed;
  }

  function draftFromProduct(product: ProductRecord): ProductDraft {
    return { ...product };
  }

  function getProduct(productId: string | null | undefined) {
    return products.value.find((product) => product.id === productId) ?? null;
  }

  return {
    products,
    deletedProducts,
    categories,
    loading,
    error,
    filters,
    editorOpen,
    activeProduct,
    filteredProducts,
    statusMessage,
    editorMode,
    setAdminAccess,
    unlockAdmin,
    bootstrap,
    setSearch,
    setCategory,
    openEditor,
    closeEditor,
    beginNewProduct,
    saveProduct,
    removeProduct,
    loadDeletedProducts,
    restoreProductRecord,
    addCategory,
    draftFromProduct,
    getProduct,
    isAdmin
  };
});
