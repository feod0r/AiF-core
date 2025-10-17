import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, validator
from app.api.reference_tables.models import ReferenceItemOut


class CounterpartyCategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CounterpartyOut(BaseModel):
    id: int
    name: str
    category: Optional[CounterpartyCategoryOut] = None
    category_id: Optional[int] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)


class CounterpartyIn(BaseModel):
    name: str
    category_id: Optional[int] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = None
    notes: Optional[str] = None

    @validator("inn")
    def validate_inn(cls, v):
        if v is not None and len(v) not in range(1, 20):
            raise ValueError("ИНН должен содержать от 1 до 20 цифр")
        return v

    @validator("kpp")
    def validate_kpp(cls, v):
        if v is not None and len(v) != 9:
            raise ValueError("КПП должен содержать 9 цифр")
        return v


class CounterpartyUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @validator("inn")
    def validate_inn(cls, v):
        if v is not None and len(v) not in range(1, 20):
            raise ValueError("ИНН должен содержать от 1 до 20 цифр")
        return v

    @validator("kpp")
    def validate_kpp(cls, v):
        if v is not None and len(v) != 9:
            raise ValueError("КПП должен содержать 9 цифр")
        return v
