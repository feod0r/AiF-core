from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from .models import CounterpartyIn, CounterpartyOut, CounterpartyUpdate
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List, Optional

router = APIRouter()

@router.get("/counterparties", response_model=List[CounterpartyOut])
def read_counterparties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[int] = Query(None, description="Фильтр по ID категории"),
    search: Optional[str] = Query(None, description="Поиск по названию, ИНН, контактному лицу"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    db: Session = Depends(get_db)
):
    """Получить список контрагентов с фильтрацией"""
    return controllers.get_counterparties(
        db, 
        skip=skip, 
        limit=limit,
        category_id=category_id,
        search=search,
        is_active=is_active
    )

@router.get("/counterparties/{counterparty_id}", response_model=CounterpartyOut)
def read_counterparty(
    counterparty_id: int = Path(..., description="ID контрагента"),
    db: Session = Depends(get_db)
):
    """Получить контрагента по ID"""
    return controllers.get_counterparty(db, counterparty_id)

@router.get("/counterparties/inn/{inn}", response_model=CounterpartyOut)
def read_counterparty_by_inn(
    inn: str = Path(..., description="ИНН контрагента"),
    db: Session = Depends(get_db)
):
    """Получить контрагента по ИНН"""
    return controllers.get_counterparty_by_inn(db, inn)

@router.post("/counterparties", response_model=CounterpartyOut)
def create_counterparty(
    counterparty: CounterpartyIn,
    db: Session = Depends(get_db)
):
    """Создать нового контрагента"""
    return controllers.create_counterparty(db, counterparty)

@router.put("/counterparties/{counterparty_id}", response_model=CounterpartyOut)
def update_counterparty(
    counterparty_id: int = Path(..., description="ID контрагента"),
    counterparty: CounterpartyUpdate = None,
    db: Session = Depends(get_db)
):
    """Обновить контрагента"""
    return controllers.update_counterparty(db, counterparty_id, counterparty)

@router.delete("/counterparties/{counterparty_id}")
def delete_counterparty(
    counterparty_id: int = Path(..., description="ID контрагента"),
    db: Session = Depends(get_db)
):
    """Удалить контрагента (мягкое удаление)"""
    return controllers.delete_counterparty(db, counterparty_id) 