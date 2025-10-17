from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, validator
from app.api.reference_tables.models import ReferenceItemOut


class ItemCategoryTypeOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ItemCategoryParentOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ItemCategoryOut(BaseModel):
    id: int
    name: str
    category_type: Optional[ItemCategoryTypeOut] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent: Optional[ItemCategoryParentOut] = None
    is_active: bool
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)

class ItemCategoryIn(BaseModel):
    name: str
    category_type_id: int
    description: Optional[str] = None
    parent_id: Optional[int] = None

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Название категории не может быть пустым')
        return v.strip()


class ItemCategoryUpdate(BaseModel):
    name: Optional[str] = None
    category_type_id: Optional[int] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Название категории не может быть пустым')
        return v.strip() if v is not None else v


class ItemCategoryTree(BaseModel):
    id: int
    name: str
    category_type_id: int
    description: Optional[str] = None
    parent_id: Optional[int] = None
    children: List['ItemCategoryTree'] = []

    model_config = ConfigDict(from_attributes=True)

class ItemCategoryPath(BaseModel):
    id: int
    name: str
    level: int

    model_config = ConfigDict(from_attributes=True)

class ItemCategorySummary(BaseModel):
    total_categories: int
    root_categories: int
    type_counts: Dict[str, int]


class ItemCategoryDetail(BaseModel):
    id: int
    name: str
    category_type: Optional[ItemCategoryTypeOut] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    is_active: bool
    start_date: datetime
    end_date: datetime
    children_count: int
    path: List[ItemCategoryPath]

    model_config = ConfigDict(from_attributes=True)

# Для рекурсивных ссылок
ItemCategoryTree.update_forward_refs() 