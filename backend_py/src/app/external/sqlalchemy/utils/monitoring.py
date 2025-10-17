from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..models import Monitoring, Machine


def get_monitoring(
    db: Session,
    machine_id: int,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Monitoring]:
    """Получить записи мониторинга для конкретного автомата"""
    query = (
        db.query(Monitoring)
        .options(joinedload(Monitoring.machine))
        .filter(Monitoring.machine_id == machine_id)
        .order_by(Monitoring.date.desc())
    )

    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(Monitoring.date >= from_date)
        except ValueError:
            pass
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            query = query.filter(Monitoring.date <= to_date)
        except ValueError:
            pass

    return query.offset(skip).limit(limit).all()


def get_monitoring_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    machine_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Monitoring]:
    """Получить записи мониторинга с фильтрацией"""
    query = (
        db.query(Monitoring)
        .options(joinedload(Monitoring.machine))
        .order_by(Monitoring.date.desc())
    )

    if machine_id is not None:
        query = query.filter(Monitoring.machine_id == machine_id)
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(Monitoring.date >= from_date)
        except ValueError:
            pass
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            query = query.filter(Monitoring.date <= to_date)
        except ValueError:
            pass

    return query.offset(skip).limit(limit).all()


def get_monitoring_by_id(db: Session, monitoring_id: int) -> Optional[Monitoring]:
    """Получить запись мониторинга по ID"""
    return db.query(Monitoring).filter(Monitoring.id == monitoring_id).first()


def create_monitoring(
    db: Session, machine_id: int, coins: Decimal, toys: int, date: Optional[datetime]
) -> Monitoring:
    """Создать новую запись мониторинга"""
    db_monitoring = Monitoring(
        machine_id=machine_id,
        coins=coins,
        toys=toys,
        date=date if date else datetime.now(timezone.utc),
    )
    db.add(db_monitoring)
    db.commit()
    db.refresh(db_monitoring)
    return db_monitoring


def update_monitoring(
    db: Session, monitoring_id: int, machine_id: int, coins: Decimal, toys: int, date: Optional[datetime]
) -> Optional[Monitoring]:
    """Обновить запись мониторинга"""
    db_monitoring = db.query(Monitoring).filter(Monitoring.id == monitoring_id).first()
    if not db_monitoring:
        return None
    
    db_monitoring.machine_id = machine_id
    db_monitoring.coins = coins
    db_monitoring.toys = toys
    if date:
        db_monitoring.date = date
    
    db.commit()
    db.refresh(db_monitoring)
    return db_monitoring


def delete_monitoring(db: Session, monitoring_id: int) -> bool:
    """Удалить запись мониторинга"""
    db_monitoring = db.query(Monitoring).filter(Monitoring.id == monitoring_id).first()
    if not db_monitoring:
        return False
    
    db.delete(db_monitoring)
    db.commit()
    return True


def create_or_update_monitoring(
    db: Session, machine_id: int, coins: Decimal, toys: int, date: Optional[datetime]
) -> tuple[Monitoring, bool]:
    """Создать новую запись или обновить существующую по уникальному ключу
    Возвращает (monitoring_record, was_created)"""
    try:
        # Пытаемся создать новую запись
        monitoring = create_monitoring(
            db, machine_id, coins, toys, date if date else datetime.now(timezone.utc)
        )
        return monitoring, True  # Новая запись была создана
    except IntegrityError:
        # Если запись с таким ключом уже существует, обновляем дату
        db.rollback()
        existing = (
            db.query(Monitoring)
            .filter(
                Monitoring.machine_id == machine_id,
                Monitoring.coins == coins,
                Monitoring.toys == toys,
            )
            .first()
        )
        return existing, False  # Существующая запись была найдена
        # if existing:
        #     existing.date = datetime.now()
        #     db.commit()
        #     db.refresh(existing)
        #     return existing, False  # Существующая запись была обновлена
        # else:
        # raise


def get_latest_monitoring(db: Session, machine_id: int) -> Optional[Monitoring]:
    """Получить последнюю запись мониторинга для автомата"""
    return (
        db.query(Monitoring)
        .filter(Monitoring.machine_id == machine_id)
        .order_by(Monitoring.date.desc())
        .first()
    )


def get_monitoring_summary(
    db: Session, machine_id: int, start_date: datetime, end_date: datetime
) -> dict:
    """Получить сводку мониторинга за период"""
    records = (
        db.query(Monitoring)
        .filter(
            Monitoring.machine_id == machine_id,
            Monitoring.date >= start_date,
            Monitoring.date <= end_date,
        )
        .order_by(Monitoring.date.asc())
        .all()
    )

    if not records:
        return {
            "total_coins": 0,
            "total_toys": 0,
            "records_count": 0,
            "first_record": None,
            "last_record": None,
        }

    first_record = records[0]
    last_record = records[-1]

    return {
        "total_coins": float(last_record.coins - first_record.coins),
        "total_toys": last_record.toys - first_record.toys,
        "records_count": len(records),
        "first_record": first_record,
        "last_record": last_record,
    }
