from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, validator
from decimal import Decimal
from app.api.reference_tables.models import ReferenceItemOut
from app.api.item_categories.models import ItemCategoryOut


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
    min_stock: Decimal
    max_stock: Optional[Decimal] = None
    is_active: bool
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemIn(BaseModel):
    name: str
    sku: str
    category_id: int
    description: Optional[str] = None
    unit: str = "шт"
    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    barcode: Optional[str] = None
    min_stock: Decimal = Decimal('0')
    max_stock: Optional[Decimal] = None

    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Название товара не может быть пустым")
        return v.strip()

    @validator("sku")
    def validate_sku(cls, v):
        if not v or not v.strip():
            raise ValueError("SKU не может быть пустым")
        return v.strip()

    @validator("category_id")
    def validate_category_id(cls, v):
        if v <= 0:
            raise ValueError("ID категории должен быть больше нуля")
        return v

    @validator("unit")
    def validate_unit(cls, v):
        valid_units = ["шт", "кг", "л", "м", "м²", "м³", "упак", "компл"]
        if v not in valid_units:
            raise ValueError(
                f"Единица измерения должна быть одной из: {', '.join(valid_units)}"
            )
        return v

    @validator("weight")
    def validate_weight(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Вес должен быть больше нуля")
        return v

    @validator("barcode")
    def validate_barcode(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Штрихкод не может быть пустым")
        return v.strip() if v else None

    @validator("min_stock")
    def validate_min_stock(cls, v):
        if v is not None and v < 0:
            raise ValueError("Минимальный остаток не может быть отрицательным")
        return v

    @validator("max_stock")
    def validate_max_stock(cls, v):
        if v is not None and v < 0:
            raise ValueError("Максимальный остаток не может быть отрицательным")
        return v


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    barcode: Optional[str] = None
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    is_active: Optional[bool] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Название товара не может быть пустым")
        return v.strip() if v else None

    @validator("sku")
    def validate_sku(cls, v):
        if v is not None and not v.strip():
            raise ValueError("SKU не может быть пустым")
        return v.strip() if v else None

    @validator("category_id")
    def validate_category_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("ID категории должен быть больше нуля")
        return v

    @validator("unit")
    def validate_unit(cls, v):
        if v is not None:
            valid_units = ["шт", "кг", "л", "м", "м²", "м³", "упак", "компл"]
            if v not in valid_units:
                raise ValueError(
                    f"Единица измерения должна быть одной из: {', '.join(valid_units)}"
                )
        return v

    @validator("weight")
    def validate_weight(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Вес должен быть больше нуля")
        return v

    @validator("barcode")
    def validate_barcode(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Штрихкод не может быть пустым")
        return v.strip() if v else None

    @validator("min_stock")
    def validate_min_stock(cls, v):
        if v is not None and v < 0:
            raise ValueError("Минимальный остаток не может быть отрицательным")
        return v

    @validator("max_stock")
    def validate_max_stock(cls, v):
        if v is not None and v < 0:
            raise ValueError("Максимальный остаток не может быть отрицательным")
        return v


class ItemWithStockInfo(BaseModel):
    id: int
    name: str
    sku: Optional[str] = None
    category: Optional[ItemCategoryOut] = None
    description: Optional[str] = None
    unit: str
    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    barcode: Optional[str] = None
    is_active: bool
    total_warehouse_quantity: float
    total_machine_quantity: float
    total_reserved: float
    available_quantity: float
    warehouse_quantity: Optional[float] = None
    warehouse_reserved: Optional[float] = None
    warehouse_available: Optional[float] = None
    warehouse_location: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ItemSummary(BaseModel):
    total_items: int
    items_with_stock: int
    items_without_stock: int
    total_warehouse_quantity: float
    total_machine_quantity: float
    total_reserved: float
    total_available: float


class ItemDetail(BaseModel):
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
    start_date: datetime
    end_date: datetime
    total_warehouse_quantity: float
    total_machine_quantity: float
    total_reserved: float
    available_quantity: float
    warehouse_stocks: List[Dict] = []
    machine_stocks: List[Dict] = []

    model_config = ConfigDict(from_attributes=True)


class ItemFilter(BaseModel):
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    has_stock: Optional[bool] = None
    search: Optional[str] = None


class LowStockItem(BaseModel):
    id: int
    name: str
    sku: Optional[str]
    category: Optional[ItemCategoryOut] = None
    current_quantity: float
    min_quantity: float
    warehouse: Optional[Dict] = None

    model_config = ConfigDict(from_attributes=True)
