from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from ..models import Item, WarehouseStock, MachineStock
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


def get_item(db: Session, item_id: int) -> Optional[Item]:
    """Получить товар по ID"""
    return db.query(Item).filter(Item.id == item_id, Item.is_active == True).first()


def get_items(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    has_stock: Optional[bool] = None,
) -> List[Item]:
    """Получить список товаров с фильтрацией"""
    query = db.query(Item)

    # Фильтр по активности
    if is_active is not None:
        query = query.filter(Item.is_active == is_active)
    else:
        query = query.filter(Item.is_active == True)

    # Фильтр по категории
    if category_id is not None:
        query = query.filter(Item.category_id == category_id)

    # Поиск по названию, артикулу, описанию, штрихкоду
    if search:
        search_filter = or_(
            Item.name.ilike(f"%{search}%"),
            Item.sku.ilike(f"%{search}%"),
            Item.description.ilike(f"%{search}%"),
            Item.barcode.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    # Фильтр по наличию остатков
    if has_stock is not None:
        if has_stock:
            # Товары с остатками на складах или в автоматах
            query = query.filter(
                or_(
                    Item.warehouse_stocks.any(WarehouseStock.quantity > 0),
                    Item.machine_stocks.any(MachineStock.quantity > 0),
                )
            )
        else:
            # Товары без остатков
            query = query.filter(
                and_(
                    ~Item.warehouse_stocks.any(WarehouseStock.quantity > 0),
                    ~Item.machine_stocks.any(MachineStock.quantity > 0),
                )
            )

    return query.offset(skip).limit(limit).all()


def get_item_by_sku(db: Session, sku: str) -> Optional[Item]:
    """Получить товар по артикулу"""
    return db.query(Item).filter(Item.sku == sku, Item.is_active == True).first()


def get_item_by_barcode(db: Session, barcode: str) -> Optional[Item]:
    """Получить товар по штрихкоду"""
    return (
        db.query(Item).filter(Item.barcode == barcode, Item.is_active == True).first()
    )


def create_item(db: Session, item_data) -> Item:
    """Создать новый товар"""
    db_item = Item(
        name=item_data.name,
        sku=item_data.sku,
        category_id=item_data.category_id,
        description=item_data.description,
        unit=item_data.unit if hasattr(item_data, "unit") else "шт",
        weight=item_data.weight if hasattr(item_data, "weight") else None,
        dimensions=item_data.dimensions if hasattr(item_data, "dimensions") else None,
        barcode=item_data.barcode if hasattr(item_data, "barcode") else None,
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=datetime(9999, 12, 31, 0, 0, 0),
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(db: Session, item_id: int, item_data) -> Optional[Item]:
    """Обновить товар"""
    item = db.query(Item).filter(Item.id == item_id, Item.is_active == True).first()
    if not item:
        return None

    # Обновляем только переданные поля
    if item_data.name is not None:
        item.name = item_data.name
    if item_data.sku is not None:
        item.sku = item_data.sku
    if item_data.category_id is not None:
        item.category_id = item_data.category_id
    if item_data.description is not None:
        item.description = item_data.description
    if item_data.unit is not None:
        item.unit = item_data.unit
    if item_data.weight is not None:
        item.weight = item_data.weight
    if item_data.dimensions is not None:
        item.dimensions = item_data.dimensions
    if item_data.barcode is not None:
        item.barcode = item_data.barcode
    if item_data.min_stock is not None:
        item.min_stock = item_data.min_stock
    if item_data.is_active is not None:
        item.is_active = item_data.is_active

    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int) -> bool:
    """Мягкое удаление товара (soft delete)"""
    item = db.query(Item).filter(Item.id == item_id, Item.is_active == True).first()
    if not item:
        return False

    item.is_active = False
    item.end_date = datetime.utcnow()
    db.commit()
    return True


def get_items_by_category(db: Session, category_id: int) -> List[Item]:
    """Получить все товары определенной категории"""
    return (
        db.query(Item)
        .filter(Item.category_id == category_id, Item.is_active == True)
        .all()
    )


def get_items_with_stock_info(
    db: Session, warehouse_id: Optional[int] = None
) -> List[dict]:
    """Получить товары с информацией об остатках"""
    query = db.query(Item).filter(Item.is_active == True)

    items = query.all()
    result = []

    for item in items:
        # Подсчитываем общие остатки
        total_warehouse_quantity = sum(
            stock.quantity for stock in item.warehouse_stocks
        )
        total_machine_quantity = sum(stock.quantity for stock in item.machine_stocks)
        total_reserved = sum(stock.reserved_quantity for stock in item.warehouse_stocks)

        item_data = {
            "id": item.id,
            "name": item.name,
            "sku": item.sku,
            "category": item.category,
            "description": item.description,
            "unit": item.unit,
            "weight": item.weight,
            "dimensions": item.dimensions,
            "barcode": item.barcode,
            "is_active": item.is_active,
            "total_warehouse_quantity": float(total_warehouse_quantity),
            "total_machine_quantity": float(total_machine_quantity),
            "total_reserved": float(total_reserved),
            "available_quantity": float(total_warehouse_quantity - total_reserved),
        }

        # Если указан конкретный склад, добавляем информацию по нему
        if warehouse_id:
            warehouse_stock = next(
                (
                    stock
                    for stock in item.warehouse_stocks
                    if stock.warehouse_id == warehouse_id
                ),
                None,
            )
            if warehouse_stock:
                item_data["warehouse_quantity"] = float(warehouse_stock.quantity)
                item_data["warehouse_reserved"] = float(
                    warehouse_stock.reserved_quantity
                )
                item_data["warehouse_available"] = float(
                    warehouse_stock.quantity - warehouse_stock.reserved_quantity
                )
                item_data["warehouse_location"] = warehouse_stock.location

        result.append(item_data)

    return result


def get_items_summary(db: Session) -> dict:
    """Получить сводку по товарам"""
    total_items = db.query(Item).filter(Item.is_active == True).count()

    # Товары с остатками
    items_with_stock = (
        db.query(Item)
        .filter(
            Item.is_active == True,
            or_(
                Item.warehouse_stocks.any(WarehouseStock.quantity > 0),
                Item.machine_stocks.any(MachineStock.quantity > 0),
            ),
        )
        .count()
    )

    # Товары без остатков
    items_without_stock = total_items - items_with_stock

    # Общие остатки
    total_warehouse_quantity = db.query(
        func.sum(WarehouseStock.quantity)
    ).scalar() or Decimal("0")
    total_machine_quantity = db.query(
        func.sum(MachineStock.quantity)
    ).scalar() or Decimal("0")
    total_reserved = db.query(
        func.sum(WarehouseStock.reserved_quantity)
    ).scalar() or Decimal("0")

    return {
        "total_items": total_items,
        "items_with_stock": items_with_stock,
        "items_without_stock": items_without_stock,
        "total_warehouse_quantity": float(total_warehouse_quantity),
        "total_machine_quantity": float(total_machine_quantity),
        "total_reserved": float(total_reserved),
        "total_available": float(total_warehouse_quantity - total_reserved),
    }


def get_low_stock_items(db: Session, warehouse_id: Optional[int] = None) -> List[dict]:
    """Получить товары с низкими остатками"""
    query = db.query(Item).filter(Item.is_active == True)

    if warehouse_id:
        # Товары с низкими остатками на конкретном складе
        query = query.join(WarehouseStock).filter(
            WarehouseStock.warehouse_id == warehouse_id,
            # Сравниваем с максимальным из min_quantity склада и min_stock товара
            WarehouseStock.quantity
            <= sa.func.greatest(WarehouseStock.min_quantity, Item.min_stock),
        )
    else:
        # Товары с низкими остатками на любом складе
        query = query.join(WarehouseStock).filter(
            # Сравниваем с максимальным из min_quantity склада и min_stock товара
            WarehouseStock.quantity
            <= sa.func.greatest(WarehouseStock.min_quantity, Item.min_stock)
        )

    items = query.all()
    result = []

    for item in items:
        if warehouse_id:
            stock = next(
                stock
                for stock in item.warehouse_stocks
                if stock.warehouse_id == warehouse_id
            )
            # Используем максимальное значение между min_quantity склада и min_stock товара
            effective_min_quantity = max(
                float(stock.min_quantity), float(item.min_stock)
            )
            item_data = {
                "id": item.id,
                "name": item.name,
                "sku": item.sku,
                "category": item.category,
                "current_quantity": float(stock.quantity),
                "min_quantity": effective_min_quantity,
                "warehouse": stock.warehouse,
            }
        else:
            # Находим склад с минимальным остатком
            min_stock = min(item.warehouse_stocks, key=lambda s: s.quantity)
            # Используем максимальное значение между min_quantity склада и min_stock товара
            effective_min_quantity = max(
                float(min_stock.min_quantity), float(item.min_stock)
            )
            item_data = {
                "id": item.id,
                "name": item.name,
                "sku": item.sku,
                "category": item.category,
                "current_quantity": float(min_stock.quantity),
                "min_quantity": effective_min_quantity,
                "warehouse": min_stock.warehouse,
            }

        result.append(item_data)

    return result
