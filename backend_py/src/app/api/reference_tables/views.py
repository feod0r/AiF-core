from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from .models import ReferenceItemIn, ReferenceItemOut, ReferenceItemUpdate, ReferenceItemCreateOrUpdate
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List

router = APIRouter()

@router.get("/reference-tables", response_model=List[str])
def get_available_reference_tables():
    """Получить список доступных справочных таблиц"""
    return controllers.get_available_tables()

@router.get("/reference-tables/{table_name}", response_model=List[ReferenceItemOut])
def read_reference_items(
    table_name: str = Path(..., description="Name of the reference table"),
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Search by name or description"),
    start_date_from: str = Query(None, description="Start date from in ISO format"),
    start_date_to: str = Query(None, description="Start date to in ISO format"),
    db: Session = Depends(get_db)
):
    """Получить все записи справочной таблицы с фильтрацией"""
    return controllers.get_reference_items(
        db, 
        table_name, 
        skip=skip, 
        limit=limit,
        search=search,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )

@router.get("/reference-tables/{table_name}/{item_id}", response_model=ReferenceItemOut)
def read_reference_item(
    table_name: str = Path(..., description="Name of the reference table"),
    item_id: int = Path(..., description="ID of the item"),
    db: Session = Depends(get_db)
):
    """Получить запись справочной таблицы по ID"""
    return controllers.get_reference_item(db, table_name, item_id)

@router.get("/reference-tables/{table_name}/name/{name}", response_model=ReferenceItemOut)
def read_reference_item_by_name(
    table_name: str = Path(..., description="Name of the reference table"),
    name: str = Path(..., description="Name of the item"),
    db: Session = Depends(get_db)
):
    """Получить запись справочной таблицы по имени"""
    return controllers.get_reference_item_by_name(db, table_name, name)

@router.post("/reference-tables/{table_name}", response_model=ReferenceItemOut)
def create_reference_item(
    table_name: str = Path(..., description="Name of the reference table"),
    item: ReferenceItemIn = None,
    db: Session = Depends(get_db)
):
    """Создать новую запись в справочной таблице"""
    return controllers.create_reference_item(db, table_name, item)

@router.put("/reference-tables/{table_name}/{item_id}", response_model=ReferenceItemOut)
def update_reference_item(
    table_name: str = Path(..., description="Name of the reference table"),
    item_id: int = Path(..., description="ID of the item"),
    item: ReferenceItemUpdate = None,
    db: Session = Depends(get_db)
):
    """Обновить запись в справочной таблице"""
    return controllers.update_reference_item(db, table_name, item_id, item)

@router.delete("/reference-tables/{table_name}/{item_id}")
def delete_reference_item(
    table_name: str = Path(..., description="Name of the reference table"),
    item_id: int = Path(..., description="ID of the item"),
    db: Session = Depends(get_db)
):
    """Удалить запись из справочной таблицы"""
    return controllers.delete_reference_item(db, table_name, item_id)

@router.post("/reference-tables/{table_name}/create-or-update", response_model=ReferenceItemOut)
def create_or_update_reference_item(
    table_name: str = Path(..., description="Name of the reference table"),
    item: ReferenceItemCreateOrUpdate = None,
    db: Session = Depends(get_db)
):
    """Создать или обновить запись в справочной таблице по имени"""
    return controllers.create_or_update_reference_item(db, table_name, item) 