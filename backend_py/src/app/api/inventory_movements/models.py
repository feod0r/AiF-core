from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, validator

from app.api.accounts.models import OwnerOut
from app.api.item_categories.models import ItemCategoryOut
from app.api.reference_tables.models import ReferenceItemOut


class ItemOut(BaseModel):
    id: int
    name: str
    sku: str
    category: Optional[ItemCategoryOut] = None
    description: Optional[str] = None
    unit: str
    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    barcode: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class WarehouseOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    owner: Optional[OwnerOut] = None

    model_config = ConfigDict(from_attributes=True)


class MachineOut(BaseModel):
    id: int
    name: str
    game_cost: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class CounterpartyOut(BaseModel):
    id: int
    name: str
    inn: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class InventoryMovementItemOut(BaseModel):
    id: int
    item: ItemOut
    quantity: Decimal
    price: Decimal
    amount: Decimal
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryMovementItemIn(BaseModel):
    item_id: int
    quantity: Decimal
    price: Decimal
    description: Optional[str] = None

    @validator("quantity")
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Количество должно быть больше нуля")
        return v

    @validator("price")
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return v


class InventoryMovementOut(BaseModel):
    id: int
    movement_type: str
    document_date: datetime
    status: Optional[ReferenceItemOut] = None
    description: Optional[str] = None

    # Места отправления и назначения
    from_warehouse: Optional[WarehouseOut] = None
    to_warehouse: Optional[WarehouseOut] = None
    from_machine: Optional[MachineOut] = None
    to_machine: Optional[MachineOut] = None

    # Контрагенты и ответственные
    counterparty: Optional[CounterpartyOut] = None
    created_by_user: Optional[UserOut] = None
    approved_by_user: Optional[UserOut] = None
    executed_by_user: Optional[UserOut] = None

    # Даты
    created_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

    # Суммы
    total_amount: Decimal
    currency: str

    # Позиции
    items: List[InventoryMovementItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class InventoryMovementIn(BaseModel):
    movement_type: str
    document_date: Optional[datetime] = None
    status_id: int
    description: Optional[str] = None

    # Места отправления и назначения
    from_warehouse_id: Optional[int] = None
    to_warehouse_id: Optional[int] = None
    from_machine_id: Optional[int] = None
    to_machine_id: Optional[int] = None

    # Контрагенты и ответственные
    counterparty_id: Optional[int] = None
    created_by: Optional[int] = None
    currency: str = "RUB"

    # Позиции
    items: List[InventoryMovementItemIn]

    @validator("movement_type")
    def validate_movement_type(cls, v):
        valid_types = [
            "receipt",
            "issue",
            "transfer",
            "adjustment",
            "sale",
            "load_machine",
            "unload_machine",
        ]
        if v not in valid_types:
            raise ValueError(
                f"Тип движения должен быть одним из: {', '.join(valid_types)}"
            )
        return v

    @validator("items")
    def validate_items(cls, v):
        if not v:
            raise ValueError("Документ должен содержать хотя бы одну позицию")
        return v

    @validator("currency")
    def validate_currency(cls, v):
        if v not in ["RUB", "USD", "EUR"]:
            raise ValueError("Поддерживаемые валюты: RUB, USD, EUR")
        return v


class InventoryMovementUpdate(BaseModel):
    movement_type: Optional[str] = None
    document_date: Optional[datetime] = None
    status_id: Optional[int] = None
    description: Optional[str] = None

    # Места отправления и назначения
    from_warehouse_id: Optional[int] = None
    to_warehouse_id: Optional[int] = None
    from_machine_id: Optional[int] = None
    to_machine_id: Optional[int] = None

    # Контрагенты
    counterparty_id: Optional[int] = None
    currency: Optional[str] = None

    # Позиции
    items: Optional[List[InventoryMovementItemIn]] = None

    @validator("movement_type")
    def validate_movement_type(cls, v):
        if v is not None:
            valid_types = [
                "receipt",
                "issue",
                "transfer",
                "adjustment",
                "sale",
                "load_machine",
                "unload_machine",
            ]
            if v not in valid_types:
                raise ValueError(
                    f"Тип движения должен быть одним из: {', '.join(valid_types)}"
                )
        return v

    @validator("currency")
    def validate_currency(cls, v):
        if v is not None and v not in ["RUB", "USD", "EUR"]:
            raise ValueError("Поддерживаемые валюты: RUB, USD, EUR")
        return v


class InventoryMovementSummary(BaseModel):
    total_movements: int
    total_amount: float
    type_counts: Dict[str, int]
    type_amounts: Dict[str, float]
    status_counts: Dict[str, int]


class InventoryMovementDetail(BaseModel):
    id: int
    movement_type: str
    document_date: datetime
    status: Optional[ReferenceItemOut] = None
    description: Optional[str] = None

    # Места отправления и назначения
    from_warehouse: Optional[WarehouseOut] = None
    to_warehouse: Optional[WarehouseOut] = None
    from_machine: Optional[MachineOut] = None
    to_machine: Optional[MachineOut] = None

    # Контрагенты и ответственные
    counterparty: Optional[CounterpartyOut] = None
    created_by_user: Optional[UserOut] = None
    approved_by_user: Optional[UserOut] = None
    executed_by_user: Optional[UserOut] = None

    # Даты
    created_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

    # Суммы
    total_amount: Decimal
    currency: str

    # Позиции
    items: List[InventoryMovementItemOut] = []

    # Дополнительная информация
    is_approved: bool
    is_executed: bool
    can_edit: bool
    can_approve: bool
    can_execute: bool

    model_config = ConfigDict(from_attributes=True)


class MovementFilter(BaseModel):
    movement_type: Optional[str] = None
    status_id: Optional[int] = None
    counterparty_id: Optional[int] = None
    created_by: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    # Для фильтрации по конкретным местам
    from_warehouse_id: Optional[int] = None
    to_warehouse_id: Optional[int] = None
    from_machine_id: Optional[int] = None
    to_machine_id: Optional[int] = None


class MovementApproval(BaseModel):
    approved_by: int


class MovementExecution(BaseModel):
    executed_by: int


class BulkMovementApproval(BaseModel):
    approved_by: int
    movement_ids: List[int] = []


class BulkMovementExecution(BaseModel):
    executed_by: int
    movement_ids: List[int] = []


class BulkOperationResult(BaseModel):
    success_count: int
    error_count: int
    errors: List[Dict[str, str]] = []
    message: str
