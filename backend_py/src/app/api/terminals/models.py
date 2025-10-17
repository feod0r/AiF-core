from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.api.owners.models import OwnerOut


class AccountOut(BaseModel):
    id: int
    name: str
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class TerminalOut(BaseModel):
    id: int
    terminal: Optional[int] = None
    name: str
    owner_id: Optional[int] = None
    account_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    owner: Optional[OwnerOut] = None
    account: Optional[AccountOut] = None

    model_config = ConfigDict(from_attributes=True)


class TerminalIn(BaseModel):
    name: str
    terminal: Optional[int] = None
    owner_id: Optional[int] = None
    account_id: Optional[int] = None
    start_date: Optional[date | datetime] = None
    end_date: Optional[date | datetime] = None


class TerminalUpdate(BaseModel):
    name: Optional[str] = None
    terminal: Optional[int] = None
    owner_id: Optional[int] = None
    account_id: Optional[int] = None
    start_date: Optional[date | datetime] = None
    end_date: Optional[date | datetime] = None
