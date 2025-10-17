from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.api.owners.models import OwnerOut


class RentOut(BaseModel):
    id: int
    pay_date: int
    location: str
    amount: Decimal
    details: Optional[str] = None
    machine_id: Optional[int] = None
    payer_id: Optional[int] = None
    payer: Optional[OwnerOut] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RentIn(BaseModel):
    pay_date: int
    location: str
    amount: Decimal
    details: Optional[str] = None
    payer_id: Optional[int] = None
    start_date: datetime
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    end_date: Optional[datetime] = None

    @field_validator('latitude', 'longitude', mode='before')
    @classmethod
    def validate_coordinates(cls, v, info):
        if v is not None:
            try:
                # Очищаем от переносов строк и лишних символов
                clean_value = str(v).replace('\n', '').replace('\r', '').replace('\t', '').strip()
                parsed_value = float(clean_value)
                
                # Проверяем диапазон
                if info.field_name == 'latitude':
                    if parsed_value < -90 or parsed_value > 90:
                        raise ValueError('Широта должна быть в диапазоне от -90 до 90')
                else:  # longitude
                    if parsed_value < -180 or parsed_value > 180:
                        raise ValueError('Долгота должна быть в диапазоне от -180 до 180')
                
                return Decimal(str(parsed_value))
            except (ValueError, TypeError):
                raise ValueError('Некорректный формат координат')
        return v


class RentUpdate(BaseModel):
    pay_date: Optional[int] = None
    location: Optional[str] = None
    amount: Optional[Decimal] = None
    details: Optional[str] = None
    payer_id: Optional[int] = None
    start_date: datetime
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    end_date: Optional[datetime] = None


class RentSummary(BaseModel):
    total_amount: float
    rents_count: int
    average_amount: float
