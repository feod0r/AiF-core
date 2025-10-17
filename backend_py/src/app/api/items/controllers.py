from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import ItemIn, ItemUpdate
from app.external.sqlalchemy.utils import items as item_crud
from app.external.sqlalchemy.utils.item_categories import get_item_category
from typing import List, Dict
from datetime import datetime


def get_item(db: Session, item_id: int):
    """Получить товар по ID"""
    item = item_crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return item


def get_items(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category_id: int = None,
    is_active: bool = None,
    has_stock: bool = None,
    search: str = None
):
    """Получить список товаров с фильтрацией"""
    return item_crud.get_items(
        db=db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        is_active=is_active,
        has_stock=has_stock,
        search=search
    )


def get_item_by_sku(db: Session, sku: str):
    """Получить товар по артикулу"""
    item = item_crud.get_item_by_sku(db, sku)
    if not item:
        raise HTTPException(status_code=404, detail=f"Товар с артикулом {sku} не найден")
    return item


def get_item_by_barcode(db: Session, barcode: str):
    """Получить товар по штрихкоду"""
    item = item_crud.get_item_by_barcode(db, barcode)
    if not item:
        raise HTTPException(status_code=404, detail=f"Товар со штрихкодом {barcode} не найден")
    return item


def create_item(db: Session, item_in: ItemIn):
    """Создать новый товар"""
    # Валидация связей
    _validate_item_links(db, item_in)
    
    # Проверка уникальности артикула
    existing_sku = item_crud.get_item_by_sku(db, item_in.sku)
    if existing_sku:
        raise HTTPException(status_code=400, detail=f"Товар с артикулом {item_in.sku} уже существует")
    
    # Проверка уникальности штрихкода
    if item_in.barcode:
        existing_barcode = item_crud.get_item_by_barcode(db, item_in.barcode)
        if existing_barcode:
            raise HTTPException(status_code=400, detail=f"Товар со штрихкодом {item_in.barcode} уже существует")
    
    try:
        return item_crud.create_item(db, item_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании товара: {str(e)}")


def update_item(db: Session, item_id: int, item_update: ItemUpdate):
    """Обновить товар"""
    # Проверяем существование товара
    existing_item = item_crud.get_item(db, item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Валидация связей для обновляемых полей
    _validate_item_links(db, item_update, existing_item)
    
    # Проверка уникальности артикула
    if item_update.sku is not None:
        existing_sku = item_crud.get_item_by_sku(db, item_update.sku)
        if existing_sku and existing_sku.id != item_id:
            raise HTTPException(status_code=400, detail=f"Товар с артикулом {item_update.sku} уже существует")
    
    # Проверка уникальности штрихкода
    if item_update.barcode is not None:
        existing_barcode = item_crud.get_item_by_barcode(db, item_update.barcode)
        if existing_barcode and existing_barcode.id != item_id:
            raise HTTPException(status_code=400, detail=f"Товар со штрихкодом {item_update.barcode} уже существует")
    
    try:
        item = item_crud.update_item(db, item_id, item_update)
        if not item:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return item
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обновлении товара: {str(e)}")


def delete_item(db: Session, item_id: int):
    """Удалить товар"""
    try:
        success = item_crud.delete_item(db, item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return {"message": "Товар успешно удален"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при удалении товара: {str(e)}")


def get_items_by_category(db: Session, category_id: int):
    """Получить все товары определенной категории"""
    return item_crud.get_items_by_category(db, category_id)


def get_items_with_stock_info(db: Session, warehouse_id: int = None):
    """Получить товары с информацией об остатках"""
    return item_crud.get_items_with_stock_info(db, warehouse_id)


def get_items_summary(db: Session):
    """Получить сводку по товарам"""
    return item_crud.get_items_summary(db)


def get_low_stock_items(db: Session, warehouse_id: int = None):
    """Получить товары с низкими остатками"""
    return item_crud.get_low_stock_items(db, warehouse_id)


def get_item_detail(db: Session, item_id: int):
    """Получить детальную информацию о товаре"""
    item = item_crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Получаем информацию об остатках
    stock_info = item_crud.get_items_with_stock_info(db)
    item_stock_info = next((info for info in stock_info if info['id'] == item_id), None)
    
    # Получаем остатки на складах
    warehouse_stocks = []
    for stock in item.warehouse_stocks:
        warehouse_stocks.append({
            "warehouse_id": stock.warehouse_id,
            "warehouse_name": stock.warehouse.name if stock.warehouse else None,
            "quantity": float(stock.quantity),
            "reserved_quantity": float(stock.reserved_quantity),
            "available_quantity": float(stock.quantity - stock.reserved_quantity),
            "min_quantity": float(stock.min_quantity),
            "max_quantity": float(stock.max_quantity) if stock.max_quantity else None,
            "location": stock.location,
            "last_updated": stock.last_updated
        })
    
    # Получаем остатки в автоматах
    machine_stocks = []
    for stock in item.machine_stocks:
        machine_stocks.append({
            "machine_id": stock.machine_id,
            "machine_name": stock.machine.name if stock.machine else None,
            "quantity": float(stock.quantity),
            "capacity": float(stock.capacity) if stock.capacity else None,
            "min_quantity": float(stock.min_quantity),
            "last_updated": stock.last_updated
        })
    
    # Создаем детальный объект
    detail = {
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
        "start_date": item.start_date,
        "end_date": item.end_date,
        "total_warehouse_quantity": item_stock_info['total_warehouse_quantity'] if item_stock_info else 0.0,
        "total_machine_quantity": item_stock_info['total_machine_quantity'] if item_stock_info else 0.0,
        "total_reserved": item_stock_info['total_reserved'] if item_stock_info else 0.0,
        "available_quantity": item_stock_info['available_quantity'] if item_stock_info else 0.0,
        "warehouse_stocks": warehouse_stocks,
        "machine_stocks": machine_stocks
    }
    
    return detail


def _validate_item_links(db: Session, item_data, existing_item=None):
    """Валидация связей товара"""
    
    # Проверяем категорию
    if hasattr(item_data, 'category_id') and item_data.category_id is not None:
        try:
            get_item_category(db, item_data.category_id)
        except HTTPException:
            raise HTTPException(status_code=400, detail=f"Категория с ID {item_data.category_id} не найдена") 