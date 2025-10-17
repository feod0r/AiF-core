from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, validator

from app.api.accounts.models import OwnerOut
from app.api.counterparties.models import CounterpartyOut


class WarehouseOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    contact_person_id: Optional[int] = None
    contact_person: Optional[CounterpartyOut] = None
    owner_id: int
    owner: Optional[OwnerOut] = None
    is_active: bool
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseIn(BaseModel):
    name: str
    address: Optional[str] = None
    contact_person_id: Optional[int] = None
    owner_id: int

    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Название склада не может быть пустым")
        return v.strip()


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact_person_id: Optional[int] = None
    owner_id: Optional[int] = None
    is_active: Optional[bool] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Название склада не может быть пустым")
        return v.strip() if v is not None else v


class WarehouseSummary(BaseModel):
    total_warehouses: int
    owner_counts: Dict[str, int]


class WarehouseDetail(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    contact_person_id: Optional[int] = None
    contact_person: Optional[CounterpartyOut] = None
    owner_id: int
    owner: Optional[OwnerOut] = None
    is_active: bool
    start_date: datetime
    end_date: datetime
    stock_count: int = 0  # Количество позиций на складе

    model_config = ConfigDict(from_attributes=True)


class WarehouseWithStocks(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    contact_person_id: Optional[int] = None
    contact_person: Optional[CounterpartyOut] = None
    owner_id: int
    owner: Optional[OwnerOut] = None
    is_active: bool
    stock_count: int
    total_items: int  # Общее количество товаров на складе

    model_config = ConfigDict(from_attributes=True)
