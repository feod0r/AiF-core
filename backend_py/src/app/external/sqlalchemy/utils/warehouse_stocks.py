from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
import sqlalchemy as sa
from ..models import WarehouseStock, Item, Warehouse
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


def get_warehouse_stock(db: Session, stock_id: int) -> Optional[WarehouseStock]:
    """Получить складской остаток по ID"""
    return db.query(WarehouseStock).filter(WarehouseStock.id == stock_id).first()


def get_warehouse_stock_by_item(db: Session, warehouse_id: int, item_id: int) -> Optional[WarehouseStock]:
    """Получить складской остаток по товару и складу"""
    return db.query(WarehouseStock).filter(
        WarehouseStock.warehouse_id == warehouse_id,
        WarehouseStock.item_id == item_id
    ).first()


def get_warehouse_stocks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    warehouse_id: Optional[int] = None,
    item_id: Optional[int] = None,
    low_stock: Optional[bool] = None,
    search: Optional[str] = None
) -> List[WarehouseStock]:
    """Получить список складских остатков с фильтрацией"""
    query = db.query(WarehouseStock)
    
    # Фильтр по складу
    if warehouse_id is not None:
        query = query.filter(WarehouseStock.warehouse_id == warehouse_id)
    
    # Фильтр по товару
    if item_id is not None:
        query = query.filter(WarehouseStock.item_id == item_id)
    
    # Фильтр по низким остаткам
    if low_stock is not None:
        if low_stock:
            # Сравниваем с максимальным из min_quantity склада и min_stock товара
            query = query.join(Item).filter(
                WarehouseStock.quantity <= sa.func.greatest(WarehouseStock.min_quantity, Item.min_stock)
            )
        else:
            # Сравниваем с максимальным из min_quantity склада и min_stock товара
            query = query.join(Item).filter(
                WarehouseStock.quantity > sa.func.greatest(WarehouseStock.min_quantity, Item.min_stock)
            )
    
    # Поиск по названию товара, артикулу, штрихкоду
    if search:
        query = query.join(Item).filter(
            or_(
                Item.name.ilike(f"%{search}%"),
                Item.sku.ilike(f"%{search}%"),
                Item.barcode.ilike(f"%{search}%")
            )
        )
    
    return query.offset(skip).limit(limit).all()


def create_warehouse_stock(db: Session, stock_data) -> WarehouseStock:
    """Создать новый складской остаток"""
    # Проверяем, существует ли уже остаток для данного товара на складе
    existing_stock = get_warehouse_stock_by_item(db, stock_data.warehouse_id, stock_data.item_id)
    if existing_stock:
        raise ValueError(f"Остаток для товара {stock_data.item_id} на складе {stock_data.warehouse_id} уже существует")
    
    db_stock = WarehouseStock(
        warehouse_id=stock_data.warehouse_id,
        item_id=stock_data.item_id,
        quantity=stock_data.quantity if hasattr(stock_data, 'quantity') else Decimal('0'),
        reserved_quantity=stock_data.reserved_quantity if hasattr(stock_data, 'reserved_quantity') else Decimal('0'),
        min_quantity=stock_data.min_quantity if hasattr(stock_data, 'min_quantity') else Decimal('0'),
        max_quantity=stock_data.max_quantity if hasattr(stock_data, 'max_quantity') else None,
        location=stock_data.location if hasattr(stock_data, 'location') else None,
        last_updated=datetime.utcnow()
    )
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


def update_warehouse_stock(db: Session, stock_id: int, stock_data) -> Optional[WarehouseStock]:
    """Обновить складской остаток"""
    stock = db.query(WarehouseStock).filter(WarehouseStock.id == stock_id).first()
    if not stock:
        return None
    
    # Обновляем только переданные поля
    if stock_data.quantity is not None:
        stock.quantity = stock_data.quantity
    if stock_data.reserved_quantity is not None:
        stock.reserved_quantity = stock_data.reserved_quantity
    if stock_data.min_quantity is not None:
        stock.min_quantity = stock_data.min_quantity
    if stock_data.max_quantity is not None:
        stock.max_quantity = stock_data.max_quantity
    if stock_data.location is not None:
        stock.location = stock_data.location
    
    stock.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(stock)
    return stock


def delete_warehouse_stock(db: Session, stock_id: int) -> bool:
    """Удалить складской остаток"""
    stock = db.query(WarehouseStock).filter(WarehouseStock.id == stock_id).first()
    if not stock:
        return False
    
    db.delete(stock)
    db.commit()
    return True


def add_warehouse_stock(db: Session, warehouse_id: int, item_id: int, quantity: Decimal) -> WarehouseStock:
    """Добавить товар на склад (приход)"""
    stock = get_warehouse_stock_by_item(db, warehouse_id, item_id)
    
    if stock:
        # Обновляем существующий остаток
        stock.quantity += quantity
        stock.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(stock)
    else:
        # Создаем новый остаток
        stock_data = type('StockData', (), {
            'warehouse_id': warehouse_id,
            'item_id': item_id,
            'quantity': quantity
        })()
        stock = create_warehouse_stock(db, stock_data)
    
    return stock


def remove_warehouse_stock(db: Session, warehouse_id: int, item_id: int, quantity: Decimal) -> WarehouseStock:
    """Убрать товар со склада (расход)"""
    stock = get_warehouse_stock_by_item(db, warehouse_id, item_id)
    
    if not stock:
        raise ValueError(f"Товар {item_id} не найден на складе {warehouse_id}")
    
    available_quantity = stock.quantity - stock.reserved_quantity
    
    if available_quantity < quantity:
        raise ValueError(f"Недостаточно товара на складе. Доступно: {available_quantity}, требуется: {quantity}")
    
    stock.quantity -= quantity
    stock.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(stock)
    
    return stock


def reserve_warehouse_stock(db: Session, warehouse_id: int, item_id: int, quantity: Decimal) -> WarehouseStock:
    """Зарезервировать товар на складе"""
    stock = get_warehouse_stock_by_item(db, warehouse_id, item_id)
    
    if not stock:
        raise ValueError(f"Товар {item_id} не найден на складе {warehouse_id}")
    
    available_quantity = stock.quantity - stock.reserved_quantity
    
    if available_quantity < quantity:
        raise ValueError(f"Недостаточно товара для резервирования. Доступно: {available_quantity}, требуется: {quantity}")
    
    stock.reserved_quantity += quantity
    stock.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(stock)
    
    return stock


def release_warehouse_stock(db: Session, warehouse_id: int, item_id: int, quantity: Decimal) -> WarehouseStock:
    """Снять резервирование товара на складе"""
    stock = get_warehouse_stock_by_item(db, warehouse_id, item_id)
    
    if not stock:
        raise ValueError(f"Товар {item_id} не найден на складе {warehouse_id}")
    
    if stock.reserved_quantity < quantity:
        raise ValueError(f"Недостаточно зарезервированного товара. Зарезервировано: {stock.reserved_quantity}, требуется снять: {quantity}")
    
    stock.reserved_quantity -= quantity
    stock.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(stock)
    
    return stock


def get_warehouse_stocks_summary(db: Session, warehouse_id: Optional[int] = None) -> dict:
    """Получить сводку по складским остаткам"""
    query = db.query(WarehouseStock)
    
    if warehouse_id is not None:
        query = query.filter(WarehouseStock.warehouse_id == warehouse_id)
    
    stocks = query.all()
    
    total_quantity = sum(stock.quantity for stock in stocks)
    total_reserved = sum(stock.reserved_quantity for stock in stocks)
    total_available = total_quantity - total_reserved
    
    # Количество позиций с остатками
    items_with_stock = len([stock for stock in stocks if stock.quantity > 0])
    
    # Количество позиций с низкими остатками
    low_stock_items = len([
        stock for stock in stocks 
        if stock.quantity <= max(float(stock.min_quantity), float(stock.item.min_stock) if stock.item and stock.item.min_stock else 0)
    ])
    
    return {
        "total_quantity": float(total_quantity),
        "total_reserved": float(total_reserved),
        "total_available": float(total_available),
        "items_with_stock": items_with_stock,
        "low_stock_items": low_stock_items
    }


def get_low_stock_warehouses(db: Session) -> List[dict]:
    """Получить склады с товарами, у которых низкие остатки"""
    # Получаем все склады с товарами, у которых остаток меньше или равен минимальному
    stocks = db.query(WarehouseStock).filter(
        WarehouseStock.quantity <= WarehouseStock.min_quantity
    ).all()
    
    # Группируем по складам
    warehouse_low_stocks = {}
    for stock in stocks:
        warehouse_id = stock.warehouse_id
        if warehouse_id not in warehouse_low_stocks:
            warehouse_low_stocks[warehouse_id] = {
                "warehouse": stock.warehouse,
                "low_stock_items": []
            }
        
        warehouse_low_stocks[warehouse_id]["low_stock_items"].append({
            "item": stock.item,
            "current_quantity": float(stock.quantity),
            "min_quantity": float(stock.min_quantity),
            "location": stock.location
        })
    
    return list(warehouse_low_stocks.values())


def transfer_warehouse_stock(
    db: Session, 
    from_warehouse_id: int, 
    to_warehouse_id: int, 
    item_id: int, 
    quantity: Decimal
) -> tuple[WarehouseStock, WarehouseStock]:
    """Переместить товар между складами"""
    # Убираем с исходного склада
    from_stock = remove_warehouse_stock(db, from_warehouse_id, item_id, quantity)
    
    # Добавляем на целевой склад
    to_stock = add_warehouse_stock(db, to_warehouse_id, item_id, quantity)
    
    return from_stock, to_stock 