from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from ..models import Machine
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from app.api.machines.models import MachineUpdate


def get_machine(db: Session, machine_id: int) -> Optional[Machine]:
    """Получить автомат по ID с связями"""
    return (
        db.query(Machine)
        .filter(Machine.id == machine_id)
        .filter(
            or_(Machine.end_date == None, Machine.end_date > datetime.now(timezone.utc))
        )
        .first()
    )


def get_machines(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    terminal_id: Optional[int] = None,
    rent_id: Optional[int] = None,
    phone_id: Optional[int] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
) -> List[Machine]:
    """Получить список автоматов с фильтрацией и связями"""
    query = db.query(Machine)

    # Фильтр по активности
    if is_active is not None:
        if is_active:
            query = query.filter(
                or_(
                    Machine.end_date == None,
                    Machine.end_date > datetime.now(timezone.utc),
                )
            )
        else:
            query = query.filter(Machine.end_date != None)
    else:
        query = query.filter(
            or_(Machine.end_date == None, Machine.end_date > datetime.now(timezone.utc))
        )

    # Поиск по названию
    if search:
        query = query.filter(Machine.name.ilike(f"%{search}%"))

    # Фильтр по терминалу
    if terminal_id is not None:
        query = query.filter(Machine.terminal_id == terminal_id)

    # Фильтр по аренде
    if rent_id is not None:
        query = query.filter(Machine.rent_id == rent_id)

    # Фильтр по телефону
    if phone_id is not None:
        query = query.filter(Machine.phone_id == phone_id)

    # Фильтр по дате начала
    if start_date_from:
        try:
            start_from_date = datetime.fromisoformat(
                start_date_from.replace("Z", "+00:00")
            )
            query = query.filter(Machine.start_date >= start_from_date)
        except ValueError:
            pass

    if start_date_to:
        try:
            start_to_date = datetime.fromisoformat(start_date_to.replace("Z", "+00:00"))
            query = query.filter(Machine.start_date <= start_to_date)
        except ValueError:
            pass

    return query.offset(skip).limit(limit).all()


def get_machine_by_name(db: Session, name: str) -> Optional[Machine]:
    """Получить автомат по названию с связями"""
    return (
        db.query(Machine)
        .options(
            joinedload(Machine.terminal),
            joinedload(Machine.phones),
            joinedload(Machine.rents),
        )
        .filter(
            Machine.name == name,
            or_(Machine.end_date == None, Machine.end_date > datetime.now()),
        )
        .first()
    )


def create_machine(db: Session, machine_data) -> Machine:
    """Создать новый автомат"""
    db_machine = Machine(
        name=machine_data.name,
        terminal_id=machine_data.terminal_id
        if hasattr(machine_data, "terminal_id")
        else None,
        game_cost=machine_data.game_cost
        if hasattr(machine_data, "game_cost")
        else None,
        rent_id=machine_data.rent_id if hasattr(machine_data, "rent_id") else None,
        phone_id=machine_data.phone_id if hasattr(machine_data, "phone_id") else None,
        start_date=machine_data.start_date
        if hasattr(machine_data, "start_date") and machine_data.start_date
        else datetime.now(timezone.utc),
        end_date=machine_data.end_date
        if hasattr(machine_data, "end_date") and machine_data.end_date
        else datetime(9999, 12, 31, 0, 0, 0),
    )
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine


def update_machine(
    db: Session, machine_id: int, machine_data: MachineUpdate
) -> Optional[Machine]:
    """Обновить автомат"""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        return None

    # Обновляем только переданные поля
    if machine_data.name is not None:
        machine.name = machine_data.name
    if machine_data.game_cost is not None:
        machine.game_cost = machine_data.game_cost
    if machine_data.terminal_id is not None:
        machine.terminal_id = machine_data.terminal_id
    if machine_data.phone_id is not None:
        machine.phone_id = machine_data.phone_id
    if machine_data.rent_id is not None:
        machine.rent_id = machine_data.rent_id
    if machine_data.start_date is not None:
        machine.start_date = machine_data.start_date
    if machine_data.end_date is not None:
        machine.end_date = machine_data.end_date

    db.commit()
    db.refresh(machine)
    return machine


def delete_machine(db: Session, machine_id: int) -> bool:
    """Мягкое удаление автомата (soft delete)"""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        return False

    machine.end_date = datetime.now(timezone.utc)
    db.commit()
    return True


def get_machines_summary(db: Session) -> dict:
    """Получить сводку по автоматам"""
    total_machines = db.query(Machine).count()

    # Активные автоматы
    active_machines = (
        db.query(Machine)
        .filter(
            or_(Machine.end_date == None, Machine.end_date > datetime.now(timezone.utc))
        )
        .count()
    )

    return {"total_machines": total_machines, "active_machines": active_machines}
