from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import ReferenceItemIn, ReferenceItemUpdate, ReferenceItemCreateOrUpdate
from app.external.sqlalchemy.utils.reference_tables import reference_cruds
from typing import List

def get_reference_items(
    db: Session, 
    table_name: str, 
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    start_date_from: str = None,
    start_date_to: str = None
):
    """Получить все записи справочной таблицы с фильтрацией"""
    if table_name not in reference_cruds:
        raise HTTPException(status_code=404, detail=f"Reference table '{table_name}' not found")
    
    return reference_cruds[table_name].get_all(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )

def get_reference_item(db: Session, table_name: str, item_id: int):
    """Получить запись справочной таблицы по ID"""
    if table_name not in reference_cruds:
        raise HTTPException(status_code=404, detail=f"Reference table '{table_name}' not found")
    
    item = reference_cruds[table_name].get_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found in {table_name}")
    return item

def get_reference_item_by_name(db: Session, table_name: str, name: str):
    """Получить запись справочной таблицы по имени"""
    if table_name not in reference_cruds:
        raise HTTPException(status_code=404, detail=f"Reference table '{table_name}' not found")
    
    item = reference_cruds[table_name].get_by_name(db, name)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with name '{name}' not found in {table_name}")
    return item

def create_reference_item(db: Session, table_name: str, item_in: ReferenceItemIn):
    """Создать новую запись в справочной таблице"""
    if table_name not in reference_cruds:
        raise HTTPException(status_code=404, detail=f"Reference table '{table_name}' not found")
    
    try:
        return reference_cruds[table_name].create(
            db, 
            name=item_in.name, 
            description=item_in.description
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create item: {str(e)}")

def update_reference_item(db: Session, table_name: str, item_id: int, item_update: ReferenceItemUpdate):
    """Обновить запись в справочной таблице"""
    if table_name not in reference_cruds:
        raise HTTPException(status_code=404, detail=f"Reference table '{table_name}' not found")
    
    item = reference_cruds[table_name].update(
        db, 
        item_id=item_id,
        name=item_update.name, 
        description=item_update.description
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found in {table_name}")
    return item

def delete_reference_item(db: Session, table_name: str, item_id: int):
    """Удалить запись из справочной таблицы"""
    if table_name not in reference_cruds:
        raise HTTPException(status_code=404, detail=f"Reference table '{table_name}' not found")
    
    success = reference_cruds[table_name].delete(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found in {table_name}")
    return {"message": f"Item deleted successfully from {table_name}"}

def create_or_update_reference_item(db: Session, table_name: str, item_in: ReferenceItemCreateOrUpdate):
    """Создать или обновить запись в справочной таблице по имени"""
    if table_name not in reference_cruds:
        raise HTTPException(status_code=404, detail=f"Reference table '{table_name}' not found")
    
    try:
        return reference_cruds[table_name].create_or_update(
            db, 
            name=item_in.name, 
            description=item_in.description
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create or update item: {str(e)}")

def get_available_tables():
    """Получить список доступных справочных таблиц"""
    return list(reference_cruds.keys()) 