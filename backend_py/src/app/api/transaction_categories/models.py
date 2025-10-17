from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.api.reference_tables.models import ReferenceItemOut


class TransactionTypeOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TransactionCategoryOut(BaseModel):
    id: int
    name: str
    transaction_type_id: int
    transaction_type: Optional[TransactionTypeOut] = None
    description: Optional[str] = None
    is_active: bool
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionCategoryIn(BaseModel):
    name: str
    transaction_type_id: int
    description: Optional[str] = None


class TransactionCategoryUpdate(BaseModel):
    name: Optional[str] = None
    transaction_type_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None 