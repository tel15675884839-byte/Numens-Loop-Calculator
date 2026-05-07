export interface ProductRecord {
  id: string;
  category: string;
  factory_name: string;
  customer_name: string;
  product_name: string;
  standby: number;
  alarm: number;
  ledCost: number;
  type: string;
  built_in: boolean;
  created_at?: string;
  updated_at?: string;
  deleted_at?: string;
  deleted_by?: string;
}

export interface ProductFilters {
  search: string;
  category: string;
}

export interface ProductDraft {
  id?: string;
  category: string;
  factory_name: string;
  customer_name: string;
  product_name: string;
  standby: number;
  alarm: number;
  ledCost: number;
  type: string;
  built_in: boolean;
}
