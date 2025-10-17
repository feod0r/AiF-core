from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, validator
from decimal import Decimal
from app.api.items.models import ItemOut
from app.api.machines.models import MachineOut


class MachineStockOut(BaseModel):
    id: int
    machine: Optional[MachineOut] = None
    item: Optional[ItemOut] = None
    quantity: Decimal
    capacity: Optional[Decimal] = None
    min_quantity: Decimal
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class MachineStockIn(BaseModel):
    machine_id: int
    item_id: int
    quantity: Decimal = Decimal('0')
    capacity: Optional[Decimal] = None
    min_quantity: Decimal = Decimal('0')

    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Количество не может быть отрицательным')
        return v

    @validator('capacity')
    def validate_capacity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Вместимость должна быть больше нуля')
        return v

    @validator('min_quantity')
    def validate_min_quantity(cls, v):
        if v < 0:
            raise ValueError('Минимальное количество не может быть отрицательным')
        return v


class MachineStockUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    capacity: Optional[Decimal] = None
    min_quantity: Optional[Decimal] = None

    @validator('quantity')
    def validate_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Количество не может быть отрицательным')
        return v

    @validator('capacity')
    def validate_capacity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Вместимость должна быть больше нуля')
        return v

    @validator('min_quantity')
    def validate_min_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Минимальное количество не может быть отрицательным')
        return v


class MachineStockOperation(BaseModel):
    quantity: Decimal

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше нуля')
        return v


class MachineStockTransfer(BaseModel):
    from_machine_id: int
    to_machine_id: int
    item_id: int
    quantity: Decimal

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше нуля')
        return v

    @validator('from_machine_id', 'to_machine_id')
    def validate_machines(cls, v, values):
        if 'from_machine_id' in values and 'to_machine_id' in values:
            if values['from_machine_id'] == values['to_machine_id']:
                raise ValueError('Автоматы отправления и назначения не могут быть одинаковыми')
        return v


class MachineLoadOperation(BaseModel):
    warehouse_id: int
    quantity: Decimal

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше нуля')
        return v


class MachineUnloadOperation(BaseModel):
    warehouse_id: int
    quantity: Decimal

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше нуля')
        return v


class MachineStockSummary(BaseModel):
    total_quantity: float
    total_capacity: float
    total_utilization: float
    machines_with_stock: int
    low_stock_machines: int
    full_machines: int


class MachineStockDetail(BaseModel):
    id: int
    machine: Optional[MachineOut] = None
    item: Optional[ItemOut] = None
    quantity: Decimal
    capacity: Optional[Decimal] = None
    min_quantity: Decimal
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class LowStockMachine(BaseModel):
    machine: Optional[MachineOut] = None
    low_stock_items: List[Dict] = []

    model_config = ConfigDict(from_attributes=True)

class MachineUtilization(BaseModel):
    machine_id: int
    machine_name: Optional[str] = None
    total_capacity: float
    total_quantity: float
    utilization_percent: float
    items_count: int
    low_stock_items: int
    full_items: int

    model_config = ConfigDict(from_attributes=True)

class MachineStockFilter(BaseModel):
    machine_id: Optional[int] = None
    item_id: Optional[int] = None
    low_stock: Optional[bool] = None
    full_machines: Optional[bool] = None
    search: Optional[str] = None 