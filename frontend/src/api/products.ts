import { requestJson } from "./client";
import type { ProductDraft, ProductRecord } from "../types/product";

interface ApiProductRecord {
  id: string;
  category: string;
  factory_name: string;
  customer_name: string;
  product_name: string;
  standby_ma: number;
  alarm_ma: number;
  led_cost: number;
  device_type: string;
  built_in: boolean;
  created_at?: string;
  updated_at?: string;
}

interface ApiCategoryRecord {
  id: number;
  name: string;
  sort_order: number;
}

function fromApiProduct(product: ApiProductRecord): ProductRecord {
  return {
    id: product.id,
    category: product.category,
    factory_name: product.factory_name,
    customer_name: product.customer_name,
    product_name: product.product_name,
    standby: product.standby_ma,
    alarm: product.alarm_ma,
    ledCost: product.led_cost,
    type: product.device_type,
    built_in: product.built_in,
    created_at: product.created_at,
    updated_at: product.updated_at
  };
}

function toApiProduct(product: ProductDraft) {
  return {
    id: product.id,
    category: product.category,
    factory_name: product.factory_name,
    customer_name: product.customer_name,
    product_name: product.product_name,
    standby_ma: product.standby,
    alarm_ma: product.alarm,
    led_cost: product.ledCost,
    device_type: product.type,
    built_in: product.built_in
  };
}

export function listProducts() {
  return requestJson<ApiProductRecord[]>("/api/products").then((products) => products.map(fromApiProduct));
}

export function createProduct(product: ProductDraft) {
  return requestJson<ApiProductRecord>("/api/products", {
    method: "POST",
    body: JSON.stringify(toApiProduct(product))
  }).then(fromApiProduct);
}

export function updateProduct(productId: string, product: ProductDraft) {
  return requestJson<ApiProductRecord>(`/api/products/${productId}`, {
    method: "PUT",
    body: JSON.stringify(toApiProduct(product))
  }).then(fromApiProduct);
}

export function deleteProduct(productId: string) {
  return requestJson<void>(`/api/products/${productId}`, {
    method: "DELETE"
  });
}

export function listCategories() {
  return requestJson<ApiCategoryRecord[]>("/api/categories").then((categories) => categories.map((category) => category.name));
}

export function createCategory(name: string) {
  return requestJson<ApiCategoryRecord>("/api/categories", {
    method: "POST",
    body: JSON.stringify({ name })
  }).then((category) => category.name);
}
