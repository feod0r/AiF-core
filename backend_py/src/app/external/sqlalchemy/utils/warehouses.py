from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from ..models import Warehouse
from typing import List, Optional
from datetime import datetime


def get_warehouse(db: Session, warehouse_id: int) -> Optional[Warehouse]:
    """Получить склад по ID"""
    return (
        db.query(Warehouse)
        .filter(Warehouse.id == warehouse_id, Warehouse.is_active == True)
        .first()
    )


def get_warehouses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[Warehouse]:
    """Получить список складов с фильтрацией"""
    query = db.query(Warehouse)

    # Фильтр по активности
    if is_active is not None:
        query = query.filter(Warehouse.is_active == is_active)
    else:
        query = query.filter(Warehouse.is_active == True)

    # Фильтр по владельцу
    if owner_id is not None:
        query = query.filter(Warehouse.owner_id == owner_id)

    # Поиск по названию и адресу
    if search:
        search_filter = or_(
            Warehouse.name.ilike(f"%{search}%"), Warehouse.address.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    return query.offset(skip).limit(limit).all()


def get_warehouse_by_name(db: Session, name: str) -> Optional[Warehouse]:
    """Получить склад по названию"""
    return (
        db.query(Warehouse)
        .filter(Warehouse.name == name, Warehouse.is_active == True)
        .first()
    )


def get_warehouses_by_owner(db: Session, owner_id: int) -> List[Warehouse]:
    """Получить все склады владельца"""
    return (
        db.query(Warehouse)
        .filter(Warehouse.owner_id == owner_id, Warehouse.is_active == True)
        .all()
    )


def create_warehouse(db: Session, warehouse_data) -> Warehouse:
    """Создать новый склад"""
    db_warehouse = Warehouse(
        name=warehouse_data.name,
        address=warehouse_data.address,
        contact_person_id=warehouse_data.contact_person_id,
        owner_id=warehouse_data.owner_id,
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=datetime(9999, 12, 31, 0, 0, 0),
    )
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse


def update_warehouse(
    db: Session, warehouse_id: int, warehouse_data
) -> Optional[Warehouse]:
    """Обновить склад"""
    warehouse = (
        db.query(Warehouse)
        .filter(Warehouse.id == warehouse_id, Warehouse.is_active == True)
        .first()
    )
    if not warehouse:
        return None

    # Обновляем только переданные поля
    if warehouse_data.name is not None:
        warehouse.name = warehouse_data.name
    if warehouse_data.address is not None:
        warehouse.address = warehouse_data.address
    if warehouse_data.contact_person_id is not None:
        warehouse.contact_person_id = warehouse_data.contact_person_id
    if warehouse_data.owner_id is not None:
        warehouse.owner_id = warehouse_data.owner_id
    if warehouse_data.is_active is not None:
        warehouse.is_active = warehouse_data.is_active

    db.commit()
    db.refresh(warehouse)
    return warehouse


def delete_warehouse(db: Session, warehouse_id: int) -> bool:
    """Мягкое удаление склада (soft delete)"""
    warehouse = (
        db.query(Warehouse)
        .filter(Warehouse.id == warehouse_id, Warehouse.is_active == True)
        .first()
    )
    if not warehouse:
        return False

    warehouse.is_active = False
    warehouse.end_date = datetime.utcnow()
    db.commit()
    return True


def get_warehouse_summary(db: Session, owner_id: Optional[int] = None) -> dict:
    """Получить сводку по складам"""
    query = db.query(Warehouse).filter(Warehouse.is_active == True)

    if owner_id is not None:
        query = query.filter(Warehouse.owner_id == owner_id)

    warehouses = query.all()
    total_warehouses = len(warehouses)

    # Группировка по владельцам
    from sqlalchemy import func

    owner_counts = (
        db.query(Warehouse.owner_id, func.count(Warehouse.id).label("count"))
        .filter(Warehouse.is_active == True)
        .group_by(Warehouse.owner_id)
        .all()
    )

    return {
        "total_warehouses": total_warehouses,
        "owner_counts": {str(owner_id): count for owner_id, count in owner_counts},
    }


def get_warehouses_with_stocks(
    db: Session, owner_id: Optional[int] = None
) -> List[Warehouse]:
    """Получить склады с информацией о наличии товаров"""
    query = db.query(Warehouse).filter(Warehouse.is_active == True)

    if owner_id is not None:
        query = query.filter(Warehouse.owner_id == owner_id)

    warehouses = query.all()

    # Для каждого склада получаем количество позиций в наличии
    for warehouse in warehouses:
        # Здесь можно добавить логику подсчета товаров на складе
        # когда будет создана модель WarehouseStock
        warehouse.stock_count = 0  # Временно

    return warehouses
