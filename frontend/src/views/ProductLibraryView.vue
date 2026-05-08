<template>
  <div class="relative h-full min-h-0 overflow-y-auto px-4 py-4">
    <div class="space-y-6">
      <ProductFilters
        :search="productStore.filters.search"
        :category="productStore.filters.category"
        :categories="categoriesWithProducts"
        :total="productStore.filteredProducts.length"
        :isAdmin="productStore.isAdmin"
        @create="productStore.beginNewProduct"
        @update:search="productStore.setSearch"
        @update:category="productStore.setCategory"
        @adminUnlock="handleAdminUnlock"
        @openDeletedProducts="openRecoveryPanel"
      />

      <ProductTable
        :products="productStore.filteredProducts"
        :isAdmin="productStore.isAdmin"
        @save="saveProductInTable"
        @delete="confirmDelete"
      />

      <section v-if="recoveryOpen && productStore.isAdmin" class="panel">
        <div class="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">{{ t("products.deletedProducts") }}</p>
            <p class="text-sm text-zinc-600">{{ productStore.deletedProducts.length }} {{ t("products.productsRestoreCount") }}</p>
          </div>
          <button class="toolbar-button px-3 py-1.5 text-xs" @click="recoveryOpen = false">{{ t("products.close") }}</button>
        </div>
        <div v-if="productStore.deletedProducts.length" class="divide-y divide-zinc-200">
          <div
            v-for="product in productStore.deletedProducts"
            :key="product.id"
            class="flex items-center justify-between gap-4 px-4 py-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-zinc-900">{{ product.product_name || product.customer_name || product.id }}</p>
              <p class="truncate text-xs text-zinc-500">{{ product.category }} · {{ product.factory_name }}</p>
              <p v-if="product.deleted_at" class="text-xs text-zinc-400">{{ t("products.deleted") }} {{ product.deleted_at }}</p>
            </div>
            <button class="toolbar-button-primary px-3 py-1.5 text-xs" @click="restoreDeletedProduct(product.id)">
              {{ t("products.restore") }}
            </button>
          </div>
        </div>
        <div v-else class="px-4 py-6 text-sm text-zinc-500">{{ t("products.noDeletedProducts") }}</div>
      </section>
    </div>

    <ProductEditorDrawer
      :open="productStore.editorOpen"
      :draft="draft"
      :categories="productStore.categories"
      :isAdmin="productStore.isAdmin"
      @close="productStore.closeEditor"
      @save="saveProduct"
      @delete="deleteProduct"
      @patch="patchDraft"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import ProductEditorDrawer from "../components/products/ProductEditorDrawer.vue";
import ProductFilters from "../components/products/ProductFilters.vue";
import ProductTable from "../components/products/ProductTable.vue";
import { translateMessage as t } from "../i18n";
import { useDialogStore } from "../stores/dialogStore";
import { useProductStore } from "../stores/productStore";
import type { ProductDraft, ProductRecord } from "../types/product";

const dialog = useDialogStore();
const productStore = useProductStore();
const recoveryOpen = ref(false);
const draft = ref<ProductDraft>({
  category: "",
  factory_name: "",
  customer_name: "",
  product_name: "",
  standby: 0.5,
  alarm: 2,
  ledCost: 1,
  type: "",
  built_in: false
});

const activeProduct = computed(() => productStore.activeProduct);

// Compute categories that actually have products
const categoriesWithProducts = computed(() => {
  const seen = new Set<string>();
  const values: string[] = [];
  for (const product of productStore.products) {
    if (product.category && !seen.has(product.category)) {
      seen.add(product.category);
      values.push(product.category);
    }
  }
  return values;
});

onMounted(() => {
  void productStore.bootstrap();
});

watch(
  activeProduct,
  (product) => {
    if (product) {
      draft.value = productStore.draftFromProduct(product);
      return;
    }
    draft.value = {
      category: productStore.categories[0] ?? "Detector",
      factory_name: "",
      customer_name: "",
      product_name: "",
      standby: 0.5,
      alarm: 2,
      ledCost: 1,
      type: productStore.categories[0] ?? "Detector",
      built_in: false
    };
  },
  { immediate: true }
);

function openEditor(product: ProductRecord) {
  productStore.openEditor(product);
}

function patchDraft(patch: Partial<ProductDraft>) {
  draft.value = {
    ...draft.value,
    ...patch
  };
}

async function handleAdminUnlock() {
  if (productStore.isAdmin) {
    productStore.setAdminAccess(null);
    return;
  }
  const pwd = await dialog.prompt({
    title: t("products.adminAccess"),
    message: t("products.unlockMessage"),
    initialValue: "",
    confirmLabel: t("products.unlock")
  });
  if (pwd === null) {
    return;
  }
  try {
    await productStore.unlockAdmin(pwd);
  } catch {
    await dialog.alert({
      title: t("products.accessDenied"),
      message: t("products.incorrectPassword")
    });
  }
}

async function saveProduct() {
  await productStore.saveProduct(draft.value);
  productStore.closeEditor();
}

async function saveProductInTable(product: ProductRecord) {
  // Overwrite local mode to edit before updating
  productStore.editorMode = "edit";
  await productStore.saveProduct(product);
}

async function deleteProduct() {
  const current = productStore.activeProduct;
  if (!current) {
    return;
  }
  const confirmed = await dialog.confirm({
    title: t("products.deleteProduct"),
    message: `Delete ${current.product_name || current.customer_name || current.id}?`,
    confirmLabel: t("common.delete")
  });
  if (!confirmed) {
    return;
  }
  await productStore.removeProduct(current, productStore.isAdmin);
  if (recoveryOpen.value) {
    await productStore.loadDeletedProducts();
  }
}

async function confirmDelete(product: ProductRecord) {
  if (product.built_in && !productStore.isAdmin) {
    await dialog.alert({
      title: t("products.protectedProduct"),
      message: t("products.builtInProtected")
    });
    return;
  }
  const confirmed = await dialog.confirm({
    title: t("products.deleteProduct"),
    message: `Delete ${product.product_name || product.customer_name || product.id}?`,
    confirmLabel: t("common.delete")
  });
  if (confirmed) {
    await productStore.removeProduct(product, productStore.isAdmin);
    if (recoveryOpen.value) {
      await productStore.loadDeletedProducts();
    }
  }
}

async function openRecoveryPanel() {
  recoveryOpen.value = true;
  await productStore.loadDeletedProducts();
}

async function restoreDeletedProduct(productId: string) {
  await productStore.restoreProductRecord(productId);
}
</script>
