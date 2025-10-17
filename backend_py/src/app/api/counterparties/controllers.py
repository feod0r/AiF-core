from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import CounterpartyIn, CounterpartyUpdate
from app.external.sqlalchemy.utils import counterparties as counterparty_crud
from typing import List


def get_counterparty(db: Session, counterparty_id: int):
    """Получить контрагента по ID"""
    counterparty = counterparty_crud.get_counterparty(db, counterparty_id)
    if not counterparty:
        raise HTTPException(status_code=404, detail="Контрагент не найден")
    return counterparty


def get_counterparties(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category_id: int = None,
    search: str = None,
    is_active: bool = None
):
    """Получить список контрагентов с фильтрацией"""
    return counterparty_crud.get_counterparties(
        db, 
        skip=skip, 
        limit=limit,
        category_id=category_id,
        search=search,
        is_active=is_active
    )


def get_counterparty_by_inn(db: Session, inn: str):
    """Получить контрагента по ИНН"""
    counterparty = counterparty_crud.get_counterparty_by_inn(db, inn)
    if not counterparty:
        raise HTTPException(status_code=404, detail=f"Контрагент с ИНН {inn} не найден")
    return counterparty


def create_counterparty(db: Session, counterparty_in: CounterpartyIn):
    """Создать нового контрагента"""
    # Проверяем уникальность ИНН, если он указан
    if counterparty_in.inn:
        existing = counterparty_crud.get_counterparty_by_inn(db, counterparty_in.inn)
        if existing:
            raise HTTPException(status_code=400, detail=f"Контрагент с ИНН {counterparty_in.inn} уже существует")
    
    try:
        return counterparty_crud.create_counterparty(db, counterparty_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании контрагента: {str(e)}")


def update_counterparty(db: Session, counterparty_id: int, counterparty_update: CounterpartyUpdate):
    """Обновить контрагента"""
    # Проверяем уникальность ИНН, если он изменяется
    if counterparty_update.inn:
        existing = counterparty_crud.get_counterparty_by_inn(db, counterparty_update.inn)
        if existing and existing.id != counterparty_id:
            raise HTTPException(status_code=400, detail=f"Контрагент с ИНН {counterparty_update.inn} уже существует")
    
    counterparty = counterparty_crud.update_counterparty(db, counterparty_id, counterparty_update)
    if not counterparty:
        raise HTTPException(status_code=404, detail="Контрагент не найден")
    return counterparty


def delete_counterparty(db: Session, counterparty_id: int):
    """Удалить контрагента (мягкое удаление)"""
    success = counterparty_crud.delete_counterparty(db, counterparty_id)
    if not success:
        raise HTTPException(status_code=404, detail="Контрагент не найден")
    return {"message": "Контрагент успешно удален"} 