from datetime import datetime, date, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, validator
from decimal import Decimal
from app.api.reference_tables.models import ReferenceItemOut
from app.api.counterparties.models import CounterpartyOut
from app.api.transaction_categories.models import TransactionCategoryOut
from app.api.auth.models import UserResponse as UserOut
from app.api.owners.models import OwnerOut
from app.api.machines.models import MachineOut
from app.api.rent.models import RentOut


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

    model_config = ConfigDict(from_attributes=True)


class TransactionOut(BaseModel):
    id: int
    date: datetime
    account: AccountOut
    to_account: Optional[AccountOut] = None
    category: TransactionCategoryOut
    counterparty: Optional[CounterpartyOut] = None
    amount: Decimal
    transaction_type: ReferenceItemOut
    description: Optional[str] = None
    machine: Optional[MachineOut] = None
    rent_location: Optional[RentOut] = None
    reference_number: Optional[str] = None
    is_confirmed: bool
    created_by_user: Optional[UserOut] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionIn(BaseModel):
    date: Optional[datetime] = None
    account_id: int
    to_account_id: Optional[int] = None
    category_id: int
    counterparty_id: Optional[int] = None
    amount: Decimal
    transaction_type_id: int
    description: Optional[str] = None
    machine_id: Optional[int] = None
    rent_location_id: Optional[int] = None
    reference_number: Optional[str] = None
    is_confirmed: bool = False
    created_by: Optional[int] = None

    @validator("amount")
    def validate_amount(cls, v):
        if v == 0:
            raise ValueError("Сумма транзакции не может быть равна нулю")
        return v

    @validator("date")
    def validate_date(cls, v):
        if v is None:
            return datetime.now(timezone.utc)
        return v

    @validator("to_account_id")
    def validate_to_account_id(cls, v, values):
        # Проверяем, что для переводов указан счет назначения
        if (
            "transaction_type_id" in values and values["transaction_type_id"] == 3
        ):  # Предполагаем, что ID типа "перевод" = 3
            if v is None:
                raise ValueError("Для перевода необходимо указать счет назначения")
        return v


class TransactionUpdate(BaseModel):
    date: Optional[datetime] = None
    account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    category_id: Optional[int] = None
    counterparty_id: Optional[int] = None
    amount: Optional[Decimal] = None
    transaction_type_id: Optional[int] = None
    description: Optional[str] = None
    machine_id: Optional[int] = None
    rent_location_id: Optional[int] = None
    reference_number: Optional[str] = None
    is_confirmed: Optional[bool] = None

    @validator("amount")
    def validate_amount(cls, v):
        if v is not None and v == 0:
            raise ValueError("Сумма транзакции не может быть равна нулю")
        return v

    @validator("to_account_id")
    def validate_to_account_id(cls, v, values):
        # Проверяем, что для переводов указан счет назначения
        if (
            "transaction_type_id" in values and values["transaction_type_id"] == 3
        ):  # Предполагаем, что ID типа "перевод" = 3
            if v is None:
                raise ValueError("Для перевода необходимо указать счет назначения")
        return v


class TransactionSummary(BaseModel):
    income: float
    expense: float
    net: float
    total_transactions: int


class TransactionFilter(BaseModel):
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    counterparty_id: Optional[int] = None
    transaction_type_id: Optional[int] = None
    machine_id: Optional[int] = None
    date_from: Optional[date | datetime] = None
    date_to: Optional[date | datetime] = None
    is_confirmed: Optional[bool] = None
    search: Optional[str] = None
