<template>
  <div class="relative h-full min-h-0 overflow-hidden px-4 py-4">
    <div class="space-y-4">
      <ProductFilters
        :search="productStore.filters.search"
        :category="productStore.filters.category"
        :categories="productStore.categories"
        :total="productStore.filteredProducts.length"
        @create="productStore.beginNewProduct"
        @update:search="productStore.setSearch"
        @update:category="productStore.setCategory"
      />
      <ProductTable
        :products="productStore.filteredProducts"
        @edit="openEditor"
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
import { useProductStore } from "../stores/productStore";
import type { ProductDraft, ProductRecord } from "../types/product";

const productStore = useProductStore();
const draft = ref<ProductDraft>({
  category: "Detector",
  factory_name: "",
  customer_name: "",
  product_name: "",
  standby: 0.5,
  alarm: 2,
  ledCost: 1,
  type: "Detector",
  built_in: false
});

const activeProduct = computed(() => productStore.activeProduct);

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

async function saveProduct() {
  await productStore.saveProduct(draft.value);
}

async function deleteProduct() {
  const current = productStore.activeProduct;
  if (!current) {
    return;
  }
  const confirmed = window.confirm(`Delete ${current.product_name || current.customer_name || current.id}?`);
  if (!confirmed) {
    return;
  }
  await productStore.removeProduct(current, false);
}

function confirmDelete(product: ProductRecord) {
  if (product.built_in) {
    window.alert("Built-in products are protected.");
    return;
  }
  void productStore.removeProduct(product, window.confirm(`Delete ${product.product_name || product.customer_name || product.id}?`));
}
</script>
