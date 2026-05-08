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
  deleted_at?: string;
  deleted_by?: string;
}

interface ApiCategoryRecord {
  id: number;
  name: string;
  sort_order: number;
}

function adminHeaders(adminPassword: string | null | undefined) {
  return adminPassword
    ? {
        "X-Admin-Password": adminPassword
      }
    : undefined;
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
    updated_at: product.updated_at,
    deleted_at: product.deleted_at,
    deleted_by: product.deleted_by
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

export function listProducts(options: { deleted?: "active" | "only" | "all" } = {}) {
  const params = new URLSearchParams();
  if (options.deleted && options.deleted !== "active") {
    params.set("deleted", options.deleted);
  }
  const query = params.toString();
  return requestJson<ApiProductRecord[]>(`/api/products${query ? `?${query}` : ""}`).then((products) => products.map(fromApiProduct));
}

export function createProduct(product: ProductDraft, adminPassword?: string | null) {
  return requestJson<ApiProductRecord>("/api/products", {
    method: "POST",
    headers: adminHeaders(adminPassword),
    body: JSON.stringify(toApiProduct(product))
  }).then(fromApiProduct);
}

export function updateProduct(productId: string, product: ProductDraft, adminPassword?: string | null) {
  return requestJson<ApiProductRecord>(`/api/products/${productId}`, {
    method: "PUT",
    headers: adminHeaders(adminPassword),
    body: JSON.stringify(toApiProduct(product))
  }).then(fromApiProduct);
}

export function deleteProduct(productId: string, force = false, adminPassword?: string | null) {
  const forceParam = force ? "?force=true" : "";
  return requestJson<void>(`/api/products/${productId}${forceParam}`, {
    method: "DELETE",
    headers: adminHeaders(adminPassword)
  });
}

export function restoreProduct(productId: string, adminPassword?: string | null) {
  return requestJson<ApiProductRecord>(`/api/products/${productId}/restore`, {
    method: "POST",
    headers: adminHeaders(adminPassword)
  }).then(fromApiProduct);
}

export function listCategories() {
  return requestJson<ApiCategoryRecord[]>("/api/categories").then((categories) => categories.map((category) => category.name));
}

export function createCategory(name: string, adminPassword?: string | null) {
  return requestJson<ApiCategoryRecord>("/api/categories", {
    method: "POST",
    headers: adminHeaders(adminPassword),
    body: JSON.stringify({ name })
  }).then((category) => category.name);
}

export function verifyAdminPassword(adminPassword: string) {
  return requestJson<{ ok: boolean }>("/api/admin/verify", {
    method: "POST",
    headers: adminHeaders(adminPassword)
  });
}
