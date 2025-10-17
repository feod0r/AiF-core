from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.external.sqlalchemy.utils import cashless_payments as cashless_crud
from app.external.sqlalchemy.utils import monitoring as monitoring_crud

from .models import CashlessPaymentIn, MonitoringIn

# === Monitoring Controllers ===


def get_monitoring(
    db: Session, 
    machine_id: int, 
    skip: int = 0, 
    limit: int = 100,
    date_from: str = None,
    date_to: str = None
):
    """Получить записи мониторинга для автомата"""
    return monitoring_crud.get_monitoring(
        db, 
        machine_id, 
        skip=skip, 
        limit=limit,
        date_from=date_from,
        date_to=date_to
    )


def get_monitoring_all(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    machine_id: int = None,
    date_from: str = None,
    date_to: str = None
):
    """Получить записи мониторинга с фильтрацией"""
    return monitoring_crud.get_monitoring_all(
        db, 
        skip=skip, 
        limit=limit,
        machine_id=machine_id,
        date_from=date_from,
        date_to=date_to
    )


def get_latest_monitoring(db: Session, machine_id: int):
    """Получить последнюю запись мониторинга для автомата"""
    monitoring = monitoring_crud.get_latest_monitoring(db, machine_id)
    if not monitoring:
        raise HTTPException(
            status_code=404, detail="No monitoring records found for this machine"
        )
    return monitoring


def create_monitoring(db: Session, monitoring_in: MonitoringIn):
    """Создать новую запись мониторинга"""
    from app.api.reports.controllers import compute_and_store_reports

    monitoring, was_created = monitoring_crud.create_or_update_monitoring(
        db,
        machine_id=monitoring_in.machine_id,
        coins=monitoring_in.coins,
        toys=monitoring_in.toys,
        date=monitoring_in.date,
    )

    # Если была создана новая запись (не обновлена существующая), создаем отчет за день
    if was_created:
        try:
            # Используем дату записи мониторинга для создания отчета
            report_date = monitoring.date if monitoring.date else monitoring_in.date
            if report_date:
                processed = compute_and_store_reports(db, report_date)
                print(
                    f"Автоматически создан отчет за {report_date.strftime('%d.%m.%Y')}. Обработано автоматов: {processed}"
                )
        except Exception as e:
            # Логируем ошибку, но не прерываем создание записи мониторинга
            print(f"Ошибка при автоматическом создании отчета: {e}")

    return monitoring


def update_monitoring(db: Session, monitoring_id: int, monitoring_in: MonitoringIn):
    """Обновить запись мониторинга"""
    existing_monitoring = monitoring_crud.get_monitoring_by_id(db, monitoring_id)
    if not existing_monitoring:
        raise HTTPException(
            status_code=404, detail="Monitoring record not found"
        )
    
    return monitoring_crud.update_monitoring(
        db,
        monitoring_id=monitoring_id,
        machine_id=monitoring_in.machine_id,
        coins=monitoring_in.coins,
        toys=monitoring_in.toys,
        date=monitoring_in.date,
    )


def delete_monitoring(db: Session, monitoring_id: int):
    """Удалить запись мониторинга"""
    existing_monitoring = monitoring_crud.get_monitoring_by_id(db, monitoring_id)
    if not existing_monitoring:
        raise HTTPException(
            status_code=404, detail="Monitoring record not found"
        )
    
    monitoring_crud.delete_monitoring(db, monitoring_id)
    return {"message": "Monitoring record deleted successfully"}


def get_monitoring_summary(
    db: Session, machine_id: int, start_date: str, end_date: str
):
    """Получить сводку мониторинга за период"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)"
        )

    return monitoring_crud.get_monitoring_summary(db, machine_id, start, end)


# === Cashless Payments Controllers ===


def get_cashless_payments(
    db: Session, machine_id: int, skip: int = 0, limit: int = 100
):
    """Получить записи безналичных платежей для автомата"""
    return cashless_crud.get_cashless_payments(db, machine_id, skip=skip, limit=limit)


def add_cashless_transaction(db: Session, machine_id: int, amount: Decimal):
    """Добавить новую безналичную транзакцию"""
    return cashless_crud.add_cashless_transaction(db, machine_id, amount)


def create_cashless_payment(db: Session, payment_in: CashlessPaymentIn):
    """Создать или обновить запись безналичных платежей"""
    today = date.today()
    return cashless_crud.create_or_update_cashless_payment(
        db,
        machine_id=payment_in.machine_id,
        payment_date=today,
        amount=payment_in.amount,
    )


def get_cashless_payment_summary(
    db: Session, machine_id: int, start_date: str, end_date: str
):
    """Получить сводку безналичных платежей за период"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)"
        )

    return cashless_crud.get_cashless_payment_summary(db, machine_id, start, end)
