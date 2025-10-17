from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.api.phones.models import PhoneIn, PhoneUpdate

from ..models import Phone


def get_phone(db: Session, phone_id: int) -> Optional[Phone]:
    """Получить запись телефона по ID"""
    return (
        db.query(Phone)
        .filter(Phone.id == phone_id, Phone.end_date > datetime.utcnow())
        .first()
    )


def get_phones(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    pay_date: Optional[int] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
) -> List[Phone]:
    """Получить все записи телефонов с фильтрацией"""
    query = (
        db.query(Phone)
        .filter(Phone.end_date > datetime.utcnow())
        .order_by(Phone.pay_date.asc())
    )

    if search:
        query = query.filter(
            (Phone.phone.ilike(f"%{search}%")) | (Phone.details.ilike(f"%{search}%"))
        )
    if pay_date is not None:
        try:
            pay_date_int = int(pay_date) if isinstance(pay_date, str) else pay_date
            query = query.filter(Phone.pay_date == pay_date_int)
        except (ValueError, TypeError):
            pass
    if start_date_from:
        try:
            from_date = datetime.fromisoformat(start_date_from.replace("Z", "+00:00"))
            query = query.filter(Phone.start_date >= from_date)
        except ValueError:
            pass
    if start_date_to:
        try:
            to_date = datetime.fromisoformat(start_date_to.replace("Z", "+00:00"))
            query = query.filter(Phone.start_date <= to_date)
        except ValueError:
            pass

    return query.offset(skip).limit(limit).all()


def get_phones_by_machine(
    db: Session, machine_id: int, skip: int = 0, limit: int = 100
) -> List[Phone]:
    """Получить записи телефонов для конкретного автомата"""
    return (
        db.query(Phone)
        .filter(Phone.machine_id == machine_id, Phone.end_date > datetime.utcnow())
        .order_by(Phone.pay_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_phones_by_number(
    db: Session, phone_number: str, skip: int = 0, limit: int = 100
) -> List[Phone]:
    """Получить записи телефонов по номеру"""
    return (
        db.query(Phone)
        .filter(Phone.phone == phone_number, Phone.end_date > datetime.utcnow())
        .order_by(Phone.pay_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_phone(db: Session, phone_data: PhoneIn) -> Phone:
    """Создать новую запись телефона"""
    # Валидация дня месяца
    if not 1 <= phone_data.pay_date <= 31:
        raise ValueError("pay_date must be between 1 and 31")

    db_phone = Phone(
        pay_date=phone_data.pay_date,
        phone=phone_data.phone,
        amount=phone_data.amount,
        details=phone_data.details,
        start_date=phone_data.start_date,
    )
    db.add(db_phone)
    db.commit()
    db.refresh(db_phone)
    return db_phone


def update_phone(
    db: Session, phone_id: int, phone_data: PhoneUpdate
) -> Optional[Phone]:
    """Обновить запись телефона"""
    phone_record = get_phone(db, phone_id)
    if not phone_record:
        return None

    if phone_data.pay_date is not None:
        # Валидация дня месяца
        if not 1 <= phone_data.pay_date <= 31:
            raise ValueError("pay_date must be between 1 and 31")
        phone_record.pay_date = phone_data.pay_date
    if phone_data.phone is not None:
        phone_record.phone = phone_data.phone
    if phone_data.amount is not None:
        phone_record.amount = phone_data.amount
    if phone_data.details is not None:
        phone_record.details = phone_data.details
    if phone_data.start_date is not None:
        phone_record.start_date = phone_data.start_date
    if phone_data.end_date is not None:
        phone_record.end_date = phone_data.end_date

    db.commit()
    db.refresh(phone_record)
    return phone_record


def delete_phone(db: Session, phone_id: int) -> bool:
    """Удалить запись телефона (мягкое удаление)"""
    phone_record = get_phone(db, phone_id)
    if not phone_record:
        return False

    phone_record.end_date = datetime.utcnow()
    db.commit()
    return True


def get_active_phones_by_machine(db: Session, machine_id: int) -> List[Phone]:
    """Получить активные телефоны для автомата (последние записи по каждому номеру)"""
    # Подзапрос для получения максимальных ID для каждого номера телефона
    from sqlalchemy import func

    subquery = (
        db.query(Phone.phone, func.max(Phone.id).label("max_id"))
        .filter(Phone.machine_id == machine_id, Phone.end_date > datetime.utcnow())
        .group_by(Phone.phone)
        .subquery()
    )

    return (
        db.query(Phone)
        .join(subquery, Phone.id == subquery.c.max_id)
        .filter(Phone.machine_id == machine_id, Phone.end_date > datetime.utcnow())
        .order_by(Phone.pay_date.asc())
        .all()
    )


def get_phone_summary(
    db: Session,
    machine_id: Optional[int] = None,
    phone_number: Optional[str] = None,
    pay_date: Optional[int] = None,
) -> dict:
    """Получить сводку по телефонам"""
    query = db.query(Phone).filter(Phone.end_date > datetime.utcnow())

    if machine_id is not None:
        query = query.filter(Phone.machine_id == machine_id)
    if phone_number is not None:
        query = query.filter(Phone.phone == phone_number)
    if pay_date is not None:
        query = query.filter(Phone.pay_date == pay_date)

    phones = query.all()

    total_amount = sum(phone.amount for phone in phones)
    unique_phones = len(set(phone.phone for phone in phones))

    return {
        "total_phones": len(phones),
        "unique_phone_numbers": unique_phones,
        "total_amount": float(total_amount),
        "average_amount": float(total_amount / len(phones)) if phones else 0.0,
    }
