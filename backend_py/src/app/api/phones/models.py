from pydantic import BaseModel, ConfigDict, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PhoneOut(BaseModel):
    id: int
    pay_date: int  # День месяца (1-31)
    phone: str
    amount: Decimal
    details: Optional[str] = None
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PhoneIn(BaseModel):
    pay_date: int  # День месяца (1-31)
    phone: str
    amount: Decimal
    details: Optional[str] = None
    start_date: Optional[datetime] = None

    @validator("pay_date")
    def validate_pay_date(cls, v):
        if not 1 <= v <= 31:
            raise ValueError("pay_date must be between 1 and 31")
        return v


class PhoneUpdate(BaseModel):
    pay_date: Optional[int] = None  # День месяца (1-31)
    phone: Optional[str] = None
    amount: Optional[Decimal] = None
    details: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @validator("pay_date")
    def validate_pay_date(cls, v):
        if v is not None and not 1 <= v <= 31:
            raise ValueError("pay_date must be between 1 and 31")
        return v


class PhoneSummary(BaseModel):
    total_amount: float
    phones_count: int
    average_amount: float
