from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.api.machines.models import MachineOut


class ReportOut(BaseModel):
    id: int
    report_date: datetime
    machine_id: int
    revenue: Decimal
    toy_consumption: int
    plays_per_toy: Decimal
    profit: Decimal
    days_count: int
    rent_cost: Decimal
    machine: Optional[MachineOut] = None

    model_config = ConfigDict(from_attributes=True)


class ReportIn(BaseModel):
    report_date: datetime


class ReportComputeResponse(BaseModel):
    processed: int
    report_date: datetime


class ReportAggregateParams(BaseModel):
    period: str = "daily"  # daily, weekly, monthly, quarterly, halfyear, yearly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    machine_id: Optional[int] = None


class ChartDataPoint(BaseModel):
    period: str
    total_toys_sold: float
    total_coins_earned: float
    total_profit: float
    total_revenue: float
    total_rent_cost: float
    records_count: int


class ReportAggregateResponse(BaseModel):
    success: bool
    period: str
    data: list[ChartDataPoint]


# --- Модели для Accounting Pivot ---

class ChartDataset(BaseModel):
    label: str
    data: list[float]
    backgroundColor: str
    borderColor: str
    borderWidth: int = 1


class AccountingChartData(BaseModel):
    labels: list[str]
    datasets: list[ChartDataset]


class AccountingChartResponse(BaseModel):
    success: bool = True
    data: AccountingChartData
    period: str


class TransposedSumRow(BaseModel):
    name: str
    # Динамические поля для периодов будут добавляться как дополнительные атрибуты
    
    model_config = ConfigDict(extra='allow')


class TransposedSumResponse(BaseModel):
    success: bool = True
    periods: list[str]
    rows: list[TransposedSumRow]


class AccountingPeriodParams(BaseModel):
    period: str = "monthly"  # daily, weekly, monthly, quarterly, yearly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

