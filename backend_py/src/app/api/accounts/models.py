from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict, validator
from decimal import Decimal
from app.api.reference_tables.models import ReferenceItemOut


class OwnerOut(BaseModel):
    id: int
    name: str
    inn: str

    model_config = ConfigDict(from_attributes=True)

class AccountOut(BaseModel):
    id: int
    name: str
    account_type: Optional[ReferenceItemOut] = None
    owner: Optional[OwnerOut] = None
    balance: Decimal
    initial_balance: Decimal
    currency: str
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    is_active: bool
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)

class AccountIn(BaseModel):
    name: str
    account_type_id: int
    owner_id: int
    balance: Optional[Decimal] = Decimal('0.00')
    initial_balance: Optional[Decimal] = Decimal('0.00')
    currency: str = 'RUB'
    account_number: Optional[str] = None
    bank_name: Optional[str] = None

    @validator('currency')
    def validate_currency(cls, v):
        if v not in ['RUB', 'USD', 'EUR']:
            raise ValueError('Поддерживаемые валюты: RUB, USD, EUR')
        return v



class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type_id: Optional[int] = None
    owner_id: Optional[int] = None
    balance: Optional[Decimal] = None
    initial_balance: Optional[Decimal] = None
    currency: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('currency')
    def validate_currency(cls, v):
        if v is not None and v not in ['RUB', 'USD', 'EUR']:
            raise ValueError('Поддерживаемые валюты: RUB, USD, EUR')
        return v


class AccountSummary(BaseModel):
    total_balance: float
    total_accounts: int
    currency_balances: Dict[str, float]


class AccountDetail(BaseModel):
    id: int
    name: str
    account_type: Optional[ReferenceItemOut] = None
    owner: Optional[OwnerOut] = None
    balance: Decimal
    initial_balance: Decimal
    currency: str
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    is_active: bool
    start_date: datetime
    end_date: datetime
    transactions_count: int
    last_transaction_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)