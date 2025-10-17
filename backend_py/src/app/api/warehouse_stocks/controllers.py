from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import WarehouseStockIn, WarehouseStockUpdate, StockOperation, StockTransfer, StockReservation
from app.external.sqlalchemy.utils import warehouse_stocks as stock_crud
from app.external.sqlalchemy.utils.warehouses import get_warehouse
from app.external.sqlalchemy.utils.items import get_item
from typing import List, Dict, Tuple
from datetime import datetime
from decimal import Decimal


def get_warehouse_stock(db: Session, stock_id: int):
    """Получить складской остаток по ID"""
    stock = stock_crud.get_warehouse_stock(db, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Складской остаток не найден")
    return stock


def get_warehouse_stocks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    warehouse_id: int = None,
    item_id: int = None,
    low_stock: bool = None,
    search: str = None
):
    """Получить список складских остатков с фильтрацией"""
    return stock_crud.get_warehouse_stocks(
        db=db,
        skip=skip,
        limit=limit,
        warehouse_id=warehouse_id,
        item_id=item_id,
        low_stock=low_stock,
        search=search
    )


def get_warehouse_stock_by_item(db: Session, warehouse_id: int, item_id: int):
    """Получить складской остаток по товару и складу"""
    stock = stock_crud.get_warehouse_stock_by_item(db, warehouse_id, item_id)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Остаток товара {item_id} на складе {warehouse_id} не найден")
    return stock


def create_warehouse_stock(db: Session, stock_in: WarehouseStockIn):
    """Создать новый складской остаток"""
    # Валидация связей
    _validate_stock_links(db, stock_in)
    
    try:
        return stock_crud.create_warehouse_stock(db, stock_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании остатка: {str(e)}")


def update_warehouse_stock(db: Session, stock_id: int, stock_update: WarehouseStockUpdate):
    """Обновить складской остаток"""
    # Проверяем существование остатка
    existing_stock = stock_crud.get_warehouse_stock(db, stock_id)
    if not existing_stock:
        raise HTTPException(status_code=404, detail="Складской остаток не найден")
    
    # Валидация бизнес-логики
    _validate_stock_update(db, existing_stock, stock_update)
    
    try:
        stock = stock_crud.update_warehouse_stock(db, stock_id, stock_update)
        if not stock:
            raise HTTPException(status_code=404, detail="Складской остаток не найден")
        return stock
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обновлении остатка: {str(e)}")


def delete_warehouse_stock(db: Session, stock_id: int):
    """Удалить складской остаток"""
    try:
        success = stock_crud.delete_warehouse_stock(db, stock_id)
        if not success:
            raise HTTPException(status_code=404, detail="Складской остаток не найден")
        return {"message": "Складской остаток успешно удален"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при удалении остатка: {str(e)}")


def add_warehouse_stock(db: Session, warehouse_id: int, item_id: int, operation: StockOperation):
    """Добавить товар на склад (приход)"""
    # Валидация связей
    _validate_warehouse_item(db, warehouse_id, item_id)
    
    try:
        return stock_crud.add_warehouse_stock(db, warehouse_id, item_id, operation.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при добавлении товара: {str(e)}")


def remove_warehouse_stock(db: Session, warehouse_id: int, item_id: int, operation: StockOperation):
    """Убрать товар со склада (расход)"""
    # Валидация связей
    _validate_warehouse_item(db, warehouse_id, item_id)
    
    try:
        return stock_crud.remove_warehouse_stock(db, warehouse_id, item_id, operation.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при списании товара: {str(e)}")


def reserve_warehouse_stock(db: Session, warehouse_id: int, item_id: int, reservation: StockReservation):
    """Зарезервировать товар на складе"""
    # Валидация связей
    _validate_warehouse_item(db, warehouse_id, item_id)
    
    try:
        return stock_crud.reserve_warehouse_stock(db, warehouse_id, item_id, reservation.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при резервировании товара: {str(e)}")


def release_warehouse_stock(db: Session, warehouse_id: int, item_id: int, reservation: StockReservation):
    """Снять резервирование товара на складе"""
    # Валидация связей
    _validate_warehouse_item(db, warehouse_id, item_id)
    
    try:
        return stock_crud.release_warehouse_stock(db, warehouse_id, item_id, reservation.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при снятии резервирования: {str(e)}")


def transfer_warehouse_stock(db: Session, transfer: StockTransfer):
    """Переместить товар между складами"""
    # Валидация связей
    _validate_warehouse_item(db, transfer.from_warehouse_id, transfer.item_id)
    _validate_warehouse_item(db, transfer.to_warehouse_id, transfer.item_id)
    
    try:
        from_stock, to_stock = stock_crud.transfer_warehouse_stock(
            db, 
            transfer.from_warehouse_id, 
            transfer.to_warehouse_id, 
            transfer.item_id, 
            transfer.quantity
        )
        return {
            "from_stock": from_stock,
            "to_stock": to_stock,
            "message": f"Перемещено {transfer.quantity} единиц товара {transfer.item_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при перемещении товара: {str(e)}")


def get_warehouse_stocks_summary(db: Session, warehouse_id: int = None):
    """Получить сводку по складским остаткам"""
    return stock_crud.get_warehouse_stocks_summary(db, warehouse_id)


def get_low_stock_warehouses(db: Session):
    """Получить склады с товарами, у которых низкие остатки"""
    return stock_crud.get_low_stock_warehouses(db)


def get_warehouse_stocks_by_warehouse(db: Session, warehouse_id: int):
    """Получить все остатки на конкретном складе"""
    return stock_crud.get_warehouse_stocks(db, warehouse_id=warehouse_id)


def get_warehouse_stocks_by_item(db: Session, item_id: int):
    """Получить все остатки конкретного товара на всех складах"""
    return stock_crud.get_warehouse_stocks(db, item_id=item_id)


def get_stock_detail(db: Session, stock_id: int):
    """Получить детальную информацию о складском остатке"""
    stock = stock_crud.get_warehouse_stock(db, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Складской остаток не найден")
    
    # Вычисляем дополнительные поля
    available_quantity = stock.quantity - stock.reserved_quantity
    utilization_percent = None
    if stock.max_quantity and stock.max_quantity > 0:
        utilization_percent = float(stock.quantity / stock.max_quantity * 100)
    
    is_low_stock = stock.quantity <= stock.min_quantity
    is_overstock = stock.max_quantity is not None and stock.quantity > stock.max_quantity
    
    # Создаем детальный объект
    detail = {
        "id": stock.id,
        "warehouse": stock.warehouse,
        "item": stock.item,
        "quantity": stock.quantity,
        "reserved_quantity": stock.reserved_quantity,
        "min_quantity": stock.min_quantity,
        "max_quantity": stock.max_quantity,
        "location": stock.location,
        "last_updated": stock.last_updated,
        "available_quantity": available_quantity,
        "utilization_percent": utilization_percent,
        "is_low_stock": is_low_stock,
        "is_overstock": is_overstock
    }
    
    return detail


def _validate_stock_links(db: Session, stock_data):
    """Валидация связей складского остатка"""
    
    # Проверяем склад
    try:
        get_warehouse(db, stock_data.warehouse_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Склад с ID {stock_data.warehouse_id} не найден")
    
    # Проверяем товар
    try:
        get_item(db, stock_data.item_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Товар с ID {stock_data.item_id} не найден")


def _validate_warehouse_item(db: Session, warehouse_id: int, item_id: int):
    """Валидация склада и товара"""
    
    # Проверяем склад
    try:
        get_warehouse(db, warehouse_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Склад с ID {warehouse_id} не найден")
    
    # Проверяем товар
    try:
        get_item(db, item_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Товар с ID {item_id} не найден")


def _validate_stock_update(db: Session, existing_stock, stock_update: WarehouseStockUpdate):
    """Валидация обновления складского остатка"""
    
    # Проверяем, что зарезервированное количество не превышает общее количество
    if stock_update.quantity is not None and stock_update.reserved_quantity is not None:
        if stock_update.reserved_quantity > stock_update.quantity:
            raise HTTPException(
                status_code=400, 
                detail="Зарезервированное количество не может превышать общее количество"
            )
    
    # Проверяем, что зарезервированное количество не превышает новое общее количество
    elif stock_update.quantity is not None:
        if existing_stock.reserved_quantity > stock_update.quantity:
            raise HTTPException(
                status_code=400, 
                detail="Зарезервированное количество не может превышать общее количество"
            )
    
    # Проверяем, что новое зарезервированное количество не превышает текущее общее количество
    elif stock_update.reserved_quantity is not None:
        if stock_update.reserved_quantity > existing_stock.quantity:
            raise HTTPException(
                status_code=400, 
                detail="Зарезервированное количество не может превышать общее количество"
            )
    
    # Проверяем, что максимальное количество больше минимального
    if stock_update.max_quantity is not None and stock_update.min_quantity is not None:
        if stock_update.max_quantity <= stock_update.min_quantity:
            raise HTTPException(
                status_code=400, 
                detail="Максимальное количество должно быть больше минимального"
            )
    
    elif stock_update.max_quantity is not None:
        if stock_update.max_quantity <= existing_stock.min_quantity:
            raise HTTPException(
                status_code=400, 
                detail="Максимальное количество должно быть больше минимального"
            )
    
    elif stock_update.min_quantity is not None:
        if existing_stock.max_quantity and stock_update.min_quantity >= existing_stock.max_quantity:
            raise HTTPException(
                status_code=400, 
                detail="Минимальное количество должно быть меньше максимального"
            ) 