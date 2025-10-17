from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.external.sqlalchemy.utils import rent as rent_crud

from .models import RentIn, RentUpdate


def get_rent(db: Session, rent_id: int):
    """Получить запись аренды по ID"""
    rent = rent_crud.get_rent(db, rent_id)
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


def get_rents(db: Session, skip: int = 0, limit: int = 100, search: str = None, pay_date: int = None, payer_id: int = None, start_date_from: str = None, start_date_to: str = None):
    """Получить все записи аренды"""
    return rent_crud.get_rents(db, skip=skip, limit=limit, search=search, pay_date=pay_date, payer_id=payer_id, start_date_from=start_date_from, start_date_to=start_date_to)


def get_rents_by_machine(db: Session, machine_id: int, skip: int = 0, limit: int = 100):
    """Получить записи аренды для конкретного автомата"""
    return rent_crud.get_rents_by_machine(db, machine_id, skip=skip, limit=limit)


def get_rents_by_payer(db: Session, payer_id: int, skip: int = 0, limit: int = 100):
    """Получить записи аренды для конкретного плательщика"""
    return rent_crud.get_rents_by_payer(db, payer_id, skip=skip, limit=limit)


def create_rent(db: Session, rent_in: RentIn):
    """Создать новую запись аренды"""
    return rent_crud.create_rent(db, rent_in)


def update_rent(db: Session, rent_id: int, rent_update: RentUpdate):
    """Обновить запись аренды"""
    rent = rent_crud.update_rent(db, rent_id=rent_id, rent_data=rent_update)
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


def delete_rent(db: Session, rent_id: int):
    """Удалить запись аренды"""
    success = rent_crud.delete_rent(db, rent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rent not found")
    return {"message": "Rent deleted successfully"}


def get_rent_summary(
    db: Session,
    payer_id: int = None,
    start_date: str = None,
    end_date: str = None,
):
    """Получить сводку по аренде"""
    from datetime import datetime

    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use ISO format (YYYY-MM-DD)",
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DD)",
            )

    return rent_crud.get_rent_summary(db, payer_id, start_dt, end_dt)
