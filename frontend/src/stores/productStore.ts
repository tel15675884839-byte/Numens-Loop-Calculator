import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { createCategory, createProduct, deleteProduct, listCategories, listProducts, updateProduct } from "../api/products";
import { defaultProducts } from "../data/defaultProducts";
import type { ProductDraft, ProductFilters, ProductRecord } from "../types/product";
import { readJson, writeJson } from "../utils/storage";
import { createId } from "../utils/ids";

const PRODUCTS_CACHE_KEY = "loop-calculator.products";
const CATEGORIES_CACHE_KEY = "loop-calculator.categories";

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

export const useProductStore = defineStore("products", () => {
  const products = ref<ProductRecord[]>(cloneProducts(defaultProducts));
  const categories = ref<string[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const filters = ref<ProductFilters>({ search: "", category: "All" });
  const editorOpen = ref(false);
  const activeId = ref<string | null>(null);
  const editorMode = ref<"new" | "edit">("edit");
  const statusMessage = ref<string>("Ready");

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

  function hydrateProducts(items: ProductRecord[], source: "api" | "cache" | "seed") {
    products.value = cloneProducts(items);
    categories.value = categoriesFromProducts(items);
    statusMessage.value = source === "api" ? "Loaded" : source === "cache" ? "Cache" : "Seeded";
    writeJson(PRODUCTS_CACHE_KEY, items);
    writeJson(CATEGORIES_CACHE_KEY, categories.value);
  }

  async function bootstrap() {
    loading.value = true;
    error.value = null;

    const cachedProducts = readJson<ProductRecord[]>(PRODUCTS_CACHE_KEY);
    const cachedCategories = readJson<string[]>(CATEGORIES_CACHE_KEY);

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
        hydrateProducts(cachedProducts, "cache");
        if (cachedCategories?.length) {
          categories.value = cachedCategories;
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
        ? await updateProduct(normalized.id, payload)
        : await createProduct(payload);
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
    } catch {
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
      return record;
    }
  }

  async function removeProduct(product: ProductRecord, force = false) {
    if (product.built_in && !force) {
      return { removed: false, message: "Built-in products are protected." };
    }
    try {
      await deleteProduct(product.id);
    } catch {
      // Fall back to local deletion when the API is unavailable.
    }
    products.value = products.value.filter((item) => item.id !== product.id);
    categories.value = categoriesFromProducts(products.value);
    writeJson(PRODUCTS_CACHE_KEY, products.value);
    writeJson(CATEGORIES_CACHE_KEY, categories.value);
    if (activeId.value === product.id) {
      closeEditor();
    }
    statusMessage.value = "Deleted";
    return { removed: true, message: "Product removed." };
  }

  async function addCategory(name: string) {
    const trimmed = name.trim();
    if (!trimmed || categories.value.includes(trimmed)) {
      return trimmed;
    }
    try {
      await createCategory(trimmed);
    } catch {
      // Cache only when the backend is not present.
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
    categories,
    loading,
    error,
    filters,
    editorOpen,
    activeProduct,
    filteredProducts,
    statusMessage,
    editorMode,
    bootstrap,
    setSearch,
    setCategory,
    openEditor,
    closeEditor,
    beginNewProduct,
    saveProduct,
    removeProduct,
    addCategory,
    draftFromProduct,
    getProduct
  };
});
