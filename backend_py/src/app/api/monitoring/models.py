from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.api.machines.models import MachineOut


class MonitoringOut(BaseModel):
    id: int
    date: datetime
    coins: Decimal
    toys: int
    machine_id: int
    machine: Optional[MachineOut] = None
    model_config = ConfigDict(from_attributes=True)


class MonitoringIn(BaseModel):
    machine_id: int
    coins: Decimal
    toys: int
    date: Optional[datetime] = None


class MonitoringSummary(BaseModel):
    total_coins: float
    total_toys: int
    records_count: int
    first_record: Optional[MonitoringOut] = None
    last_record: Optional[MonitoringOut] = None


class CashlessPaymentOut(BaseModel):
    id: int
    date: date
    amount: Decimal
    transactions_count: int
    machine_id: int
    machine: Optional[MachineOut] = None

    model_config = ConfigDict(from_attributes=True)


class CashlessPaymentIn(BaseModel):
    machine_id: int
    amount: Decimal
    transactions_count: int = 1


class CashlessPaymentSummary(BaseModel):
    total_amount: float
    total_transactions: int
    days_count: int
    average_per_day: float
