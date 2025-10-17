from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from .models import PhoneIn, PhoneOut, PhoneUpdate, PhoneSummary
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List

router = APIRouter()

@router.get("/phones", response_model=List[PhoneOut])
def read_phones(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000),
    search: str = None,
    pay_date: int = None,
    start_date_from: str = None,
    start_date_to: str = None,
    db: Session = Depends(get_db)
):
    """Получить все записи телефонов с фильтрацией"""
    return controllers.get_phones(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        pay_date=pay_date,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )

@router.get("/phones/{phone_id}", response_model=PhoneOut)
def read_phone(phone_id: int, db: Session = Depends(get_db)):
    """Получить запись телефона по ID"""
    return controllers.get_phone(db, phone_id)

@router.post("/phones", response_model=PhoneOut)
def create_phone(phone: PhoneIn, db: Session = Depends(get_db)):
    """Создать новую запись телефона"""
    return controllers.create_phone(db, phone)

@router.put("/phones/{phone_id}", response_model=PhoneOut)
def update_phone(phone_id: int, phone: PhoneUpdate, db: Session = Depends(get_db)):
    """Обновить запись телефона"""
    return controllers.update_phone(db, phone_id, phone)

@router.delete("/phones/{phone_id}")
def delete_phone(phone_id: int, db: Session = Depends(get_db)):
    """Удалить запись телефона"""
    return controllers.delete_phone(db, phone_id)

@router.get("/phones/machine/{machine_id}", response_model=List[PhoneOut])
def read_phones_by_machine(
    machine_id: int,
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    db: Session = Depends(get_db)
):
    """Получить записи телефонов для конкретного автомата"""
    return controllers.get_phones_by_machine(db, machine_id, skip=skip, limit=limit)

@router.get("/phones/machine/{machine_id}/active", response_model=List[PhoneOut])
def read_active_phones_by_machine(machine_id: int, db: Session = Depends(get_db)):
    """Получить активные телефоны для автомата (последние записи по каждому номеру)"""
    return controllers.get_active_phones_by_machine(db, machine_id)

@router.get("/phones/number/{phone_number}", response_model=List[PhoneOut])
def read_phones_by_number(
    phone_number: str,
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    db: Session = Depends(get_db)
):
    """Получить записи телефонов по номеру"""
    return controllers.get_phones_by_number(db, phone_number, skip=skip, limit=limit)

@router.get("/phones/summary", response_model=PhoneSummary)
def get_phone_summary(
    machine_id: int = Query(None, description="Filter by machine ID"),
    phone_number: str = Query(None, description="Filter by phone number"),
    pay_date: int = Query(None, ge=1, le=31, description="Filter by day of month (1-31)"),
    db: Session = Depends(get_db)
):
    """Получить сводку по телефонам"""
    return controllers.get_phone_summary(db, machine_id, phone_number, pay_date) 