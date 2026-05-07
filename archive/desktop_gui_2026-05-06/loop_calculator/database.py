"""Product database persistence and normalization helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .constants import MODULE_CATEGORY_ALIASES, MODULE_CATEGORY_NAME, PRODUCT_DB_BACKUP_FILENAME, PRODUCT_DB_FILENAME


def resolve_product_db_path(base_dir: str | Path) -> Path:
    return Path(base_dir) / PRODUCT_DB_FILENAME


def resolve_legacy_products_path(base_dir: str | Path) -> Path:
    return Path(base_dir) / "devices_new.json"


class ProductDatabase:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.path = resolve_product_db_path(self.base_dir)
        self.backup_path = self.base_dir / PRODUCT_DB_BACKUP_FILENAME
        self.products: list[dict[str, Any]] = []
        self.extra_categories: list[str] = []
        self._merged_options: dict[str, list[dict[str, Any]]] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._migrate_from_legacy()
        with self.path.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
        self.products = [self._normalize_product(dict(product)) for product in data.get("products", [])]
        self.extra_categories = self._normalize_categories(data.get("categories", []))
        self._merged_options = self._build_merged_options()
        self._ensure_default_backup()
        self.save()

    def _normalize_product(self, product: dict[str, Any]) -> dict[str, Any]:
        if product.get("category") in MODULE_CATEGORY_ALIASES:
            product["category"] = MODULE_CATEGORY_NAME
        if product.get("type") in MODULE_CATEGORY_ALIASES:
            product["type"] = MODULE_CATEGORY_NAME
        if "built_in" not in product:
            product["built_in"] = True
        return product

    def _migrate_from_legacy(self) -> None:
        legacy_path = resolve_legacy_products_path(self.base_dir)
        products: list[dict[str, Any]] = []
        if legacy_path.exists():
            with legacy_path.open("r", encoding="utf-8-sig") as f:
                legacy = json.load(f)
            for index, item in enumerate(legacy, start=1):
                name = item.get("name", f"Product {index}")
                category = item.get("type", "Other")
                products.append(
                    self._normalize_product(
                        {
                            "id": f"product-{index:04d}",
                            "category": category,
                            "factory_name": name,
                            "customer_name": name,
                            "standby": float(item.get("standby", 0.5)),
                            "alarm": float(item.get("alarm", 2.0)),
                            "ledCost": int(item.get("ledCost", 1)),
                            "type": category,
                        }
                    )
                )
        else:
            products = [
                self._normalize_product(
                    {
                        "id": "product-0001",
                        "category": "Detector",
                        "factory_name": "Generic Device",
                        "customer_name": "Generic Device",
                        "standby": 0.5,
                        "alarm": 2.0,
                        "ledCost": 1,
                        "type": "Detector",
                    }
                )
            ]
        self.products = products
        self.save()

    def save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump({"categories": self.extra_categories, "products": self.products}, f, ensure_ascii=False, indent=2)

    def categories(self) -> list[str]:
        seen: list[str] = []
        for category in self.extra_categories:
            if category not in seen:
                seen.append(category)
        for product in self.products:
            category = product.get("category", "Other")
            if category not in seen:
                seen.append(category)
        order_map = {"Detector": 0, "MCP": 1, "Sounder": 2, "I/O Module": 3, "Isolator": 4}
        return sorted(seen, key=lambda value: order_map.get(value, 999))

    def add_category(self, name: str) -> None:
        normalized = self._normalize_category(name)
        if not normalized:
            return
        if normalized not in self.extra_categories:
            self.extra_categories.append(normalized)
            self.save()

    def restore_default_products(self) -> None:
        if not self.backup_path.exists():
            self._ensure_default_backup(force=True)
        try:
            with self.backup_path.open("r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            # Backup might be corrupted or saved with incompatible content; rebuild once.
            self._ensure_default_backup(force=True)
            with self.backup_path.open("r", encoding="utf-8-sig") as f:
                data = json.load(f)
        default_products = [self._normalize_product(dict(product)) for product in data.get("products", [])]
        custom_products = [self._normalize_product(dict(product)) for product in self.products if not product.get("built_in", True)]
        restored_categories = self._normalize_categories(data.get("categories", []))
        custom_categories = [product.get("category", "Other") for product in custom_products]
        self.products = default_products + custom_products
        self.extra_categories = self._normalize_categories(restored_categories + self.extra_categories + custom_categories)
        self._merged_options = self._build_merged_options()
        self.save()

    def products_by_category(self, category: str) -> list[dict[str, Any]]:
        return [dict(product) for product in self.products if product.get("category") == category]

    def product_options_by_category(self, category: str) -> list[dict[str, Any]]:
        options = [self._product_to_option(product) for product in self.products if product.get("category") == category]
        if category == "Detector":
            return sorted(options, key=lambda opt: opt.get("popup_name", "").strip().startswith("600"))
        return options

    def merged_options_by_category(self, category: str) -> list[dict[str, Any]]:
        return [dict(option) for option in self._merged_options.get(category, [])]

    def get_merged_option(self, merge_key: str) -> dict[str, Any] | None:
        for options in self._merged_options.values():
            for option in options:
                if option.get("merge_key") == merge_key:
                    return dict(option)
        return None

    def resolve_row_state(self, row_state: dict[str, Any] | None) -> dict[str, Any]:
        state = dict(row_state or {})
        product_id = state.get("product_id")
        if product_id:
            option = self.get_product_option(product_id)
            if option:
                return {**option, **state}
        merge_key = state.get("merge_key")
        if merge_key:
            option = self.get_merged_option(merge_key)
            if option:
                member_ids = option.get("member_product_ids", [])
                if member_ids:
                    product_option = self.get_product_option(member_ids[0])
                    if product_option:
                        state.pop("merge_key", None)
                        state.pop("member_product_ids", None)
                        return {**product_option, **state}
        legacy_product_id = state.get("product_id")
        if legacy_product_id:
            option = self.get_merged_option_for_product(legacy_product_id)
            if option:
                member_ids = option.get("member_product_ids", [])
                if member_ids:
                    product_option = self.get_product_option(member_ids[0])
                    if product_option:
                        state.pop("merge_key", None)
                        state.pop("member_product_ids", None)
                        return {**product_option, **state}
        return state

    def get_merged_option_for_product(self, product_id: str) -> dict[str, Any] | None:
        for options in self._merged_options.values():
            for option in options:
                if product_id in option.get("member_product_ids", []):
                    return dict(option)
        return None

    def get_product(self, product_id: str) -> dict[str, Any] | None:
        for product in self.products:
            if product.get("id") == product_id:
                return dict(product)
        return None

    def get_product_option(self, product_id: str) -> dict[str, Any] | None:
        product = self.get_product(product_id)
        return self._product_to_option(product) if product else None

    def update_customer_name(self, product_id: str, customer_name: str) -> dict[str, Any] | None:
        customer_name = (customer_name or "").strip()
        if not customer_name:
            return None
        for product in self.products:
            if product.get("id") == product_id:
                product["customer_name"] = customer_name
                self.save()
                return dict(product)
        return None

    def replace_all(self, products: list[dict[str, Any]]) -> None:
        self.products = [self._normalize_product(dict(product)) for product in products]
        self.extra_categories = self._normalize_categories(self.extra_categories + [product.get("category", "Other") for product in self.products])
        self._merged_options = self._build_merged_options()
        self.save()

    def next_product_id(self) -> str:
        values: list[int] = []
        for product in self.products:
            pid = product.get("id", "")
            if isinstance(pid, str) and pid.startswith("product-"):
                try:
                    values.append(int(pid.split("-")[-1]))
                except ValueError:
                    pass
        return f"product-{(max(values) + 1 if values else 1):04d}"

    def _product_to_option(self, product: dict[str, Any] | None) -> dict[str, Any] | None:
        if not product:
            return None
        customer_name = str(product.get("customer_name", "")).strip()
        product_name = str(product.get("product_name", "")).strip()
        popup_name = f"{customer_name} - {product_name}" if customer_name and product_name else (product_name or customer_name)
        display_name = product_name or customer_name
        return {
            "product_id": product.get("id"),
            "category": product.get("category", "Other"),
            "type": product.get("type", product.get("category", "Other")),
            "standby": float(product.get("standby", 0.5)),
            "alarm": float(product.get("alarm", 0.0)),
            "ledCost": int(product.get("ledCost", 1)),
            "customer_name": customer_name,
            "factory_name": str(product.get("factory_name", "")).strip(),
            "product_name": product_name,
            "popup_name": popup_name,
            "display_name": display_name,
        }

    def _merge_key(self, product: dict[str, Any]) -> str:
        return "|".join(
            [
                str(product.get("standby", 0)),
                str(product.get("alarm", 0)),
                str(product.get("ledCost", 1)),
                str(product.get("type", "")),
            ]
        )

    def _build_merged_options(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        category_order: list[str] = []
        for product in self.products:
            category = product.get("category", "Other")
            if category not in category_order:
                category_order.append(category)
            group_key = (category, self._merge_key(product))
            grouped.setdefault(group_key, []).append(dict(product))
        merged: dict[str, list[dict[str, Any]]] = {category: [] for category in category_order}
        for (category, merge_key), members in grouped.items():
            members = sorted(members, key=lambda item: item.get("factory_name", ""))
            first = members[0]
            merged[category].append(
                {
                    "merge_key": merge_key,
                    "category": category,
                    "type": first.get("type", category),
                    "standby": float(first.get("standby", 0.5)),
                    "alarm": float(first.get("alarm", 0.0)),
                    "ledCost": int(first.get("ledCost", 1)),
                    "member_product_ids": [item.get("id") for item in members if item.get("id")],
                    "display_name": self._build_display_name([item.get("factory_name", "") for item in members]),
                }
            )
        return merged

    def _ensure_default_backup(self, force: bool = False) -> None:
        if self.backup_path.exists() and not force:
            return
        default_products = [dict(product) for product in self.products if product.get("built_in", True)]
        if not default_products:
            default_products = [dict(product) for product in self.products]
        default_categories = self._normalize_categories(
            self.extra_categories + [product.get("category", "Other") for product in default_products]
        )
        with self.backup_path.open("w", encoding="utf-8") as f:
            json.dump({"categories": default_categories, "products": default_products}, f, ensure_ascii=False, indent=2)

    def _normalize_categories(self, categories: list[Any]) -> list[str]:
        normalized: list[str] = []
        for category in categories:
            value = self._normalize_category(category)
            if value and value not in normalized:
                normalized.append(value)
        return normalized

    def _normalize_category(self, category: Any) -> str:
        value = str(category or "").strip()
        if value in MODULE_CATEGORY_ALIASES:
            return MODULE_CATEGORY_NAME
        return value

    def _build_display_name(self, names: list[str]) -> str:
        clean = [name for name in names if name]
        if not clean:
            return ""
        if len(clean) == 1:
            return clean[0]
        parsed = [self._split_model_name(name) for name in clean]
        if all(part is not None for part in parsed):
            prefixes = {part[0] for part in parsed}
            suffixes = {part[2] for part in parsed}
            numbers = sorted(part[1] for part in parsed)
            if len(prefixes) == 1 and len(suffixes) == 1:
                prefix = parsed[0][0]
                suffix = parsed[0][2]
                if len(numbers) <= 3:
                    return f"{prefix}{'/'.join(numbers)}{suffix}"
                return f"{prefix}{numbers[0]}...{numbers[-1]}{suffix}"
        if len(clean) <= 3:
            return "/".join(clean)
        return f"{clean[0]}...{clean[-1]}"

    def _split_model_name(self, name: str) -> tuple[str, str, str] | None:
        match = re.match(r"^(.*?)(\d+)([^0-9]*)$", name)
        if not match:
            return None
        return match.group(1), match.group(2), match.group(3)
