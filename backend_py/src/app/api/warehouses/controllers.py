from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.external.sqlalchemy.utils import warehouses as warehouse_crud
from app.external.sqlalchemy.utils.owners import get_owner

from .models import WarehouseIn, WarehouseUpdate


def get_warehouse(db: Session, warehouse_id: int):
    """Получить склад по ID"""
    warehouse = warehouse_crud.get_warehouse(db, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")
    return warehouse


def get_warehouses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner_id: int = None,
    is_active: bool = None,
    search: str = None,
):
    """Получить список складов с фильтрацией"""
    return warehouse_crud.get_warehouses(
        db,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        is_active=is_active,
        search=search,
    )


def get_warehouse_by_name(db: Session, name: str):
    """Получить склад по названию"""
    warehouse = warehouse_crud.get_warehouse_by_name(db, name)
    if not warehouse:
        raise HTTPException(status_code=404, detail=f"Склад '{name}' не найден")
    return warehouse


def get_warehouses_by_owner(db: Session, owner_id: int):
    """Получить все склады владельца"""
    return warehouse_crud.get_warehouses_by_owner(db, owner_id)


def create_warehouse(db: Session, warehouse_in: WarehouseIn):
    """Создать новый склад"""
    # Валидация связей
    _validate_warehouse_links(db, warehouse_in)

    # Проверяем уникальность названия в рамках владельца
    existing = warehouse_crud.get_warehouse_by_name(db, warehouse_in.name)
    if existing and existing.owner_id == warehouse_in.owner_id:
        raise HTTPException(
            status_code=400,
            detail=f"Склад с названием '{warehouse_in.name}' уже существует у данного владельца",
        )

    try:
        return warehouse_crud.create_warehouse(db, warehouse_in)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка при создании склада: {str(e)}"
        )


def update_warehouse(db: Session, warehouse_id: int, warehouse_update: WarehouseUpdate):
    """Обновить склад"""
    # Проверяем существование склада
    existing_warehouse = warehouse_crud.get_warehouse(db, warehouse_id)
    if not existing_warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")

    # Валидация связей для обновляемых полей
    _validate_warehouse_links(db, warehouse_update, existing_warehouse)

    warehouse = warehouse_crud.update_warehouse(db, warehouse_id, warehouse_update)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")
    return warehouse


def delete_warehouse(db: Session, warehouse_id: int):
    """Удалить склад (мягкое удаление)"""
    success = warehouse_crud.delete_warehouse(db, warehouse_id)
    if not success:
        raise HTTPException(status_code=404, detail="Склад не найден")
    return {"message": "Склад успешно удален"}


def get_warehouse_summary(db: Session, owner_id: int = None):
    """Получить сводку по складам"""
    return warehouse_crud.get_warehouse_summary(db, owner_id)


def get_warehouse_detail(db: Session, warehouse_id: int):
    """Получить детальную информацию о складе"""
    warehouse = warehouse_crud.get_warehouse(db, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")

    # Получаем дополнительную информацию
    # Здесь можно добавить логику подсчета товаров на складе
    # когда будет создана модель WarehouseStock

    # Создаем детальный объект
    detail = {
        "id": warehouse.id,
        "name": warehouse.name,
        "address": warehouse.address,
        "contact_person_id": warehouse.contact_person_id,
        "contact_person": warehouse.contact_person,
        "owner_id": warehouse.owner_id,
        "owner": warehouse.owner,
        "is_active": warehouse.is_active,
        "start_date": warehouse.start_date,
        "end_date": warehouse.end_date,
        "stock_count": 0,  # Временно, будет обновлено позже
    }

    return detail


def get_warehouses_with_stocks(db: Session, owner_id: int = None):
    """Получить склады с информацией о наличии товаров"""
    warehouses = warehouse_crud.get_warehouses_with_stocks(db, owner_id)

    # Преобразуем в список словарей с дополнительной информацией
    result = []
    for warehouse in warehouses:
        warehouse_data = {
            "id": warehouse.id,
            "name": warehouse.name,
            "address": warehouse.address,
            "contact_person_id": warehouse.contact_person_id,
            "contact_person": warehouse.contact_person,
            "owner_id": warehouse.owner_id,
            "owner": warehouse.owner,
            "is_active": warehouse.is_active,
            "stock_count": getattr(warehouse, "stock_count", 0),
            "total_items": 0,  # Будет обновлено позже
        }
        result.append(warehouse_data)

    return result


def _validate_warehouse_links(db: Session, warehouse_data, existing_warehouse=None):
    """Валидация связей склада"""

    # Проверяем владельца
    if hasattr(warehouse_data, "owner_id") and warehouse_data.owner_id is not None:
        try:
            get_owner(db, warehouse_data.owner_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Владелец с ID {warehouse_data.owner_id} не найден",
            )
