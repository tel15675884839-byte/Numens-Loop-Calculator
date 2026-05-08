from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from loop_calculator.calculator import calculate_loop_from_rows


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "loop_calculator.sqlite3"
    app = create_app(db_path=db_path)
    with TestClient(app) as test_client:
        yield test_client


def test_calculation_api_maps_request_and_returns_numeric_fields(client: TestClient) -> None:
    response = client.post(
        "/api/calculations/loop",
        json={
            "devices": [
                {
                    "product_id": "product-0001",
                    "display_name": "Input Module, Single Input",
                    "category": "I/O Module",
                    "standby": 0.5,
                    "alarm": 2.1,
                    "ledCost": 1,
                    "type": "I/O Module",
                    "lead_dist": 10,
                    "interval_dist": 5,
                    "qty": 3,
                }
            ],
            "max_current_ma": 400,
            "min_voltage_v": 17,
            "cable_resistance_ohm_per_km": 12.1,
            "addr_limit": 125,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    expected = calculate_loop_from_rows(
        [
            {
                "product_id": "product-0001",
                "display_name": "Input Module, Single Input",
                "category": "I/O Module",
                "standby": 0.5,
                "alarm": 2.1,
                "ledCost": 1,
                "type": "I/O Module",
                "lead_dist": 10,
                "interval_dist": 5,
                "qty": 3,
            }
        ],
        max_current_ma=400,
        min_voltage_v=17,
        cable_resistance_ohm_per_km=12.1,
        addr_limit=125,
    )

    assert payload["total_addresses"] == expected.total_addresses
    assert payload["total_current_ma"] == pytest.approx(expected.total_current_ma)
    assert payload["total_distance_m"] == pytest.approx(expected.total_distance_m)
    assert payload["voltage_drop_v"] == pytest.approx(expected.voltage_drop_v)
    assert payload["end_voltage_v"] == pytest.approx(expected.end_voltage_v)
    assert payload["max_install_distance_m"] == pytest.approx(expected.max_install_distance_m)
    assert payload["recommended_cable_size"] == expected.recommended_cable_size
    assert payload["recommended_cable_unit"] == expected.recommended_cable_unit
    assert payload["standby_current_ma"] == pytest.approx(expected.standby_current_ma)
    assert payload["alarm_current_ma"] == pytest.approx(expected.alarm_current_ma)
    assert [diagnostic["key"] for diagnostic in payload["diagnostics"]] == [
        issue.key for issue in expected.diagnostics
    ]


def test_calculation_api_matches_core_for_mixed_led_and_lsm_loads(client: TestClient) -> None:
    request_payload = {
        "devices": [
            {
                "product_id": "det-1",
                "display_name": "Detector",
                "category": "Detector",
                "standby": 0.5,
                "alarm": 2.0,
                "ledCost": 1,
                "type": "Detector",
                "lead_dist": 20,
                "interval_dist": 15,
                "qty": 12,
            },
            {
                "product_id": "lsm-1",
                "display_name": "Loop Sounder",
                "category": "Sounder",
                "standby": 0.35,
                "alarm": 16.0,
                "ledCost": 0,
                "type": "LSM",
                "lead_dist": 35,
                "interval_dist": 20,
                "qty": 2,
            },
            {
                "product_id": "mod-1",
                "display_name": "Module",
                "category": "I/O Module",
                "standby": 0.8,
                "alarm": 3.5,
                "ledCost": 2,
                "type": "I/O Module",
                "lead_dist": 10,
                "interval_dist": 0,
                "qty": 1,
            },
        ],
        "max_current_ma": 40,
        "min_voltage_v": 27.95,
        "cable_resistance_ohm_per_km": 12.1,
        "addr_limit": 10,
    }

    response = client.post("/api/calculations/loop", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    expected = calculate_loop_from_rows(
        request_payload["devices"],
        max_current_ma=40,
        min_voltage_v=27.95,
        cable_resistance_ohm_per_km=12.1,
        addr_limit=10,
    )
    assert payload["total_addresses"] == expected.total_addresses
    assert payload["total_current_ma"] == pytest.approx(expected.total_current_ma)
    assert payload["total_distance_m"] == pytest.approx(expected.total_distance_m)
    assert payload["voltage_drop_v"] == pytest.approx(expected.voltage_drop_v)
    assert payload["end_voltage_v"] == pytest.approx(expected.end_voltage_v)
    assert payload["max_install_distance_m"] == pytest.approx(expected.max_install_distance_m)
    assert payload["recommended_cable_size"] == expected.recommended_cable_size
    assert payload["recommended_cable_unit"] == expected.recommended_cable_unit
    assert payload["standby_current_ma"] == pytest.approx(expected.standby_current_ma)
    assert payload["alarm_current_ma"] == pytest.approx(expected.alarm_current_ma)
    assert [diagnostic["key"] for diagnostic in payload["diagnostics"]] == [
        "diag_address_over",
        "diag_current_over",
        "diag_voltage_low",
    ]
    assert [diagnostic["key"] for diagnostic in payload["diagnostics"]] == [
        issue.key for issue in expected.diagnostics
    ]


def test_calculation_api_rejects_negative_numeric_inputs(client: TestClient) -> None:
    response = client.post(
        "/api/calculations/loop",
        json={
            "devices": [
                {
                    "display_name": "Invalid Device",
                    "category": "Detector",
                    "standby": -0.5,
                    "alarm": -2.0,
                    "ledCost": 1,
                    "type": "Detector",
                    "lead_dist": -10,
                    "interval_dist": -5,
                    "qty": -1,
                }
            ],
            "max_current_ma": -400,
            "min_voltage_v": 0,
            "cable_resistance_ohm_per_km": 0,
            "addr_limit": 0,
        },
    )

    assert response.status_code == 422


def test_seeded_products_support_search_and_builtin_delete_protection(client: TestClient) -> None:
    seeded = client.get("/api/products")
    assert seeded.status_code == 200
    seeded_payload = seeded.json()
    assert any(product["id"] == "product-0001" and product["built_in"] for product in seeded_payload)
    seeded_product = next(product for product in seeded_payload if product["id"] == "product-0001")
    assert seeded_product["created_at"]
    assert seeded_product["updated_at"]

    search = client.get("/api/products", params={"q": "626-001", "category": "I/O Module"})
    assert search.status_code == 200
    search_payload = search.json()
    assert [product["id"] for product in search_payload] == ["product-0001"]

    delete_builtin = client.delete("/api/products/product-0001", headers={"X-Admin-Password": "numens888"})
    assert delete_builtin.status_code == 409

    force_delete_builtin = client.delete(
        "/api/products/product-0001",
        params={"force": "true"},
        headers={"X-Admin-Password": "numens888"},
    )
    assert force_delete_builtin.status_code == 204
    backup_files = sorted((client.app.state.store.db_path.parent / "backups").glob("products-before-delete-*.json"))
    assert backup_files
    after_force_delete = client.get("/api/products", params={"q": "626-001", "category": "I/O Module"})
    assert after_force_delete.status_code == 200
    assert [product["id"] for product in after_force_delete.json()] == []

    deleted_products = client.get("/api/products", params={"deleted": "only", "q": "626-001"})
    assert deleted_products.status_code == 200
    deleted_payload = deleted_products.json()
    assert [product["id"] for product in deleted_payload] == ["product-0001"]
    assert deleted_payload[0]["deleted_at"]

    restore_builtin = client.post("/api/products/product-0001/restore", headers={"X-Admin-Password": "numens888"})
    assert restore_builtin.status_code == 200
    assert restore_builtin.json()["deleted_at"] == ""

    after_restore = client.get("/api/products", params={"q": "626-001", "category": "I/O Module"})
    assert after_restore.status_code == 200
    assert [product["id"] for product in after_restore.json()] == ["product-0001"]

    created = client.post(
        "/api/products",
        headers={"X-Admin-Password": "numens888"},
        json={
            "category": "Detector",
            "factory_name": "CUSTOM-001",
            "customer_name": "CUSTOM-001",
            "product_name": "Custom Detector",
            "standby_ma": 0.8,
            "alarm_ma": 2.2,
            "led_cost": 1,
            "device_type": "Detector",
            "built_in": False,
        },
    )
    assert created.status_code == 201
    created_payload = created.json()
    created_id = created_payload["id"]
    assert created_payload["created_at"]
    assert created_payload["updated_at"]

    delete_custom = client.delete(f"/api/products/{created_id}", headers={"X-Admin-Password": "numens888"})
    assert delete_custom.status_code == 204


def test_product_writes_require_admin_and_cannot_demote_builtin_flag(client: TestClient) -> None:
    seeded_product = next(product for product in client.get("/api/products").json() if product["id"] == "product-0001")

    unauthorized_delete = client.delete("/api/products/product-0001", params={"force": "true"})
    assert unauthorized_delete.status_code == 403

    demote_response = client.put(
        "/api/products/product-0001",
        headers={"X-Admin-Password": "numens888"},
        json={**seeded_product, "built_in": False},
    )
    assert demote_response.status_code == 200
    assert demote_response.json()["built_in"] is True

    still_protected = client.delete("/api/products/product-0001", headers={"X-Admin-Password": "numens888"})
    assert still_protected.status_code == 409


def test_project_save_and_reload_round_trip_preserves_loops_and_rows(client: TestClient) -> None:
    create_response = client.post(
        "/api/projects",
        json={
            "name": "Round Trip Project",
            "active_loop_id": None,
            "loops": [
                {
                    "name": "Loop A",
                    "sort_order": 1,
                    "address_limit": 125,
                    "max_current_ma": 400,
                    "min_voltage_v": 17,
                    "cable_size": "1.5",
                    "cable_resistance_ohm_per_km": 12.1,
                    "aux_current_ma": 0,
                    "device_rows": [
                        {
                            "sort_order": 1,
                            "product_id": "product-0001",
                            "category": "I/O Module",
                            "display_name": "Input Module, Single Input",
                            "customer_name": "626-001",
                            "factory_name": "626-001",
                            "product_name": "Input Module, Single Input",
                            "standby_ma": 0.5,
                            "alarm_ma": 2.1,
                            "led_cost": 1,
                            "device_type": "I/O Module",
                            "lead_dist_m": 10.0,
                            "interval_dist_m": 5.0,
                            "qty": 3,
                        }
                    ],
                }
            ],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()

    update_response = client.put(
        f"/api/projects/{created['id']}",
        json=created,
    )
    assert update_response.status_code == 200

    reload_response = client.get(f"/api/projects/{created['id']}")
    assert reload_response.status_code == 200
    project = reload_response.json()

    assert project["name"] == "Round Trip Project"
    assert project["created_at"]
    assert project["updated_at"]
    assert len(project["loops"]) == 1
    loop = project["loops"][0]
    assert loop["project_id"] == project["id"]
    assert loop["name"] == "Loop A"
    assert loop["address_limit"] == 125
    assert loop["device_rows"][0]["product_id"] == "product-0001"
    assert loop["device_rows"][0]["product_name"] == "Input Module, Single Input"


def test_loop_endpoints_reuse_project_validation_rules(client: TestClient) -> None:
    create_project_response = client.post(
        "/api/projects",
        json={
            "name": "Loop Endpoint Project",
            "active_loop_id": None,
            "loops": [],
        },
    )
    assert create_project_response.status_code == 201
    project_id = create_project_response.json()["id"]

    invalid_loop = {
        "name": "Invalid Loop",
        "sort_order": 1,
        "address_limit": 2,
        "max_current_ma": 400,
        "min_voltage_v": 17,
        "cable_size": "1.5",
        "cable_resistance_ohm_per_km": 12.1,
        "aux_current_ma": 0,
        "device_rows": [
            {
                "sort_order": 1,
                "product_id": "product-0001",
                "category": "I/O Module",
                "display_name": "Input Module, Single Input",
                "customer_name": "626-001",
                "factory_name": "626-001",
                "product_name": "Input Module, Single Input",
                "standby_ma": 0.5,
                "alarm_ma": 2.1,
                "led_cost": 1,
                "device_type": "I/O Module",
                "lead_dist_m": 10.0,
                "interval_dist_m": 5.0,
                "qty": 3,
            }
        ],
    }

    create_loop_response = client.post(f"/api/projects/{project_id}/loops", json=invalid_loop)

    assert create_loop_response.status_code == 422


def test_project_print_profile_round_trip(client: TestClient) -> None:
    create_response = client.post(
        "/api/projects",
        json={
            "name": "Print Project",
            "active_loop_id": None,
            "print_profile": {
                "project_no": "NUM-2401",
                "customer": "North Plant",
                "site": "Zone A",
                "panel": "FACP-01",
                "revision": "A",
                "prepared_by": "Engineering",
                "issue_date": "2026-04-30",
                "notes": "Issued for review",
            },
            "loops": [],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["print_profile"]["project_no"] == "NUM-2401"
    assert created["print_profile"]["revision"] == "A"

    created["print_profile"] = {
        "project_no": "NUM-2401",
        "customer": "North Plant",
        "site": "Zone B",
        "panel": "FACP-02",
        "revision": "B",
        "prepared_by": "QA",
        "issue_date": "2026-05-01",
        "notes": "Updated for site review",
    }
    update_response = client.put(f"/api/projects/{created['id']}", json=created)
    assert update_response.status_code == 200
    assert update_response.json()["print_profile"]["revision"] == "B"

    reload_response = client.get(f"/api/projects/{created['id']}")
    assert reload_response.status_code == 200
    reloaded = reload_response.json()

    assert reloaded["print_profile"] == {
        "project_no": "NUM-2401",
        "customer": "North Plant",
        "site": "Zone B",
        "panel": "FACP-02",
        "revision": "B",
        "prepared_by": "QA",
        "issue_date": "2026-05-01",
        "notes": "Updated for site review",
    }
