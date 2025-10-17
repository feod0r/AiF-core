from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, validator
from decimal import Decimal
from app.api.items.models import ItemOut
from app.api.warehouses.models import WarehouseOut


class WarehouseStockOut(BaseModel):
    id: int
    warehouse: Optional[WarehouseOut] = None
    item: Optional[ItemOut] = None
    quantity: Decimal
    reserved_quantity: Decimal
    min_quantity: Decimal
    max_quantity: Optional[Decimal] = None
    location: Optional[str] = None
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseStockIn(BaseModel):
    warehouse_id: int
    item_id: int
    quantity: Decimal = Decimal('0')
    reserved_quantity: Decimal = Decimal('0')
    min_quantity: Decimal = Decimal('0')
    max_quantity: Optional[Decimal] = None
    location: Optional[str] = None

    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Количество не может быть отрицательным')
        return v

    @validator('reserved_quantity')
    def validate_reserved_quantity(cls, v):
        if v < 0:
            raise ValueError('Зарезервированное количество не может быть отрицательным')
        return v

    @validator('min_quantity')
    def validate_min_quantity(cls, v):
        if v < 0:
            raise ValueError('Минимальное количество не может быть отрицательным')
        return v

    @validator('max_quantity')
    def validate_max_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Максимальное количество должно быть больше нуля')
        return v

    @validator('location')
    def validate_location(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Место хранения не может быть пустым')
        return v.strip() if v else None


class WarehouseStockUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    reserved_quantity: Optional[Decimal] = None
    min_quantity: Optional[Decimal] = None
    max_quantity: Optional[Decimal] = None
    location: Optional[str] = None

    @validator('quantity')
    def validate_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Количество не может быть отрицательным')
        return v

    @validator('reserved_quantity')
    def validate_reserved_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Зарезервированное количество не может быть отрицательным')
        return v

    @validator('min_quantity')
    def validate_min_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Минимальное количество не может быть отрицательным')
        return v

    @validator('max_quantity')
    def validate_max_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Максимальное количество должно быть больше нуля')
        return v

    @validator('location')
    def validate_location(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Место хранения не может быть пустым')
        return v.strip() if v else None


class StockOperation(BaseModel):
    quantity: Decimal

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше нуля')
        return v


class StockTransfer(BaseModel):
    from_warehouse_id: int
    to_warehouse_id: int
    item_id: int
    quantity: Decimal

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше нуля')
        return v

    @validator('from_warehouse_id', 'to_warehouse_id')
    def validate_warehouses(cls, v, values):
        if 'from_warehouse_id' in values and 'to_warehouse_id' in values:
            if values['from_warehouse_id'] == values['to_warehouse_id']:
                raise ValueError('Склады отправления и назначения не могут быть одинаковыми')
        return v


class StockReservation(BaseModel):
    quantity: Decimal

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше нуля')
        return v


class WarehouseStockSummary(BaseModel):
    total_quantity: float
    total_reserved: float
    total_available: float
    items_with_stock: int
    low_stock_items: int


class WarehouseStockDetail(BaseModel):
    id: int
    warehouse: Optional[WarehouseOut] = None
    item: Optional[ItemOut] = None
    quantity: Decimal
    reserved_quantity: Decimal
    min_quantity: Decimal
    max_quantity: Optional[Decimal] = None
    location: Optional[str] = None
    last_updated: datetime
    utilization_percent: Optional[float] = None
    is_low_stock: bool
    is_overstock: bool

    model_config = ConfigDict(from_attributes=True)


class LowStockWarehouse(BaseModel):
    warehouse: Optional[WarehouseOut] = None
    low_stock_items: List[Dict] = []

    model_config = ConfigDict(from_attributes=True)

class StockFilter(BaseModel):
    warehouse_id: Optional[int] = None
    item_id: Optional[int] = None
    low_stock: Optional[bool] = None
    search: Optional[str] = None 