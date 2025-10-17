from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models import CashlessPayment
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

def get_cashless_payment(db: Session, machine_id: int, payment_date: date) -> Optional[CashlessPayment]:
    """Получить запись безналичных платежей для автомата на конкретную дату"""
    return db.query(CashlessPayment).filter(
        CashlessPayment.machine_id == machine_id,
        CashlessPayment.date == payment_date
    ).first()

def get_cashless_payments(db: Session, machine_id: int, skip: int = 0, limit: int = 100) -> List[CashlessPayment]:
    """Получить записи безналичных платежей для автомата"""
    return db.query(CashlessPayment).filter(
        CashlessPayment.machine_id == machine_id
    ).order_by(CashlessPayment.date.desc()).offset(skip).limit(limit).all()

def create_cashless_payment(db: Session, machine_id: int, payment_date: date, 
                           amount: Decimal, transactions_count: int) -> CashlessPayment:
    """Создать новую запись безналичных платежей"""
    db_payment = CashlessPayment(
        machine_id=machine_id,
        date=payment_date,
        amount=amount,
        transactions_count=transactions_count
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def create_or_update_cashless_payment(db: Session, machine_id: int, payment_date: date, 
                                     amount: Decimal, transactions_count: int) -> CashlessPayment:
    """Создать или обновить запись безналичных платежей"""
    try:
        # Пытаемся создать новую запись
        return create_cashless_payment(db, machine_id, payment_date, amount, transactions_count)
    except IntegrityError:
        # Если запись на эту дату уже существует, обновляем
        db.rollback()
        existing = get_cashless_payment(db, machine_id, payment_date)
        if existing:
            existing.amount = amount
            existing.transactions_count = transactions_count
            db.commit()
            db.refresh(existing)
            return existing
        else:
            raise

def add_cashless_transaction(db: Session, machine_id: int, amount: Decimal) -> CashlessPayment:
    """Добавить новую безналичную транзакцию к существующей записи или создать новую"""
    today = date.today()
    existing = get_cashless_payment(db, machine_id, today)
    
    if existing:
        # Обновляем существующую запись
        existing.amount += amount
        existing.transactions_count += 1
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Создаем новую запись
        return create_cashless_payment(db, machine_id, today, amount, 1)

def get_cashless_summary(db: Session, machine_id: int, start_date: date, end_date: date) -> dict:
    """Получить сводку безналичных платежей за период"""
    payments = db.query(CashlessPayment).filter(
        CashlessPayment.machine_id == machine_id,
        CashlessPayment.date >= start_date,
        CashlessPayment.date <= end_date
    ).all()
    
    total_amount = sum(float(p.amount) for p in payments)
    total_transactions = sum(p.transactions_count for p in payments)
    
    return {
        "total_amount": total_amount,
        "total_transactions": total_transactions,
        "days_count": len(payments),
        "average_per_day": total_amount / len(payments) if payments else 0
    } 