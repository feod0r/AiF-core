from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db
from app.external.sqlalchemy.models import Report
from .models import (
    ReportOut, ReportIn, ReportComputeResponse, ReportAggregateParams, ReportAggregateResponse,
    AccountingChartResponse, TransposedSumResponse, AccountingPeriodParams
)
from .controllers import (
    compute_and_store_reports, aggregate_reports, get_detailed_reports_by_period,
    get_accounting_chart_data, get_transposed_sum_by_categories,
    get_transposed_sum_by_counterparties, get_transposed_sum_by_machines
)


router = APIRouter()


@router.get("/reports", response_model=List[ReportOut])
def list_reports(
    report_date: datetime | None = Query(None, description="Filter by report date (day)"),
    db: Session = Depends(get_db),
):
    query = db.query(Report).order_by(Report.report_date.desc())
    if report_date:
        # normalize to date-only and filter by that day
        day = datetime(report_date.year, report_date.month, report_date.day)
        query = query.filter(Report.report_date == day)
    return query.all()


@router.post("/reports/compute", response_model=ReportComputeResponse)
def compute_reports(
    payload: ReportIn, db: Session = Depends(get_db)
):
    processed = compute_and_store_reports(db=db, report_date=payload.report_date)
    return ReportComputeResponse(processed=processed, report_date=payload.report_date)


@router.post("/reports/compute-by-date", response_model=ReportComputeResponse)
def compute_reports_by_date(
    date: datetime = Query(..., description="Дата отчета (день), формат ISO"),
    db: Session = Depends(get_db),
):
    processed = compute_and_store_reports(db=db, report_date=date)
    return ReportComputeResponse(processed=processed, report_date=date)


@router.get("/reports/aggregate", response_model=ReportAggregateResponse)
def aggregate_reports_endpoint(
    period: str = Query("daily", description="daily|weekly|monthly|quarterly|halfyear|yearly"),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    machine_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return aggregate_reports(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
        machine_id=machine_id,
    )


@router.get("/reports/detailed-by-period", response_model=List[ReportOut])
def detailed_reports_by_period(
    period: str = Query("daily", description="daily|weekly|monthly|quarterly|halfyear|yearly"),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    machine_id: int | None = Query(None, description="ID автомата для фильтрации"),
    db: Session = Depends(get_db),
):
    """Получить детальные отчеты по автоматам за указанный период"""
    return get_detailed_reports_by_period(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
        machine_id=machine_id,
    )


# --- Accounting Pivot эндпоинты ---

@router.get("/reports/accounting/chart", response_model=AccountingChartResponse, tags=["accounting"])
def get_accounting_chart(
    period: str = Query("monthly", description="daily|weekly|monthly|quarterly|yearly"),
    start_date: datetime | None = Query(None, description="Начальная дата"),
    end_date: datetime | None = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db),
):
    """Получить данные для диаграммы доходов/расходов"""
    return get_accounting_chart_data(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/reports/accounting/pivot-transposed/categories", response_model=TransposedSumResponse, tags=["accounting"])
def get_accounting_pivot_categories(
    period: str = Query("monthly", description="daily|weekly|monthly|quarterly|yearly"),
    start_date: datetime | None = Query(None, description="Начальная дата"),
    end_date: datetime | None = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db),
):
    """Получить транспонированную таблицу сумм по категориям операций"""
    return get_transposed_sum_by_categories(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/reports/accounting/pivot-transposed/counterparties", response_model=TransposedSumResponse, tags=["accounting"])
def get_accounting_pivot_counterparties(
    period: str = Query("monthly", description="daily|weekly|monthly|quarterly|yearly"),
    start_date: datetime | None = Query(None, description="Начальная дата"),
    end_date: datetime | None = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db),
):
    """Получить транспонированную таблицу сумм по контрагентам"""
    return get_transposed_sum_by_counterparties(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/reports/accounting/pivot-transposed/machines", response_model=TransposedSumResponse, tags=["accounting"])
def get_accounting_pivot_machines(
    period: str = Query("monthly", description="daily|weekly|monthly|quarterly|yearly"),
    start_date: datetime | None = Query(None, description="Начальная дата"),
    end_date: datetime | None = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db),
):
    """Получить транспонированную таблицу сумм по автоматам"""
    return get_transposed_sum_by_machines(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

