from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
import sqlalchemy as sa
from ..models import MachineStock, Item, Machine, WarehouseStock
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


def get_machine_stock(db: Session, stock_id: int) -> Optional[MachineStock]:
    """Получить остаток в автомате по ID"""
    return db.query(MachineStock).filter(MachineStock.id == stock_id).first()


def get_machine_stock_by_item(
    db: Session, machine_id: int, item_id: int
) -> Optional[MachineStock]:
    """Получить остаток в автомате по товару и автомату"""
    return (
        db.query(MachineStock)
        .filter(MachineStock.machine_id == machine_id, MachineStock.item_id == item_id)
        .first()
    )


def get_machine_stocks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    machine_id: Optional[int] = None,
    item_id: Optional[int] = None,
    category_id: Optional[int] = None,
    low_stock: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[MachineStock]:
    """Получить список остатков в автоматах с фильтрацией"""
    query = db.query(MachineStock)

    # Фильтр по автомату
    if machine_id is not None:
        query = query.filter(MachineStock.machine_id == machine_id)

    # Фильтр по товару
    if item_id is not None:
        query = query.filter(MachineStock.item_id == item_id)

    # Фильтр по низким остаткам
    if low_stock is not None:
        if low_stock:
            # Сравниваем с максимальным из min_quantity автомата и min_stock товара
            query = query.join(Item).filter(
                MachineStock.quantity <= sa.func.greatest(MachineStock.min_quantity, Item.min_stock)
            )
        else:
            # Сравниваем с максимальным из min_quantity автомата и min_stock товара
            query = query.join(Item).filter(
                MachineStock.quantity > sa.func.greatest(MachineStock.min_quantity, Item.min_stock)
            )

    # Фильтр по категории товара или поиск - нужен join с Item
    if category_id is not None or search:
        query = query.join(Item)
        
        if category_id is not None:
            query = query.filter(Item.category_id == category_id)
        
        if search:
            query = query.filter(
                or_(
                    Item.name.ilike(f"%{search}%"),
                    Item.sku.ilike(f"%{search}%"),
                    Item.barcode.ilike(f"%{search}%"),
                )
            )

    return query.offset(skip).limit(limit).all()


def get_machine_stocks_count(
    db: Session,
    machine_id: Optional[int] = None,
    item_id: Optional[int] = None,
    category_id: Optional[int] = None,
    low_stock: Optional[bool] = None,
    search: Optional[str] = None,
) -> int:
    """Получить количество остатков в автоматах с фильтрацией"""
    query = db.query(MachineStock)

    # Фильтр по автомату
    if machine_id is not None:
        query = query.filter(MachineStock.machine_id == machine_id)

    # Фильтр по товару
    if item_id is not None:
        query = query.filter(MachineStock.item_id == item_id)

    # Фильтр по низким остаткам
    if low_stock is not None:
        if low_stock:
            query = query.filter(MachineStock.quantity <= MachineStock.min_quantity)
        else:
            query = query.filter(MachineStock.quantity > MachineStock.min_quantity)

    # Фильтр по категории товара или поиск - нужен join с Item
    if category_id is not None or search:
        query = query.join(Item)
        
        if category_id is not None:
            query = query.filter(Item.category_id == category_id)
        
        if search:
            query = query.filter(
                or_(
                    Item.name.ilike(f"%{search}%"),
                    Item.sku.ilike(f"%{search}%"),
                    Item.barcode.ilike(f"%{search}%"),
                )
            )

    return query.count()


def create_machine_stock(db: Session, stock_data) -> MachineStock:
    """Создать новый остаток в автомате"""
    # Проверяем, существует ли уже остаток для данного товара в автомате
    existing_stock = get_machine_stock_by_item(
        db, stock_data.machine_id, stock_data.item_id
    )
    if existing_stock:
        raise ValueError(
            f"Остаток для товара {stock_data.item_id} в автомате {stock_data.machine_id} уже существует"
        )

    db_stock = MachineStock(
        machine_id=stock_data.machine_id,
        item_id=stock_data.item_id,
        quantity=stock_data.quantity
        if hasattr(stock_data, "quantity")
        else Decimal("0"),
        capacity=stock_data.capacity if hasattr(stock_data, "capacity") else None,
        min_quantity=stock_data.min_quantity
        if hasattr(stock_data, "min_quantity")
        else Decimal("0"),
        last_updated=datetime.utcnow(),
    )
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


def update_machine_stock(
    db: Session, stock_id: int, stock_data
) -> Optional[MachineStock]:
    """Обновить остаток в автомате"""
    stock = db.query(MachineStock).filter(MachineStock.id == stock_id).first()
    if not stock:
        return None

    # Обновляем только переданные поля
    if stock_data.quantity is not None:
        stock.quantity = stock_data.quantity
    if stock_data.capacity is not None:
        stock.capacity = stock_data.capacity
    if stock_data.min_quantity is not None:
        stock.min_quantity = stock_data.min_quantity

    stock.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(stock)
    return stock


def delete_machine_stock(db: Session, stock_id: int) -> bool:
    """Удалить остаток в автомате"""
    stock = db.query(MachineStock).filter(MachineStock.id == stock_id).first()
    if not stock:
        return False

    db.delete(stock)
    db.commit()
    return True


def add_machine_stock(
    db: Session, machine_id: int, item_id: int, quantity: Decimal
) -> MachineStock:
    """Добавить товар в автомат (загрузка)"""
    stock = get_machine_stock_by_item(db, machine_id, item_id)

    if stock:
        # Проверяем вместимость
        if stock.capacity and (stock.quantity + quantity) > stock.capacity:
            raise ValueError(
                f"Превышена вместимость автомата. Максимум: {stock.capacity}, будет: {stock.quantity + quantity}"
            )

        # Обновляем существующий остаток
        stock.quantity += quantity
        stock.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(stock)
    else:
        # Создаем новый остаток
        stock_data = type(
            "StockData",
            (),
            {"machine_id": machine_id, "item_id": item_id, "quantity": quantity},
        )()
        stock = create_machine_stock(db, stock_data)

    return stock


def remove_machine_stock(
    db: Session, machine_id: int, item_id: int, quantity: Decimal
) -> MachineStock:
    """Убрать товар из автомата (продажа/изъятие)"""
    stock = get_machine_stock_by_item(db, machine_id, item_id)

    if not stock:
        raise ValueError(f"Товар {item_id} не найден в автомате {machine_id}")

    if stock.quantity < quantity:
        raise ValueError(
            f"Недостаточно товара в автомате. Доступно: {stock.quantity}, требуется: {quantity}"
        )

    stock.quantity -= quantity
    stock.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(stock)

    return stock


def get_machine_stocks_summary(db: Session, machine_id: Optional[int] = None) -> dict:
    """Получить сводку по остаткам в автоматах"""
    query = db.query(MachineStock)

    if machine_id is not None:
        query = query.filter(MachineStock.machine_id == machine_id)

    stocks = query.all()

    total_quantity = sum(stock.quantity for stock in stocks)
    total_capacity = sum(stock.capacity for stock in stocks if stock.capacity)

    # Количество позиций с остатками
    items_with_stock = len([stock for stock in stocks if stock.quantity > 0])

    # Количество позиций с низкими остатками
    low_stock_items = len([
        stock for stock in stocks 
        if stock.quantity <= max(float(stock.min_quantity), float(stock.item.min_stock) if stock.item and stock.item.min_stock else 0)
    ])

    # Количество позиций с полной загрузкой
    full_stock_items = len(
        [
            stock
            for stock in stocks
            if stock.capacity and stock.quantity >= stock.capacity
        ]
    )

    return {
        "total_quantity": float(total_quantity),
        "total_capacity": float(total_capacity) if total_capacity else None,
        "utilization_percent": float(total_quantity / total_capacity * 100)
        if total_capacity
        else None,
        "items_with_stock": items_with_stock,
        "low_stock_items": low_stock_items,
        "full_stock_items": full_stock_items,
    }


def get_low_stock_machines(db: Session) -> List[dict]:
    """Получить автоматы с товарами, у которых низкие остатки"""
    # Получаем все автоматы с товарами, у которых остаток меньше или равен максимальному из min_quantity и min_stock
    stocks = (
        db.query(MachineStock)
        .join(Item)
        .filter(MachineStock.quantity <= sa.func.greatest(MachineStock.min_quantity, Item.min_stock))
        .all()
    )

    # Группируем по автоматам
    machine_low_stocks = {}
    for stock in stocks:
        machine_id = stock.machine_id
        if machine_id not in machine_low_stocks:
            machine_low_stocks[machine_id] = {
                "machine": stock.machine,
                "low_stock_items": [],
            }

        machine_low_stocks[machine_id]["low_stock_items"].append(
            {
                "item": stock.item,
                "current_quantity": float(stock.quantity),
                "min_quantity": float(stock.min_quantity),
                "capacity": float(stock.capacity) if stock.capacity else None,
            }
        )

    return list(machine_low_stocks.values())


def get_machine_stocks_by_machine(db: Session, machine_id: int) -> List[MachineStock]:
    """Получить все остатки в конкретном автомате"""
    return db.query(MachineStock).filter(MachineStock.machine_id == machine_id).all()


def get_machine_stocks_by_item(db: Session, item_id: int) -> List[MachineStock]:
    """Получить все остатки конкретного товара во всех автоматах"""
    return db.query(MachineStock).filter(MachineStock.item_id == item_id).all()


def transfer_machine_stock(
    db: Session,
    from_machine_id: int,
    to_machine_id: int,
    item_id: int,
    quantity: Decimal,
) -> tuple[MachineStock, MachineStock]:
    """Переместить товар между автоматами"""
    # Убираем с исходного автомата
    from_stock = remove_machine_stock(db, from_machine_id, item_id, quantity)

    # Добавляем в целевой автомат
    to_stock = add_machine_stock(db, to_machine_id, item_id, quantity)

    return from_stock, to_stock


def load_machine_from_warehouse(
    db: Session, warehouse_id: int, machine_id: int, item_id: int, quantity: Decimal
) -> tuple[WarehouseStock, MachineStock]:
    """Загрузить автомат товаром со склада"""
    # Убираем со склада
    from app.external.sqlalchemy.utils.warehouse_stocks import remove_warehouse_stock

    warehouse_stock = remove_warehouse_stock(db, warehouse_id, item_id, quantity)

    # Добавляем в автомат
    machine_stock = add_machine_stock(db, machine_id, item_id, quantity)

    return warehouse_stock, machine_stock


def unload_machine_to_warehouse(
    db: Session, machine_id: int, warehouse_id: int, item_id: int, quantity: Decimal
) -> tuple[MachineStock, WarehouseStock]:
    """Выгрузить товар из автомата на склад"""
    # Убираем из автомата
    machine_stock = remove_machine_stock(db, machine_id, item_id, quantity)

    # Добавляем на склад
    from app.external.sqlalchemy.utils.warehouse_stocks import add_warehouse_stock

    warehouse_stock = add_warehouse_stock(db, warehouse_id, item_id, quantity)

    return machine_stock, warehouse_stock


def get_machine_utilization(db: Session, machine_id: int) -> dict:
    """Получить информацию о загрузке автомата"""
    stocks = get_machine_stocks_by_machine(db, machine_id)

    total_quantity = sum(stock.quantity for stock in stocks)
    total_capacity = sum(stock.capacity for stock in stocks if stock.capacity)

    # Количество позиций
    total_items = len(stocks)
    items_with_stock = len([stock for stock in stocks if stock.quantity > 0])

    # Позиции с низкими остатками
    low_stock_items = len(
        [stock for stock in stocks if stock.quantity <= stock.min_quantity]
    )

    return {
        "machine_id": machine_id,
        "total_quantity": float(total_quantity),
        "total_capacity": float(total_capacity) if total_capacity else None,
        "utilization_percent": float(total_quantity / total_capacity * 100)
        if total_capacity
        else None,
        "total_items": total_items,
        "items_with_stock": items_with_stock,
        "low_stock_items": low_stock_items,
        "empty_slots": total_items - items_with_stock,
    }
