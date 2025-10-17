from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db

from . import controllers
from .models import RentIn, RentOut, RentSummary, RentUpdate

router = APIRouter()


@router.get("/rent", response_model=List[RentOut])
def read_rents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Search by location or details"),
    pay_date: int = Query(None, description="Filter by pay date (1-31)"),
    payer_id: int = Query(None, description="Filter by payer ID"),
    start_date_from: str = Query(None, description="Start date from in ISO format"),
    start_date_to: str = Query(None, description="Start date to in ISO format"),
    db: Session = Depends(get_db),
):
    """Получить все записи аренды"""
    return controllers.get_rents(db, skip=skip, limit=limit, search=search, pay_date=pay_date, payer_id=payer_id, start_date_from=start_date_from, start_date_to=start_date_to)


@router.get("/rent/{rent_id}", response_model=RentOut)
def read_rent(rent_id: int, db: Session = Depends(get_db)):
    """Получить запись аренды по ID"""
    return controllers.get_rent(db, rent_id)


@router.post("/rent", response_model=RentOut)
def create_rent(rent: RentIn, db: Session = Depends(get_db)):
    """Создать новую запись аренды"""
    return controllers.create_rent(db, rent)


@router.put("/rent/{rent_id}", response_model=RentOut)
def update_rent(rent_id: int, rent: RentUpdate, db: Session = Depends(get_db)):
    """Обновить запись аренды"""
    return controllers.update_rent(db, rent_id, rent)


@router.delete("/rent/{rent_id}")
def delete_rent(rent_id: int, db: Session = Depends(get_db)):
    """Удалить запись аренды"""
    return controllers.delete_rent(db, rent_id)


@router.get("/rent/machine/{machine_id}", response_model=List[RentOut])
def read_rents_by_machine(
    machine_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить записи аренды для конкретного автомата"""
    return controllers.get_rents_by_machine(db, machine_id, skip=skip, limit=limit)


@router.get("/rent/payer/{payer_id}", response_model=List[RentOut])
def read_rents_by_payer(
    payer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить записи аренды для конкретного плательщика"""
    return controllers.get_rents_by_payer(db, payer_id, skip=skip, limit=limit)


@router.get("/rent/summary", response_model=RentSummary)
def get_rent_summary(
    machine_id: int = Query(None, description="Filter by machine ID"),
    payer_id: int = Query(None, description="Filter by payer ID"),
    start_date: str = Query(None, description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date in ISO format (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Получить сводку по аренде"""
    return controllers.get_rent_summary(db, machine_id, payer_id, start_date, end_date)
