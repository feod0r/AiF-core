from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db

from . import controllers
from .models import (
    CashlessPaymentIn,
    CashlessPaymentOut,
    CashlessPaymentSummary,
    MonitoringIn,
    MonitoringOut,
    MonitoringSummary,
)

router = APIRouter()

# === Monitoring Routes ===


@router.get("/monitoring/all", response_model=List[MonitoringOut])
def read_monitoring_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    machine_id: int = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
):
    """Получить записи мониторинга с фильтрацией"""
    return controllers.get_monitoring_all(
        db, 
        skip=skip, 
        limit=limit,
        machine_id=machine_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/monitoring/{machine_id}", response_model=List[MonitoringOut])
def read_monitoring(
    machine_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
):
    """Получить записи мониторинга для автомата"""
    return controllers.get_monitoring(
        db, 
        machine_id, 
        skip=skip, 
        limit=limit,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/monitoring/{machine_id}/latest", response_model=MonitoringOut)
def read_latest_monitoring(machine_id: int, db: Session = Depends(get_db)):
    """Получить последнюю запись мониторинга для автомата"""
    return controllers.get_latest_monitoring(db, machine_id)


@router.post("/monitoring", response_model=MonitoringOut)
def create_monitoring(monitoring: MonitoringIn, db: Session = Depends(get_db)):
    """Создать новую запись мониторинга (при изменении показателей)"""
    return controllers.create_monitoring(db, monitoring)


@router.put("/monitoring/{monitoring_id}", response_model=MonitoringOut)
def update_monitoring(monitoring_id: int, monitoring: MonitoringIn, db: Session = Depends(get_db)):
    """Обновить запись мониторинга"""
    return controllers.update_monitoring(db, monitoring_id, monitoring)


@router.delete("/monitoring/{monitoring_id}")
def delete_monitoring(monitoring_id: int, db: Session = Depends(get_db)):
    """Удалить запись мониторинга"""
    return controllers.delete_monitoring(db, monitoring_id)


@router.get("/monitoring/{machine_id}/summary", response_model=MonitoringSummary)
def get_monitoring_summary(
    machine_id: int,
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Получить сводку мониторинга за период"""
    return controllers.get_monitoring_summary(db, machine_id, start_date, end_date)


# === Cashless Payments Routes ===


@router.get("/cashless-payments/{machine_id}", response_model=List[CashlessPaymentOut])
def read_cashless_payments(
    machine_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить записи безналичных платежей для автомата"""
    return controllers.get_cashless_payments(db, machine_id, skip=skip, limit=limit)


@router.post("/cashless-payments/{machine_id}/transaction")
def add_cashless_transaction(
    machine_id: int,
    amount: Decimal = Query(..., gt=0, description="Transaction amount"),
    db: Session = Depends(get_db),
):
    """Добавить новую безналичную транзакцию"""
    return controllers.add_cashless_transaction(db, machine_id, amount)


@router.post("/cashless-payments", response_model=CashlessPaymentOut)
def create_cashless_payment(payment: CashlessPaymentIn, db: Session = Depends(get_db)):
    """Создать или обновить запись безналичных платежей"""
    return controllers.create_cashless_payment(db, payment)


@router.get(
    "/cashless-payments/{machine_id}/summary", response_model=CashlessPaymentSummary
)
def get_cashless_payment_summary(
    machine_id: int,
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Получить сводку безналичных платежей за период"""
    return controllers.get_cashless_payment_summary(db, machine_id, start_date, end_date)
