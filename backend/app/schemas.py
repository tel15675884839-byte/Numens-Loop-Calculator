from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str
    sort_order: int = 0


class CategoryRead(CategoryBase):
    id: int


class ProductBase(BaseModel):
    category: str
    factory_name: str
    customer_name: str
    product_name: str
    standby_ma: float = 0.0
    alarm_ma: float = 0.0
    led_cost: int = 1
    device_type: str = ""
    built_in: bool = False


class ProductCreate(ProductBase):
    id: str | None = None


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: str


class DeviceRowBase(BaseModel):
    id: str | None = None
    sort_order: int = 0
    product_id: str | None = None
    category: str = "Other"
    display_name: str = ""
    customer_name: str = ""
    factory_name: str = ""
    product_name: str = ""
    standby_ma: float = 0.5
    alarm_ma: float = 0.0
    led_cost: int = 1
    device_type: str = ""
    lead_dist_m: float = 0.0
    interval_dist_m: float = 0.0
    qty: int = 1


class LoopBase(BaseModel):
    id: str | None = None
    name: str
    sort_order: int = 0
    address_limit: int = 125
    max_current_ma: float = 400.0
    min_voltage_v: float = 17.0
    cable_size: str = ""
    cable_resistance_ohm_per_km: float = 12.1
    aux_current_ma: float = 0.0
    device_rows: list[DeviceRowBase] = Field(default_factory=list)


class ProjectBase(BaseModel):
    name: str
    active_loop_id: str | None = None
    loops: list[LoopBase] = Field(default_factory=list)


class ProjectCreate(ProjectBase):
    id: str | None = None


class ProjectUpdate(ProjectBase):
    id: str | None = None


class ProjectRead(ProjectBase):
    id: str


class CalculationDevice(BaseModel):
    product_id: str | None = None
    display_name: str = ""
    category: str = "Other"
    standby: float = 0.5
    alarm: float = 0.0
    ledCost: int = Field(default=1, alias="ledCost")
    type_: str = Field(default="", alias="type")
    lead_dist: float = 0.0
    interval_dist: float = 0.0
    qty: int = 1

    model_config = ConfigDict(populate_by_name=True)


class CalculationRequest(BaseModel):
    devices: list[CalculationDevice] = Field(default_factory=list)
    max_current_ma: float = 400.0
    min_voltage_v: float = 17.0
    cable_resistance_ohm_per_km: float = 12.1
    addr_limit: int = 125


class CalculationDiagnostic(BaseModel):
    key: str
    params: dict[str, Any] = Field(default_factory=dict)


class CalculationResponse(BaseModel):
    total_addresses: int
    total_current_ma: float
    total_distance_m: float
    voltage_drop_v: float
    end_voltage_v: float
    max_install_distance_m: float
    recommended_cable_size: str
    recommended_cable_unit: str
    standby_current_ma: float
    alarm_current_ma: float
    diagnostics: list[CalculationDiagnostic] = Field(default_factory=list)
