from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TerminalOut(BaseModel):
    id: int
    terminal: Optional[int] = None
    name: str

    model_config = ConfigDict(from_attributes=True)


class AccountOut(BaseModel):
    id: int
    account_number: str
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class TerminalOperationOut(BaseModel):
    id: int
    operation_date: date
    terminal: TerminalOut
    amount: Decimal
    transaction_count: int
    commission: Decimal
    is_closed: bool
    closed_at: Optional[datetime] = None
    closed_by_user: Optional[UserOut] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TerminalOperationCreate(BaseModel):
    operation_date: date
    terminal_id: int
    amount: Decimal
    transaction_count: int
    commission: Decimal = Decimal("0.00")


class TerminalOperationUpdate(BaseModel):
    operation_date: Optional[date | datetime] = None
    amount: Optional[Decimal] = None
    transaction_count: Optional[int] = None
    commission: Optional[Decimal] = None


class CloseDayRequest(BaseModel):
    operation_date: date
    closed_by: int


class CloseDayResponse(BaseModel):
    success: bool
    message: str
    closed_operations_count: int
    total_amount_processed: Decimal
    affected_accounts: list[dict]


class TerminalOperationSummary(BaseModel):
    total_operations: int
    total_amount: Decimal
    total_commission: Decimal
    total_transactions: int
    closed_operations: int
    open_operations: int


class VendistaSyncRequest(BaseModel):
    sync_date: date


class VendistaSyncResponse(BaseModel):
    success: bool
    message: str
    synced_terminals: int
    total_amount: Decimal
    total_transactions: int
    errors: list[str] = []


class VendistaTerminalInfo(BaseModel):
    terminal_id: int
    terminal_name: str
    vendista_id: int
    owner_name: str
    vendista_user: str
    vendista_pass: str
