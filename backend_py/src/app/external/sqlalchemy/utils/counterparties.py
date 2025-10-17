from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..models import Counterparty
from typing import List, Optional
from datetime import datetime


def get_counterparty(db: Session, counterparty_id: int) -> Optional[Counterparty]:
    """Получить контрагента по ID"""
    return db.query(Counterparty).filter(Counterparty.id == counterparty_id, Counterparty.is_active == True).first()


def get_counterparties(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[Counterparty]:
    """Получить список контрагентов с фильтрацией"""
    query = db.query(Counterparty)
    
    # Фильтр по активности
    if is_active is not None:
        query = query.filter(Counterparty.is_active == is_active)
    else:
        query = query.filter(Counterparty.is_active == True)
    
    # Фильтр по категории
    if category_id is not None:
        query = query.filter(Counterparty.category_id == category_id)
    
    # Поиск по названию, ИНН, контактному лицу
    if search:
        search_filter = or_(
            Counterparty.name.ilike(f"%{search}%"),
            Counterparty.inn.ilike(f"%{search}%"),
            Counterparty.contact_person.ilike(f"%{search}%"),
            Counterparty.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    return query.offset(skip).limit(limit).all()


def get_counterparty_by_inn(db: Session, inn: str) -> Optional[Counterparty]:
    """Получить контрагента по ИНН"""
    return db.query(Counterparty).filter(
        Counterparty.inn == inn, 
        Counterparty.is_active == True
    ).first()


def create_counterparty(db: Session, counterparty_data) -> Counterparty:
    """Создать нового контрагента"""
    db_counterparty = Counterparty(
        name=counterparty_data.name,
        category_id=counterparty_data.category_id,
        inn=counterparty_data.inn,
        kpp=counterparty_data.kpp,
        address=counterparty_data.address,
        phone=counterparty_data.phone,
        email=counterparty_data.email,
        contact_person=counterparty_data.contact_person,
        notes=counterparty_data.notes,
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=datetime(9999, 12, 31, 0, 0, 0)
    )
    db.add(db_counterparty)
    db.commit()
    db.refresh(db_counterparty)
    return db_counterparty


def update_counterparty(db: Session, counterparty_id: int, counterparty_data) -> Optional[Counterparty]:
    """Обновить контрагента"""
    counterparty = db.query(Counterparty).filter(
        Counterparty.id == counterparty_id, 
        Counterparty.is_active == True
    ).first()
    
    if not counterparty:
        return None
    
    # Обновляем только переданные поля
    if counterparty_data.name is not None:
        counterparty.name = counterparty_data.name
    if counterparty_data.category_id is not None:
        counterparty.category_id = counterparty_data.category_id
    if counterparty_data.inn is not None:
        counterparty.inn = counterparty_data.inn
    if counterparty_data.kpp is not None:
        counterparty.kpp = counterparty_data.kpp
    if counterparty_data.address is not None:
        counterparty.address = counterparty_data.address
    if counterparty_data.phone is not None:
        counterparty.phone = counterparty_data.phone
    if counterparty_data.email is not None:
        counterparty.email = counterparty_data.email
    if counterparty_data.contact_person is not None:
        counterparty.contact_person = counterparty_data.contact_person
    if counterparty_data.notes is not None:
        counterparty.notes = counterparty_data.notes
    if counterparty_data.is_active is not None:
        counterparty.is_active = counterparty_data.is_active
    
    db.commit()
    db.refresh(counterparty)
    return counterparty


def delete_counterparty(db: Session, counterparty_id: int) -> bool:
    """Мягкое удаление контрагента (soft delete)"""
    counterparty = db.query(Counterparty).filter(
        Counterparty.id == counterparty_id, 
        Counterparty.is_active == True
    ).first()
    
    if not counterparty:
        return False
    
    counterparty.is_active = False
    counterparty.end_date = datetime.utcnow()
    db.commit()
    return True 