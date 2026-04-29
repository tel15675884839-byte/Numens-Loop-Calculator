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
      />

      <ProductTable
        :products="productStore.filteredProducts"
        :isAdmin="productStore.isAdmin"
        @save="saveProductInTable"
        @delete="confirmDelete"
      />
    </div>

    <ProductEditorDrawer
      :open="productStore.editorOpen"
      :draft="draft"
      :categories="productStore.categories"
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
import { useDialogStore } from "../stores/dialogStore";
import { useProductStore } from "../stores/productStore";
import type { ProductDraft, ProductRecord } from "../types/product";

const dialog = useDialogStore();
const productStore = useProductStore();
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
    productStore.isAdmin = false;
    return;
  }
  const pwd = await dialog.prompt({
    title: "Administrator Access",
    message: "Please enter the admin password to unlock edit permissions:",
    initialValue: "",
    confirmLabel: "Unlock"
  });
  if (pwd === "numens888") {
    productStore.isAdmin = true;
  } else if (pwd !== null) {
    await dialog.alert({
      title: "Access Denied",
      message: "Incorrect password."
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
    title: "Delete product",
    message: `Delete ${current.product_name || current.customer_name || current.id}?`,
    confirmLabel: "Delete"
  });
  if (!confirmed) {
    return;
  }
  await productStore.removeProduct(current, false);
}

async function confirmDelete(product: ProductRecord) {
  if (product.built_in) {
    await dialog.alert({
      title: "Protected product",
      message: "Built-in products are protected."
    });
    return;
  }
  const confirmed = await dialog.confirm({
    title: "Delete product",
    message: `Delete ${product.product_name || product.customer_name || product.id}?`,
    confirmLabel: "Delete"
  });
  if (confirmed) {
    void productStore.removeProduct(product, true);
  }
}
</script>
