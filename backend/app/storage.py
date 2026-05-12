from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class ProductProtectedError(RuntimeError):
    pass


class NotFoundError(RuntimeError):
    pass


class ValidationError(RuntimeError):
    pass


MAX_LOOPS = 6
MAX_SOUNDER_PER_LOOP = 32


class SQLiteStore:
    def __init__(self, db_path: Path, seed_path: Path) -> None:
        self.db_path = Path(db_path)
        self.seed_path = Path(seed_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    sort_order INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    factory_name TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    standby_ma REAL NOT NULL DEFAULT 0,
                    alarm_ma REAL NOT NULL DEFAULT 0,
                    led_cost INTEGER NOT NULL DEFAULT 1,
                    device_type TEXT NOT NULL DEFAULT '',
                    built_in INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    deleted_at TEXT NOT NULL DEFAULT '',
                    deleted_by TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    active_loop_id TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS project_print_profiles (
                    project_id TEXT PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                    project_no TEXT NOT NULL DEFAULT '',
                    customer TEXT NOT NULL DEFAULT '',
                    site TEXT NOT NULL DEFAULT '',
                    panel TEXT NOT NULL DEFAULT '',
                    revision TEXT NOT NULL DEFAULT '',
                    prepared_by TEXT NOT NULL DEFAULT '',
                    issue_date TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS project_loops (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    address_limit INTEGER NOT NULL DEFAULT 125,
                    max_current_ma REAL NOT NULL DEFAULT 400,
                    min_voltage_v REAL NOT NULL DEFAULT 17,
                    cable_size TEXT NOT NULL DEFAULT '',
                    cable_resistance_ohm_per_km REAL NOT NULL DEFAULT 12.1,
                    aux_current_ma REAL NOT NULL DEFAULT 0,
                    rows_json TEXT NOT NULL DEFAULT '[]'
                );
                """
            )
            self._ensure_column(conn, "products", "created_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "products", "updated_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "products", "deleted_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "products", "deleted_by", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "projects", "created_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "projects", "updated_at", "TEXT NOT NULL DEFAULT ''")
            conn.execute("UPDATE products SET created_at = datetime('now') WHERE created_at = ''")
            conn.execute("UPDATE products SET updated_at = datetime('now') WHERE updated_at = ''")
            conn.execute("UPDATE projects SET created_at = datetime('now') WHERE created_at = ''")
            conn.execute("UPDATE projects SET updated_at = datetime('now') WHERE updated_at = ''")

        self.sync_builtin_products_from_json(self.seed_path)

    def sync_builtin_products_from_json(self, path: Path) -> None:
        with path.open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)

        seed_product_ids = [str(product["id"]) for product in payload.get("products", [])]
        with self._connect() as conn:
            if seed_product_ids:
                conn.execute(
                    f"DELETE FROM products WHERE built_in = 1 AND id NOT IN ({','.join('?' for _ in seed_product_ids)})",
                    seed_product_ids,
                )
            else:
                conn.execute("DELETE FROM products WHERE built_in = 1")
        self.seed_from_json(path)

    def sync_builtin_products_from_payload(self, products: list[dict[str, Any]]) -> None:
        product_ids = [str(product["id"]) for product in products]
        with self._connect() as conn:
            if product_ids:
                conn.execute(
                    f"DELETE FROM products WHERE built_in = 1 AND id NOT IN ({','.join('?' for _ in product_ids)})",
                    product_ids,
                )
            else:
                conn.execute("DELETE FROM products WHERE built_in = 1")

            for product in products:
                conn.execute(
                    """
                    INSERT INTO products (
                        id, category, factory_name, customer_name, product_name,
                        standby_ma, alarm_ma, led_cost, device_type, built_in
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        category=excluded.category,
                        factory_name=excluded.factory_name,
                        customer_name=excluded.customer_name,
                        product_name=excluded.product_name,
                        standby_ma=excluded.standby_ma,
                        alarm_ma=excluded.alarm_ma,
                        led_cost=excluded.led_cost,
                        device_type=excluded.device_type,
                        built_in=excluded.built_in,
                        updated_at=datetime('now')
                    """,
                    (
                        product["id"],
                        product.get("category", "Other"),
                        product.get("factory_name", ""),
                        product.get("customer_name", ""),
                        product.get("product_name", product.get("factory_name", "")),
                        float(product.get("standby_ma", product.get("standby", 0.5))),
                        float(product.get("alarm_ma", product.get("alarm", 2.0))),
                        int(product.get("led_cost", product.get("ledCost", 1))),
                        product.get("device_type", product.get("type", "")),
                        1,
                    ),
                )

    def seed_from_json(self, path: Path) -> None:
        with path.open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)

        categories = payload.get("categories", [])
        products = payload.get("products", [])

        with self._connect() as conn:
            for sort_order, name in enumerate(categories):
                conn.execute(
                    """
                    INSERT INTO categories (name, sort_order)
                    VALUES (?, ?)
                    ON CONFLICT(name) DO UPDATE SET sort_order=excluded.sort_order
                    """,
                    (name, sort_order),
                )

            for product in products:
                conn.execute(
                    """
                    INSERT INTO products (
                        id, category, factory_name, customer_name, product_name,
                        standby_ma, alarm_ma, led_cost, device_type, built_in
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        category=excluded.category,
                        factory_name=excluded.factory_name,
                        customer_name=excluded.customer_name,
                        product_name=excluded.product_name,
                        standby_ma=excluded.standby_ma,
                        alarm_ma=excluded.alarm_ma,
                        led_cost=excluded.led_cost,
                        device_type=excluded.device_type,
                        built_in=excluded.built_in,
                        updated_at=datetime('now')
                    """,
                    (
                        product["id"],
                        product["category"],
                        product["factory_name"],
                        product["customer_name"],
                        product["product_name"],
                        float(product.get("standby", product.get("standby_ma", 0.0))),
                        float(product.get("alarm", product.get("alarm_ma", 0.0))),
                        int(product.get("ledCost", product.get("led_cost", 1))),
                        product.get("type", product.get("device_type", "")),
                        1 if product.get("built_in", False) else 0,
                    ),
                )

    def list_categories(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, sort_order FROM categories ORDER BY sort_order, name"
            ).fetchall()
        return [dict(row) for row in rows]

    def create_category(self, name: str, sort_order: int = 0) -> dict[str, Any]:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
                (name, sort_order),
            )
            row = conn.execute(
                "SELECT id, name, sort_order FROM categories WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return dict(row)

    def list_products(
        self,
        q: str | None = None,
        category: str | None = None,
        *,
        deleted: str = "active",
    ) -> list[dict[str, Any]]:
        query = [
            "SELECT id, category, factory_name, customer_name, product_name, standby_ma, alarm_ma, led_cost, device_type, built_in, created_at, updated_at, deleted_at, deleted_by",
            "FROM products",
        ]
        conditions: list[str] = []
        params: list[Any] = []
        if deleted == "only":
            conditions.append("deleted_at <> ''")
        elif deleted != "all":
            conditions.append("deleted_at = ''")
        if category:
            conditions.append("category = ?")
            params.append(category)
        if q:
            conditions.append(
                "("
                "LOWER(category) LIKE ? OR LOWER(factory_name) LIKE ? OR "
                "LOWER(customer_name) LIKE ? OR LOWER(product_name) LIKE ?"
                ")"
            )
            pattern = f"%{q.lower()}%"
            params.extend([pattern, pattern, pattern, pattern])
        if conditions:
            query.append("WHERE " + " AND ".join(conditions))
        query.append("ORDER BY category, product_name, id")
        statement = " ".join(query)
        with self._connect() as conn:
            rows = conn.execute(statement, params).fetchall()
        return [self._normalize_product_row(dict(row)) for row in rows]

    def create_product(self, payload: dict[str, Any]) -> dict[str, Any]:
        product_id = payload.get("id") or f"product-{uuid4().hex[:12]}"
        values = self._normalize_product_payload(payload, product_id)
        values["built_in"] = 0
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO products (
                    id, category, factory_name, customer_name, product_name,
                    standby_ma, alarm_ma, led_cost, device_type, built_in, created_at, updated_at
                ) VALUES (:id, :category, :factory_name, :customer_name, :product_name,
                          :standby_ma, :alarm_ma, :led_cost, :device_type, :built_in,
                          datetime('now'), datetime('now'))
                """,
                values,
            )
        return self.get_product(product_id)

    def update_product(self, product_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        values = self._normalize_product_payload(payload, product_id)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE products SET
                    category=:category,
                    factory_name=:factory_name,
                    customer_name=:customer_name,
                    product_name=:product_name,
                    standby_ma=:standby_ma,
                    alarm_ma=:alarm_ma,
                    led_cost=:led_cost,
                    device_type=:device_type,
                    updated_at=datetime('now')
                WHERE id=:id AND deleted_at=''
                """,
                values,
            )
            if cursor.rowcount == 0:
                raise NotFoundError(product_id)
        return self.get_product(product_id)

    def delete_product(self, product_id: str, *, force: bool = False) -> None:
        product = self.get_product(product_id)
        if product["built_in"] and not force:
            raise ProductProtectedError(product_id)
        with self._connect() as conn:
            self._write_products_backup(conn, product_id)
            cursor = conn.execute(
                """
                UPDATE products
                SET deleted_at = datetime('now'),
                    deleted_by = ?,
                    updated_at = datetime('now')
                WHERE id = ? AND deleted_at = ''
                """,
                ("admin" if force else "user", product_id),
            )
            if cursor.rowcount == 0:
                raise NotFoundError(product_id)

    def restore_product(self, product_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE products
                SET deleted_at = '',
                    deleted_by = '',
                    updated_at = datetime('now')
                WHERE id = ? AND deleted_at <> ''
                """,
                (product_id,),
            )
            if cursor.rowcount == 0:
                raise NotFoundError(product_id)
        return self.get_product(product_id)

    def get_product(self, product_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        with self._connect() as conn:
            deleted_clause = "" if include_deleted else "AND deleted_at = ''"
            row = conn.execute(
                f"""
                SELECT id, category, factory_name, customer_name, product_name,
                       standby_ma, alarm_ma, led_cost, device_type, built_in, created_at, updated_at,
                       deleted_at, deleted_by
                FROM products
                WHERE id = ? {deleted_clause}
                """,
                (product_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError(product_id)
        return self._normalize_product_row(dict(row))

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT p.id, p.name, p.active_loop_id, p.created_at, p.updated_at, COUNT(l.id) AS loop_count
                FROM projects p
                LEFT JOIN project_loops l ON l.project_id = p.id
                GROUP BY p.id, p.name, p.active_loop_id, p.created_at, p.updated_at
                ORDER BY p.name, p.id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = payload.get("id") or f"project-{uuid4().hex[:12]}"
        self._replace_project(project_id, payload, create=True)
        return self.get_project(project_id)

    def replace_project(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._replace_project(project_id, payload, create=False)
        return self.get_project(project_id)

    def _replace_project(self, project_id: str, payload: dict[str, Any], *, create: bool) -> None:
        name = payload.get("name", "")
        active_loop_id = payload.get("active_loop_id")
        print_profile = payload.get("print_profile")
        loops = payload.get("loops", [])

        self._validate_project_loops(loops)

        with self._connect() as conn:
            if create:
                conn.execute(
                    """
                    INSERT INTO projects (id, name, active_loop_id, created_at, updated_at)
                    VALUES (?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (project_id, name, active_loop_id),
                )
            else:
                cursor = conn.execute(
                    "UPDATE projects SET name = ?, active_loop_id = ?, updated_at = datetime('now') WHERE id = ?",
                    (name, active_loop_id, project_id),
                )
                if cursor.rowcount == 0:
                    raise NotFoundError(project_id)
                conn.execute("DELETE FROM project_loops WHERE project_id = ?", (project_id,))

            for loop in loops:
                self._insert_loop(conn, project_id, loop)
            self._replace_print_profile(conn, project_id, print_profile)

    def _as_int(self, value: Any, default: int, field_name: str) -> int:
        try:
            return int(float(value if value is not None and value != "" else default))
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{field_name} must be an integer.") from exc

    def _as_float(self, value: Any, default: float, field_name: str) -> float:
        try:
            return float(value if value is not None and value != "" else default)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{field_name} must be a number.") from exc

    def _validate_project_loops(self, loops: list[dict[str, Any]]) -> None:
        if len(loops) > MAX_LOOPS:
            raise ValidationError(f"A project cannot have more than {MAX_LOOPS} loops (got {len(loops)}).")
        for loop in loops:
            self._validate_loop_payload(loop)

    def _validate_loop_payload(self, loop: dict[str, Any]) -> None:
        loop_name = str(loop.get("name", "") or "")
        address_limit = self._as_int(loop.get("address_limit"), 125, "address_limit")
        max_current_ma = self._as_float(loop.get("max_current_ma"), 400.0, "max_current_ma")
        min_voltage_v = self._as_float(loop.get("min_voltage_v"), 17.0, "min_voltage_v")
        cable_resistance = self._as_float(
            loop.get("cable_resistance_ohm_per_km"),
            12.1,
            "cable_resistance_ohm_per_km",
        )
        aux_current_ma = self._as_float(loop.get("aux_current_ma"), 0.0, "aux_current_ma")

        if address_limit < 1:
            raise ValidationError("address_limit must be at least 1.")
        if max_current_ma <= 0:
            raise ValidationError("max_current_ma must be greater than 0.")
        if min_voltage_v <= 0:
            raise ValidationError("min_voltage_v must be greater than 0.")
        if cable_resistance <= 0:
            raise ValidationError("cable_resistance_ohm_per_km must be greater than 0.")
        if aux_current_ma < 0:
            raise ValidationError("aux_current_ma must be at least 0.")

        total_qty = 0
        sounder_qty = 0
        for row in loop.get("device_rows", []):
            qty = self._as_int(row.get("qty"), 1, "qty")
            if qty < 1:
                raise ValidationError(f"Device qty must be at least 1 (got {qty}).")
            for field_name in ("standby_ma", "alarm_ma", "lead_dist_m", "interval_dist_m"):
                if self._as_float(row.get(field_name), 0.0, field_name) < 0:
                    raise ValidationError(f"{field_name} must be at least 0.")
            if self._as_int(row.get("led_cost"), 1, "led_cost") < 0:
                raise ValidationError("led_cost must be at least 0.")

            total_qty += qty
            category = str(row.get("category", "")).strip().lower()
            haystack = " ".join(
                str(row.get(k, "")) for k in ("display_name", "product_name", "customer_name", "factory_name", "device_type")
            ).upper()
            if category == "sounder" or "LSM" in haystack or "620-003" in haystack:
                sounder_qty += qty

        if total_qty > address_limit:
            raise ValidationError(f"Loop '{loop_name}' has {total_qty} addresses but limit is {address_limit}.")
        if sounder_qty > MAX_SOUNDER_PER_LOOP:
            raise ValidationError(f"Loop '{loop_name}' has {sounder_qty} sounders but max is {MAX_SOUNDER_PER_LOOP}.")

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            project = conn.execute(
                "SELECT id, name, active_loop_id, created_at, updated_at FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
            if project is None:
                raise NotFoundError(project_id)
            loops = conn.execute(
                """
                SELECT id, project_id, name, sort_order, address_limit, max_current_ma, min_voltage_v,
                       cable_size, cable_resistance_ohm_per_km, aux_current_ma, rows_json
                FROM project_loops
                WHERE project_id = ?
                ORDER BY sort_order, name, id
                """,
                (project_id,),
            ).fetchall()
            print_profile = conn.execute(
                """
                SELECT project_no, customer, site, panel, revision, prepared_by, issue_date, notes
                FROM project_print_profiles
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()

        payload = dict(project)
        payload["print_profile"] = dict(print_profile) if print_profile is not None else None
        payload["loops"] = [self._normalize_loop_row(dict(loop)) for loop in loops]
        return payload

    def delete_project(self, project_id: str) -> None:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            if cursor.rowcount == 0:
                raise NotFoundError(project_id)

    def create_loop(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        loop_id = payload.get("id") or f"loop-{uuid4().hex[:12]}"
        with self._connect() as conn:
            project = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
            if project is None:
                raise NotFoundError(project_id)
            row = conn.execute("SELECT COUNT(*) AS count FROM project_loops WHERE project_id = ?", (project_id,)).fetchone()
            loop_count = int(row["count"] if row is not None else 0)
            if loop_count >= MAX_LOOPS:
                raise ValidationError(f"A project cannot have more than {MAX_LOOPS} loops.")
            self._validate_loop_payload(payload)
            self._insert_loop(conn, project_id, payload, loop_id=loop_id)
        return self.get_loop(project_id, loop_id)

    def update_loop(self, project_id: str, loop_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM project_loops WHERE id = ? AND project_id = ?",
                (loop_id, project_id),
            ).fetchone()
            if existing is None:
                raise NotFoundError(loop_id)
            self._validate_loop_payload(payload)
            cursor = conn.execute(
                """
                UPDATE project_loops
                SET name = ?, sort_order = ?, address_limit = ?, max_current_ma = ?,
                    min_voltage_v = ?, cable_size = ?, cable_resistance_ohm_per_km = ?,
                    aux_current_ma = ?, rows_json = ?
                WHERE id = ? AND project_id = ?
                """,
                self._loop_update_values(payload) + (loop_id, project_id),
            )
        return self.get_loop(project_id, loop_id)

    def delete_loop(self, project_id: str, loop_id: str) -> None:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM project_loops WHERE id = ? AND project_id = ?",
                (loop_id, project_id),
            )
            if cursor.rowcount == 0:
                raise NotFoundError(loop_id)

    def get_loop(self, project_id: str, loop_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, name, sort_order, address_limit, max_current_ma, min_voltage_v,
                       cable_size, cable_resistance_ohm_per_km, aux_current_ma, rows_json
                FROM project_loops
                WHERE id = ? AND project_id = ?
                """,
                (loop_id, project_id),
            ).fetchone()
        if row is None:
            raise NotFoundError(loop_id)
        return self._normalize_loop_row(dict(row))

    def _insert_loop(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        payload: dict[str, Any],
        *,
        loop_id: str | None = None,
    ) -> None:
        loop_id = loop_id or payload.get("id") or f"loop-{uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO project_loops (
                id, project_id, name, sort_order, address_limit, max_current_ma,
                min_voltage_v, cable_size, cable_resistance_ohm_per_km, aux_current_ma, rows_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (loop_id, project_id) + self._loop_insert_values(payload),
        )

    def _replace_print_profile(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        payload: dict[str, Any] | None,
    ) -> None:
        conn.execute("DELETE FROM project_print_profiles WHERE project_id = ?", (project_id,))
        if payload is None:
            return
        values = self._normalize_print_profile_payload(payload)
        conn.execute(
            """
            INSERT INTO project_print_profiles (
                project_id, project_no, customer, site, panel, revision, prepared_by, issue_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                values["project_no"],
                values["customer"],
                values["site"],
                values["panel"],
                values["revision"],
                values["prepared_by"],
                values["issue_date"],
                values["notes"],
            ),
        )

    def _loop_insert_values(self, payload: dict[str, Any]) -> tuple[Any, ...]:
        rows = payload.get("device_rows", [])
        normalized_rows = [self._normalize_row_payload(row) for row in rows]
        return (
            payload.get("name", ""),
            int(payload.get("sort_order", 0)),
            int(payload.get("address_limit", 125)),
            float(payload.get("max_current_ma", 400.0)),
            float(payload.get("min_voltage_v", 17.0)),
            str(payload.get("cable_size", "")),
            float(payload.get("cable_resistance_ohm_per_km", 12.1)),
            float(payload.get("aux_current_ma", 0.0)),
            json.dumps(normalized_rows, ensure_ascii=False),
        )

    def _loop_update_values(self, payload: dict[str, Any]) -> tuple[Any, ...]:
        return self._loop_insert_values(payload)

    def _normalize_product_payload(self, payload: dict[str, Any], product_id: str) -> dict[str, Any]:
        return {
            "id": product_id,
            "category": payload.get("category", ""),
            "factory_name": payload.get("factory_name", ""),
            "customer_name": payload.get("customer_name", ""),
            "product_name": payload.get("product_name", ""),
            "standby_ma": float(payload.get("standby_ma", payload.get("standby", 0.0))),
            "alarm_ma": float(payload.get("alarm_ma", payload.get("alarm", 0.0))),
            "led_cost": int(payload.get("led_cost", payload.get("ledCost", 1))),
            "device_type": payload.get("device_type", payload.get("type", "")),
            "built_in": 1 if payload.get("built_in", False) else 0,
        }

    def _normalize_product_row(self, row: dict[str, Any]) -> dict[str, Any]:
        row["built_in"] = bool(row["built_in"])
        return row

    def _write_products_backup(self, conn: sqlite3.Connection, product_id: str) -> None:
        backup_dir = self.db_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        safe_product_id = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in product_id)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        rows = conn.execute(
            """
            SELECT id, category, factory_name, customer_name, product_name, standby_ma, alarm_ma,
                   led_cost, device_type, built_in, created_at, updated_at, deleted_at, deleted_by
            FROM products
            ORDER BY category, product_name, id
            """
        ).fetchall()
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "reason": "before product delete",
            "product_id": product_id,
            "products": [dict(row) for row in rows],
        }
        backup_path = backup_dir / f"products-before-delete-{safe_product_id}-{timestamp}.json"
        backup_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _normalize_print_profile_payload(self, payload: dict[str, Any]) -> dict[str, str]:
        return {
            "project_no": str(payload.get("project_no", "")),
            "customer": str(payload.get("customer", "")),
            "site": str(payload.get("site", "")),
            "panel": str(payload.get("panel", "")),
            "revision": str(payload.get("revision", "")),
            "prepared_by": str(payload.get("prepared_by", "")),
            "issue_date": str(payload.get("issue_date", "")),
            "notes": str(payload.get("notes", "")),
        }

    def _normalize_loop_row(self, row: dict[str, Any]) -> dict[str, Any]:
        row["device_rows"] = [
            self._normalize_row_payload(item) for item in json.loads(row.pop("rows_json") or "[]")
        ]
        return row

    def _normalize_row_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = dict(payload)
        row["sort_order"] = int(row.get("sort_order", 0))
        row["standby_ma"] = float(row.get("standby_ma", 0.5))
        row["alarm_ma"] = float(row.get("alarm_ma", 0.0))
        row["led_cost"] = int(row.get("led_cost", 1))
        row["lead_dist_m"] = float(row.get("lead_dist_m", 0.0))
        row["interval_dist_m"] = float(row.get("interval_dist_m", 0.0))
        row["qty"] = int(row.get("qty", 1))
        if not row.get("id"):
            row["id"] = f"row-{uuid4().hex[:12]}"
        return row

    def _count_products(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()
        return int(row["count"] if row is not None else 0)

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
