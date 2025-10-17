from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import PhoneIn, PhoneUpdate
from app.external.sqlalchemy.utils import phones as phone_crud
from typing import List


def get_phone(db: Session, phone_id: int):
    """Получить запись телефона по ID"""
    phone = phone_crud.get_phone(db, phone_id)
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")
    return phone


def get_phones(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    pay_date: int = None,
    start_date_from: str = None,
    start_date_to: str = None
):
    """Получить все записи телефонов с фильтрацией"""
    return phone_crud.get_phones(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        pay_date=pay_date,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )


def get_phones_by_machine(
    db: Session, machine_id: int, skip: int = 0, limit: int = 100
):
    """Получить записи телефонов для конкретного автомата"""
    return phone_crud.get_phones_by_machine(db, machine_id, skip=skip, limit=limit)


def get_phones_by_number(
    db: Session, phone_number: str, skip: int = 0, limit: int = 100
):
    """Получить записи телефонов по номеру"""
    return phone_crud.get_phones_by_number(db, phone_number, skip=skip, limit=limit)


def get_active_phones_by_machine(db: Session, machine_id: int):
    """Получить активные телефоны для автомата"""
    return phone_crud.get_active_phones_by_machine(db, machine_id)


def create_phone(db: Session, phone_in: PhoneIn):
    """Создать новую запись телефона"""
    try:
        return phone_crud.create_phone(db, phone_data=phone_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def update_phone(db: Session, phone_id: int, phone_update: PhoneUpdate):
    """Обновить запись телефона"""
    try:
        phone = phone_crud.update_phone(db, phone_id=phone_id, phone_data=phone_update)
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        return phone
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def delete_phone(db: Session, phone_id: int):
    """Удалить запись телефона"""
    success = phone_crud.delete_phone(db, phone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Phone not found")
    return {"message": "Phone deleted successfully"}


def get_phone_summary(
    db: Session, machine_id: int = None, phone_number: str = None, pay_date: int = None
):
    """Получить сводку по телефонам"""
    try:
        return phone_crud.get_phone_summary(db, machine_id, phone_number, pay_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
