from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import MachineStockIn, MachineStockUpdate, MachineStockOperation, MachineStockTransfer, MachineLoadOperation, MachineUnloadOperation
from app.external.sqlalchemy.utils import machine_stocks as stock_crud
from app.external.sqlalchemy.utils.machines import get_machine
from app.external.sqlalchemy.utils.items import get_item
from app.external.sqlalchemy.utils.warehouses import get_warehouse
from typing import List, Dict, Tuple
from datetime import datetime
from decimal import Decimal


def get_machine_stock(db: Session, stock_id: int):
    """Получить остаток в автомате по ID"""
    stock = stock_crud.get_machine_stock(db, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Остаток в автомате не найден")
    return stock


def get_machine_stocks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    machine_id: int = None,
    item_id: int = None,
    category_id: int = None,
    low_stock: bool = None,
    search: str = None
):
    """Получить список остатков в автоматах с фильтрацией"""
    return stock_crud.get_machine_stocks(
        db=db,
        skip=skip,
        limit=limit,
        machine_id=machine_id,
        item_id=item_id,
        category_id=category_id,
        low_stock=low_stock,
        search=search
    )


def get_machine_stocks_count(
    db: Session,
    machine_id: int = None,
    item_id: int = None,
    category_id: int = None,
    low_stock: bool = None,
    search: str = None
):
    """Получить количество остатков в автоматах с фильтрацией"""
    return stock_crud.get_machine_stocks_count(
        db=db,
        machine_id=machine_id,
        item_id=item_id,
        category_id=category_id,
        low_stock=low_stock,
        search=search
    )


def get_machine_stock_by_item(db: Session, machine_id: int, item_id: int):
    """Получить остаток в автомате по товару и автомату"""
    stock = stock_crud.get_machine_stock_by_item(db, machine_id, item_id)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Остаток товара {item_id} в автомате {machine_id} не найден")
    return stock


def create_machine_stock(db: Session, stock_in: MachineStockIn):
    """Создать новый остаток в автомате"""
    # Валидация связей
    _validate_stock_links(db, stock_in)
    
    try:
        return stock_crud.create_machine_stock(db, stock_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании остатка: {str(e)}")


def update_machine_stock(db: Session, stock_id: int, stock_update: MachineStockUpdate):
    """Обновить остаток в автомате"""
    # Проверяем существование остатка
    existing_stock = stock_crud.get_machine_stock(db, stock_id)
    if not existing_stock:
        raise HTTPException(status_code=404, detail="Остаток в автомате не найден")
    
    # Валидация бизнес-логики
    _validate_stock_update(db, existing_stock, stock_update)
    
    try:
        stock = stock_crud.update_machine_stock(db, stock_id, stock_update)
        if not stock:
            raise HTTPException(status_code=404, detail="Остаток в автомате не найден")
        return stock
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обновлении остатка: {str(e)}")


def delete_machine_stock(db: Session, stock_id: int):
    """Удалить остаток в автомате"""
    try:
        success = stock_crud.delete_machine_stock(db, stock_id)
        if not success:
            raise HTTPException(status_code=404, detail="Остаток в автомате не найден")
        return {"message": "Остаток в автомате успешно удален"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при удалении остатка: {str(e)}")


def add_machine_stock(db: Session, machine_id: int, item_id: int, operation: MachineStockOperation):
    """Добавить товар в автомат"""
    # Валидация связей
    _validate_machine_item(db, machine_id, item_id)
    
    try:
        return stock_crud.add_machine_stock(db, machine_id, item_id, operation.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при добавлении товара: {str(e)}")


def remove_machine_stock(db: Session, machine_id: int, item_id: int, operation: MachineStockOperation):
    """Убрать товар из автомата"""
    # Валидация связей
    _validate_machine_item(db, machine_id, item_id)
    
    try:
        return stock_crud.remove_machine_stock(db, machine_id, item_id, operation.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при списании товара: {str(e)}")


def transfer_machine_stock(db: Session, transfer: MachineStockTransfer):
    """Переместить товар между автоматами"""
    # Валидация связей
    _validate_machine_item(db, transfer.from_machine_id, transfer.item_id)
    _validate_machine_item(db, transfer.to_machine_id, transfer.item_id)
    
    try:
        from_stock, to_stock = stock_crud.transfer_machine_stock(
            db, 
            transfer.from_machine_id, 
            transfer.to_machine_id, 
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


def load_machine_from_warehouse(db: Session, machine_id: int, item_id: int, operation: MachineLoadOperation):
    """Загрузить автомат товаром со склада"""
    # Валидация связей
    _validate_machine_item(db, machine_id, item_id)
    _validate_warehouse(db, operation.warehouse_id)
    
    try:
        warehouse_stock, machine_stock = stock_crud.load_machine_from_warehouse(
            db, 
            operation.warehouse_id, 
            machine_id, 
            item_id, 
            operation.quantity
        )
        return {
            "warehouse_stock": warehouse_stock,
            "machine_stock": machine_stock,
            "message": f"Загружено {operation.quantity} единиц товара {item_id} в автомат {machine_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при загрузке автомата: {str(e)}")


def unload_machine_to_warehouse(db: Session, machine_id: int, item_id: int, operation: MachineUnloadOperation):
    """Выгрузить товар из автомата на склад"""
    # Валидация связей
    _validate_machine_item(db, machine_id, item_id)
    _validate_warehouse(db, operation.warehouse_id)
    
    try:
        machine_stock, warehouse_stock = stock_crud.unload_machine_to_warehouse(
            db, 
            machine_id, 
            operation.warehouse_id, 
            item_id, 
            operation.quantity
        )
        return {
            "machine_stock": machine_stock,
            "warehouse_stock": warehouse_stock,
            "message": f"Выгружено {operation.quantity} единиц товара {item_id} из автомата {machine_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при выгрузке автомата: {str(e)}")


def get_machine_stocks_summary(db: Session, machine_id: int = None):
    """Получить сводку по остаткам в автоматах"""
    return stock_crud.get_machine_stocks_summary(db, machine_id)


def get_low_stock_machines(db: Session):
    """Получить автоматы с товарами, у которых низкие остатки"""
    return stock_crud.get_low_stock_machines(db)


def get_machine_stocks_by_machine(db: Session, machine_id: int):
    """Получить все остатки в конкретном автомате"""
    return stock_crud.get_machine_stocks_by_machine(db, machine_id)


def get_machine_stocks_by_item(db: Session, item_id: int):
    """Получить все остатки конкретного товара во всех автоматах"""
    return stock_crud.get_machine_stocks_by_item(db, item_id)


def get_machine_utilization(db: Session, machine_id: int = None):
    """Получить информацию о загрузке автоматов"""
    return stock_crud.get_machine_utilization(db, machine_id)


def get_machine_stocks_grouped_by_machines(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    machine_id: int = None,
    item_id: int = None,
    category_id: int = None,
    low_stock: bool = None,
    search: str = None
):
    """Получить остатки в автоматах, сгруппированные по автоматам"""
    # Получаем все остатки с фильтрацией
    stocks = stock_crud.get_machine_stocks(
        db=db,
        skip=0,  # Берем все для группировки
        limit=10000,  # Большой лимит для получения всех данных
        machine_id=machine_id,
        item_id=item_id,
        category_id=category_id,
        low_stock=low_stock,
        search=search
    )
    
    # Группируем по автоматам
    grouped = {}
    for stock in stocks:
        machine_id_key = stock.machine_id
        if machine_id_key not in grouped:
            grouped[machine_id_key] = {
                "machine": {
                    "id": stock.machine.id if stock.machine else machine_id_key,
                    "name": stock.machine.name if stock.machine else f"Автомат {machine_id_key}",
                    "terminal": {
                        "id": stock.machine.terminal.id if stock.machine and stock.machine.terminal else None,
                        "name": stock.machine.terminal.name if stock.machine and stock.machine.terminal else None,
                    } if stock.machine and stock.machine.terminal else None
                },
                "stocks": [],
                "total_items": 0,
                "low_stock_items": 0,
                "total_quantity": 0,
                "total_capacity": 0,
                "utilization_percent": 0
            }
        
        group = grouped[machine_id_key]
        group["stocks"].append({
            "id": stock.id,
            "machine_id": stock.machine_id,
            "item_id": stock.item_id,
            "quantity": float(stock.quantity),
            "capacity": float(stock.capacity) if stock.capacity else None,
            "min_quantity": float(stock.min_quantity),
            "last_updated": stock.last_updated.isoformat() if stock.last_updated else None,
            "machine": {
                "id": stock.machine.id if stock.machine else stock.machine_id,
                "name": stock.machine.name if stock.machine else f"Автомат {stock.machine_id}",
                "terminal": {
                    "id": stock.machine.terminal.id if stock.machine and stock.machine.terminal else None,
                    "name": stock.machine.terminal.name if stock.machine and stock.machine.terminal else None,
                } if stock.machine and stock.machine.terminal else None
            } if stock.machine else None,
            "item": {
                "id": stock.item.id if stock.item else stock.item_id,
                "name": stock.item.name if stock.item else f"Товар {stock.item_id}",
                "sku": stock.item.sku if stock.item else None,
                "unit": stock.item.unit if stock.item else "шт",
                "min_stock": float(stock.item.min_stock) if stock.item and stock.item.min_stock else 0,
                "max_stock": float(stock.item.max_stock) if stock.item and stock.item.max_stock else None,
                "category": {
                    "id": stock.item.category.id if stock.item and stock.item.category else None,
                    "name": stock.item.category.name if stock.item and stock.item.category else None,
                    "category_type": {
                        "id": stock.item.category.category_type.id if stock.item and stock.item.category and stock.item.category.category_type else None,
                        "name": stock.item.category.category_type.name if stock.item and stock.item.category and stock.item.category.category_type else None,
                    } if stock.item and stock.item.category and stock.item.category.category_type else None
                } if stock.item and stock.item.category else None
            } if stock.item else None
        })
        
        # Обновляем статистику группы
        group["total_items"] += 1
        group["total_quantity"] += float(stock.quantity)
        if stock.capacity:
            group["total_capacity"] += float(stock.capacity)
        # Используем максимальное значение между min_quantity автомата и min_stock товара
        effective_min_quantity = max(float(stock.min_quantity), float(stock.item.min_stock) if stock.item and stock.item.min_stock else 0)
        if stock.quantity <= effective_min_quantity:
            group["low_stock_items"] += 1
    
    # Вычисляем процент загрузки для каждой группы
    for group in grouped.values():
        if group["total_capacity"] > 0:
            group["utilization_percent"] = round((group["total_quantity"] / group["total_capacity"]) * 100, 2)
    
    # Преобразуем в список и сортируем по названию автомата
    result = list(grouped.values())
    result.sort(key=lambda x: x["machine"]["name"])
    
    # Применяем пагинацию к группам
    start_idx = skip
    end_idx = skip + limit
    paginated_result = result[start_idx:end_idx]
    
    return paginated_result


def get_stock_detail(db: Session, stock_id: int):
    """Получить детальную информацию об остатке в автомате"""
    stock = stock_crud.get_machine_stock(db, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Остаток в автомате не найден")
    
    # Вычисляем дополнительные поля
    utilization_percent = None
    if stock.capacity and stock.capacity > 0:
        utilization_percent = float(stock.quantity / stock.capacity * 100)
    
    is_low_stock = stock.quantity <= stock.min_quantity
    is_full = stock.capacity is not None and stock.quantity >= stock.capacity
    can_add_quantity = None
    if stock.capacity is not None:
        can_add_quantity = max(0, stock.capacity - stock.quantity)
    
    # Создаем детальный объект
    detail = {
        "id": stock.id,
        "machine": stock.machine,
        "item": stock.item,
        "quantity": stock.quantity,
        "capacity": stock.capacity,
        "min_quantity": stock.min_quantity,
        "last_updated": stock.last_updated,
        "available_quantity": stock.quantity,
        "utilization_percent": utilization_percent,
        "is_low_stock": is_low_stock,
        "is_full": is_full,
        "can_add_quantity": can_add_quantity
    }
    
    return detail


def _validate_stock_links(db: Session, stock_data):
    """Валидация связей остатка в автомате"""
    
    # Проверяем автомат
    try:
        get_machine(db, stock_data.machine_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Автомат с ID {stock_data.machine_id} не найден")
    
    # Проверяем товар
    try:
        get_item(db, stock_data.item_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Товар с ID {stock_data.item_id} не найден")


def _validate_machine_item(db: Session, machine_id: int, item_id: int):
    """Валидация автомата и товара"""
    
    # Проверяем автомат
    try:
        get_machine(db, machine_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Автомат с ID {machine_id} не найден")
    
    # Проверяем товар
    try:
        get_item(db, item_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Товар с ID {item_id} не найден")


def _validate_warehouse(db: Session, warehouse_id: int):
    """Валидация склада"""
    
    try:
        get_warehouse(db, warehouse_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail=f"Склад с ID {warehouse_id} не найден")


def _validate_stock_update(db: Session, existing_stock, stock_update: MachineStockUpdate):
    """Валидация обновления остатка в автомате"""
    
    # Проверяем, что новое количество не превышает вместимость
    if stock_update.quantity is not None and stock_update.capacity is not None:
        if stock_update.quantity > stock_update.capacity:
            raise HTTPException(
                status_code=400, 
                detail="Количество не может превышать вместимость"
            )
    
    # Проверяем, что новое количество не превышает текущую вместимость
    elif stock_update.quantity is not None:
        if existing_stock.capacity and stock_update.quantity > existing_stock.capacity:
            raise HTTPException(
                status_code=400, 
                detail="Количество не может превышать вместимость"
            )
    
    # Проверяем, что новая вместимость не меньше текущего количества
    elif stock_update.capacity is not None:
        if stock_update.capacity < existing_stock.quantity:
            raise HTTPException(
                status_code=400, 
                detail="Вместимость не может быть меньше текущего количества"
            )
    
    # Проверяем, что максимальное количество больше минимального
    if stock_update.capacity is not None and stock_update.min_quantity is not None:
        if stock_update.capacity <= stock_update.min_quantity:
            raise HTTPException(
                status_code=400, 
                detail="Вместимость должна быть больше минимального количества"
            )
    
    elif stock_update.capacity is not None:
        if stock_update.capacity <= existing_stock.min_quantity:
            raise HTTPException(
                status_code=400, 
                detail="Вместимость должна быть больше минимального количества"
            )
    
    elif stock_update.min_quantity is not None:
        if existing_stock.capacity and stock_update.min_quantity >= existing_stock.capacity:
            raise HTTPException(
                status_code=400, 
                detail="Минимальное количество должно быть меньше вместимости"
            ) 