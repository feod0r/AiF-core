from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.api.terminals.models import TerminalOut
from app.api.rent.models import RentOut
from app.api.phones.models import PhoneOut


class MachineOut(BaseModel):
    id: int
    name: str
    game_cost: Optional[Decimal] = None
    terminal_id: Optional[int] = None
    rent_id: Optional[int] = None
    phone_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    terminal: Optional[TerminalOut] = None
    rent: Optional[RentOut] = None
    phone: Optional[PhoneOut] = None

    model_config = ConfigDict(from_attributes=True)


class MachineIn(BaseModel):
    name: str
    game_cost: Optional[Decimal] = None
    terminal_id: Optional[int] = None
    rent_id: Optional[int] = None
    phone_id: Optional[int] = None
    start_date: Optional[date | datetime] = None
    end_date: Optional[date | datetime] = None


class MachineUpdate(BaseModel):
    name: Optional[str] = None
    game_cost: Optional[Decimal] = None
    terminal_id: Optional[int] = None
    rent_id: Optional[int] = None
    phone_id: Optional[int] = None
    start_date: Optional[date | datetime] = None
    end_date: Optional[date | datetime] = None
