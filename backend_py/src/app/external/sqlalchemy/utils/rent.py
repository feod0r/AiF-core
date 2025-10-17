from sqlalchemy.orm import Session
from ..models import Rent
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from app.api.rent.models import RentIn, RentUpdate


def get_rent(db: Session, rent_id: int) -> Optional[Rent]:
    """Получить запись аренды по ID"""
    return (
        db.query(Rent)
        .filter(Rent.id == rent_id, Rent.end_date > datetime.now(timezone.utc))
        .first()
    )


def get_rents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    pay_date: Optional[int] = None,
    payer_id: Optional[int] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
) -> List[Rent]:
    """Получить все записи аренды с фильтрацией"""
    query = (
        db.query(Rent)
        .filter(Rent.end_date > datetime.now(timezone.utc))
        .order_by(Rent.pay_date.desc())
    )

    if search:
        query = query.filter(
            (Rent.location.ilike(f"%{search}%")) | (Rent.details.ilike(f"%{search}%"))
        )
    if pay_date is not None:
        try:
            pay_date_int = int(pay_date) if isinstance(pay_date, str) else pay_date
            query = query.filter(Rent.pay_date == pay_date_int)
        except (ValueError, TypeError):
            pass
    if payer_id is not None:
        query = query.filter(Rent.payer_id == payer_id)
    if start_date_from:
        try:
            from_date = datetime.fromisoformat(start_date_from.replace("Z", "+00:00"))
            query = query.filter(Rent.start_date >= from_date)
        except ValueError:
            pass
    if start_date_to:
        try:
            to_date = datetime.fromisoformat(start_date_to.replace("Z", "+00:00"))
            query = query.filter(Rent.start_date <= to_date)
        except ValueError:
            pass

    return query.offset(skip).limit(limit).all()


def get_rents_by_machine(
    db: Session, machine_id: int, skip: int = 0, limit: int = 100
) -> List[Rent]:
    """Получить записи аренды для конкретного автомата"""
    return (
        db.query(Rent)
        .filter(
            Rent.machine_id == machine_id, Rent.end_date > datetime.now(timezone.utc)
        )
        .order_by(Rent.pay_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_rents_by_payer(
    db: Session, payer_id: int, skip: int = 0, limit: int = 100
) -> List[Rent]:
    """Получить записи аренды для конкретного плательщика"""
    return (
        db.query(Rent)
        .filter(Rent.payer_id == payer_id, Rent.end_date > datetime.now(timezone.utc))
        .order_by(Rent.pay_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_rent(db: Session, rent_data: RentIn) -> Rent:
    """Создать новую запись аренды"""
    db_rent = Rent(
        pay_date=rent_data.pay_date,
        location=rent_data.location,
        amount=rent_data.amount,
        details=rent_data.details,
        latitude=rent_data.latitude,
        longitude=rent_data.longitude,
        payer_id=rent_data.payer_id,
        start_date=rent_data.start_date,
        end_date=rent_data.end_date,
    )
    db.add(db_rent)
    db.commit()
    db.refresh(db_rent)
    return db_rent


def update_rent(db: Session, rent_id: int, rent_data: RentUpdate) -> Optional[Rent]:
    """Обновить запись аренды"""
    rent = get_rent(db, rent_id)
    if not rent:
        return None

    if rent_data.pay_date is not None:
        rent.pay_date = rent_data.pay_date
    if rent_data.location is not None:
        rent.location = rent_data.location
    if rent_data.amount is not None:
        rent.amount = rent_data.amount
    if rent_data.details is not None:
        rent.details = rent_data.details
    if rent_data.payer_id is not None:
        rent.payer_id = rent_data.payer_id
    if rent_data.latitude is not None:
        rent.latitude = rent_data.latitude
    if rent_data.longitude is not None:
        rent.longitude = rent_data.longitude
    if rent_data.start_date is not None:
        rent.start_date = rent_data.start_date
    if rent_data.end_date is not None:
        rent.end_date = rent_data.end_date

    db.commit()
    db.refresh(rent)
    return rent


def delete_rent(db: Session, rent_id: int) -> bool:
    """Удалить запись аренды (soft delete)"""
    rent = get_rent(db, rent_id)
    if not rent:
        return False

    rent.end_date = datetime.now(timezone.utc)
    db.commit()
    return True


def get_rent_summary(
    db: Session,
    machine_id: int = None,
    payer_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
) -> dict:
    """Получить сводку по аренде"""
    query = db.query(Rent).filter(Rent.end_date > datetime.now(timezone.utc))

    if machine_id:
        query = query.filter(Rent.machine_id == machine_id)
    if payer_id:
        query = query.filter(Rent.payer_id == payer_id)
    if start_date:
        query = query.filter(Rent.pay_date >= start_date)
    if end_date:
        query = query.filter(Rent.pay_date <= end_date)

    rents = query.all()

    total_amount = sum(float(rent.amount) for rent in rents)

    return {
        "total_amount": total_amount,
        "rents_count": len(rents),
        "average_amount": total_amount / len(rents) if rents else 0,
    }
