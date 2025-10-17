from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ..models import (
    InventoryMovement,
    InventoryMovementItem,
    Item,
    Machine,
    Warehouse,
    Account,
    Transaction,
    TransactionCategory,
    TransactionType,
)
from .accounts import update_account_balance as _update_account_balance
from .reference_tables import inventory_count_status_crud
from .machine_stocks import get_machine_stock_by_item
from .warehouse_stocks import get_warehouse_stock_by_item


def get_inventory_movement(
    db: Session, movement_id: int
) -> Optional[InventoryMovement]:
    """Получить движение товаров по ID"""
    return (
        db.query(InventoryMovement).filter(InventoryMovement.id == movement_id).first()
    )


def get_inventory_movements(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    movement_type: Optional[str] = None,
    status_id: Optional[int] = None,
    counterparty_id: Optional[int] = None,
    created_by: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    # Новые параметры для фильтрации по местам
    from_warehouse_id: Optional[int] = None,
    to_warehouse_id: Optional[int] = None,
    from_machine_id: Optional[int] = None,
    to_machine_id: Optional[int] = None,
) -> List[InventoryMovement]:
    """Получить список движений товаров с фильтрацией"""
    query = db.query(InventoryMovement)

    # Фильтр по типу движения
    if movement_type is not None:
        query = query.filter(InventoryMovement.movement_type == movement_type)

    # Фильтр по статусу
    if status_id is not None:
        query = query.filter(InventoryMovement.status_id == status_id)

    # Фильтры по местам отправления и назначения
    if from_warehouse_id is not None:
        query = query.filter(InventoryMovement.from_warehouse_id == from_warehouse_id)
    
    if to_warehouse_id is not None:
        query = query.filter(InventoryMovement.to_warehouse_id == to_warehouse_id)
    
    if from_machine_id is not None:
        query = query.filter(InventoryMovement.from_machine_id == from_machine_id)
    
    if to_machine_id is not None:
        query = query.filter(InventoryMovement.to_machine_id == to_machine_id)

    # Фильтр по контрагенту
    if counterparty_id is not None:
        query = query.filter(InventoryMovement.counterparty_id == counterparty_id)

    # Фильтр по создателю
    if created_by is not None:
        query = query.filter(InventoryMovement.created_by == created_by)

    # Фильтр по дате
    if date_from is not None:
        query = query.filter(InventoryMovement.document_date >= date_from)
    if date_to is not None:
        query = query.filter(InventoryMovement.document_date <= date_to)

    # Поиск по номеру документа, описанию
    if search:
        search_filter = or_(
            InventoryMovement.description.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    return (
        query.order_by(InventoryMovement.document_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_inventory_movements_count(
    db: Session,
    movement_type: Optional[str] = None,
    status_id: Optional[int] = None,
    counterparty_id: Optional[int] = None,
    created_by: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    # Новые параметры для фильтрации по местам
    from_warehouse_id: Optional[int] = None,
    to_warehouse_id: Optional[int] = None,
    from_machine_id: Optional[int] = None,
    to_machine_id: Optional[int] = None,
) -> int:
    """Получить общее количество движений товаров с фильтрацией"""
    query = db.query(InventoryMovement)

    # Фильтр по типу движения
    if movement_type is not None:
        query = query.filter(InventoryMovement.movement_type == movement_type)

    # Фильтр по статусу
    if status_id is not None:
        query = query.filter(InventoryMovement.status_id == status_id)

    # Фильтры по местам отправления и назначения
    if from_warehouse_id is not None:
        query = query.filter(InventoryMovement.from_warehouse_id == from_warehouse_id)
    
    if to_warehouse_id is not None:
        query = query.filter(InventoryMovement.to_warehouse_id == to_warehouse_id)
    
    if from_machine_id is not None:
        query = query.filter(InventoryMovement.from_machine_id == from_machine_id)
    
    if to_machine_id is not None:
        query = query.filter(InventoryMovement.to_machine_id == to_machine_id)

    # Фильтр по контрагенту
    if counterparty_id is not None:
        query = query.filter(InventoryMovement.counterparty_id == counterparty_id)

    # Фильтр по создателю
    if created_by is not None:
        query = query.filter(InventoryMovement.created_by == created_by)

    # Фильтр по дате
    if date_from is not None:
        query = query.filter(InventoryMovement.document_date >= date_from)
    if date_to is not None:
        query = query.filter(InventoryMovement.document_date <= date_to)

    # Поиск по номеру документа, описанию
    if search:
        search_filter = or_(
            InventoryMovement.description.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    return query.count()


def create_inventory_movement(
    db: Session, movement_data, items_data: List[Dict]
) -> InventoryMovement:
    """Создать новое движение товаров"""
    # Проверяем уникальность номера документа

    # Создаем движение
    db_movement = InventoryMovement(
        movement_type=movement_data.movement_type,
        document_date=movement_data.document_date
        if hasattr(movement_data, "document_date")
        else datetime.utcnow(),
        status_id=movement_data.status_id,
        description=movement_data.description,
        from_warehouse_id=movement_data.from_warehouse_id
        if hasattr(movement_data, "from_warehouse_id")
        else None,
        to_warehouse_id=movement_data.to_warehouse_id
        if hasattr(movement_data, "to_warehouse_id")
        else None,
        from_machine_id=movement_data.from_machine_id
        if hasattr(movement_data, "from_machine_id")
        else None,
        to_machine_id=movement_data.to_machine_id
        if hasattr(movement_data, "to_machine_id")
        else None,
        counterparty_id=movement_data.counterparty_id
        if hasattr(movement_data, "counterparty_id")
        else None,
        created_by=movement_data.created_by
        if hasattr(movement_data, "created_by")
        else None,
        total_amount=Decimal("0.00"),
        currency=movement_data.currency
        if hasattr(movement_data, "currency")
        else "RUB",
    )

    db.add(db_movement)
    db.flush()  # Получаем ID движения

    # Добавляем позиции
    total_amount = Decimal("0.00")
    for item_data in items_data:
        amount = item_data["quantity"] * item_data["price"]
        total_amount += amount

        movement_item = InventoryMovementItem(
            movement_id=db_movement.id,
            item_id=item_data["item_id"],
            quantity=item_data["quantity"],
            price=item_data["price"],
            amount=amount,
            description=item_data.get("description", ""),
        )
        db.add(movement_item)

    # Обновляем общую сумму
    db_movement.total_amount = total_amount

    db.commit()
    db.refresh(db_movement)
    return db_movement


def update_inventory_movement(
    db: Session,
    movement_id: int,
    movement_data,
    items_data: Optional[List[Dict]] = None,
) -> Optional[InventoryMovement]:
    """Обновить движение товаров"""
    movement = (
        db.query(InventoryMovement).filter(InventoryMovement.id == movement_id).first()
    )
    if not movement:
        return None

    # Проверяем, можно ли редактировать документ
    if movement.approved_at is not None:
        raise ValueError("Нельзя редактировать утвержденный документ")

    # Обновляем основные поля
    if movement_data.movement_type is not None:
        movement.movement_type = movement_data.movement_type
    if movement_data.document_date is not None:
        movement.document_date = movement_data.document_date
    if movement_data.status_id is not None:
        movement.status_id = movement_data.status_id
    if movement_data.description is not None:
        movement.description = movement_data.description
    if hasattr(movement_data, "from_warehouse_id"):
        movement.from_warehouse_id = movement_data.from_warehouse_id
    if hasattr(movement_data, "to_warehouse_id"):
        movement.to_warehouse_id = movement_data.to_warehouse_id
    if hasattr(movement_data, "from_machine_id"):
        movement.from_machine_id = movement_data.from_machine_id
    if hasattr(movement_data, "to_machine_id"):
        movement.to_machine_id = movement_data.to_machine_id
    if hasattr(movement_data, "counterparty_id"):
        movement.counterparty_id = movement_data.counterparty_id
    if hasattr(movement_data, "currency"):
        movement.currency = movement_data.currency

    # Обновляем позиции, если переданы
    if items_data is not None:
        # Удаляем старые позиции
        db.query(InventoryMovementItem).filter(
            InventoryMovementItem.movement_id == movement_id
        ).delete()

        # Добавляем новые позиции
        total_amount = Decimal("0.00")
        for item_data in items_data:
            amount = item_data["quantity"] * item_data["price"]
            total_amount += amount

            movement_item = InventoryMovementItem(
                movement_id=movement_id,
                item_id=item_data["item_id"],
                quantity=item_data["quantity"],
                price=item_data["price"],
                amount=amount,
                description=item_data.get("description", ""),
            )
            db.add(movement_item)

        movement.total_amount = total_amount

    db.commit()
    db.refresh(movement)
    return movement


def delete_inventory_movement(db: Session, movement_id: int) -> bool:
    """Удалить движение товаров"""
    movement = (
        db.query(InventoryMovement).filter(InventoryMovement.id == movement_id).first()
    )
    if not movement:
        return False

    # Проверяем, можно ли удалить документ
    if movement.approved_at is not None:
        raise ValueError("Нельзя удалить утвержденный документ")

    # Удаляем позиции
    db.query(InventoryMovementItem).filter(
        InventoryMovementItem.movement_id == movement_id
    ).delete()

    # Удаляем движение
    db.delete(movement)
    db.commit()
    return True


def approve_inventory_movement(
    db: Session, movement_id: int, approved_by: int
) -> InventoryMovement:
    """Утвердить движение товаров"""
    movement = (
        db.query(InventoryMovement).filter(InventoryMovement.id == movement_id).first()
    )
    if not movement:
        raise ValueError("Движение товаров не найдено")

    if movement.approved_at is not None:
        raise ValueError("Документ уже утвержден")

    # Обновляем статус на "approved", если доступен
    try:
        approved_status = inventory_count_status_crud.get_by_name(db, "approved")
        if approved_status is not None:
            movement.status_id = approved_status.id
    except Exception:
        pass

    movement.approved_by = approved_by
    movement.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(movement)
    return movement


def execute_inventory_movement(
    db: Session, movement_id: int, executed_by: int
) -> InventoryMovement:
    """Выполнить движение товаров (провести по остаткам)"""
    movement = (
        db.query(InventoryMovement).filter(InventoryMovement.id == movement_id).first()
    )
    if not movement:
        raise ValueError("Движение товаров не найдено")

    if movement.executed_at is not None:
        raise ValueError("Документ уже выполнен")

    if movement.approved_at is None:
        raise ValueError("Документ должен быть утвержден перед выполнением")

    # Выполняем операции по остаткам в зависимости от типа движения
    _execute_movement_operations(db, movement)

    # Обновляем статус на "executed", если доступен
    try:
        executed_status = inventory_count_status_crud.get_by_name(db, "executed")
        if executed_status is not None:
            movement.status_id = executed_status.id
    except Exception:
        pass

    movement.executed_by = executed_by
    movement.executed_at = datetime.utcnow()

    # Если это закупка, создаем банковскую транзакцию
    try:
        should_create_purchase = False
        
        if movement.movement_type == "receipt":
            # Для прихода всегда создаем транзакцию (это закупка)
            should_create_purchase = True
        elif movement.movement_type == "load_machine":
            # Для загрузки автомата создаем транзакцию только если нет склада отправления
            # (т.е. товар не перемещается со склада, а покупается)
            should_create_purchase = not movement.from_warehouse_id
            
        if should_create_purchase:
            _create_bank_transaction_for_purchase(db, movement)
    except Exception:
        # Не блокируем выполнение документа, если не удалось создать транзакцию
        pass

    db.commit()
    db.refresh(movement)
    return movement


def _execute_movement_operations(db: Session, movement: InventoryMovement):
    """Выполнить операции по остаткам для движения товаров"""
    from .machine_stocks import (
        add_machine_stock,
        load_machine_from_warehouse,
        remove_machine_stock,
        transfer_machine_stock,
        unload_machine_to_warehouse,
    )
    from .warehouse_stocks import (
        add_warehouse_stock,
        remove_warehouse_stock,
        transfer_warehouse_stock,
    )

    for item in movement.items:
        quantity = item.quantity

        if movement.movement_type == "receipt":
            # Приход: добавляем в место назначения
            if movement.to_warehouse_id:
                add_warehouse_stock(db, movement.to_warehouse_id, item.item_id, quantity)
            elif movement.to_machine_id:
                add_machine_stock(db, movement.to_machine_id, item.item_id, quantity)

        elif movement.movement_type == "issue":
            # Расход: списываем с места отправления
            if movement.from_warehouse_id:
                remove_warehouse_stock(
                    db, movement.from_warehouse_id, item.item_id, quantity
                )
            elif movement.from_machine_id:
                remove_machine_stock(db, movement.from_machine_id, item.item_id, quantity)

        elif movement.movement_type == "sale":
            # Продажа: списываем с места отправления
            if movement.from_warehouse_id:
                remove_warehouse_stock(
                    db, movement.from_warehouse_id, item.item_id, quantity
                )
            elif movement.from_machine_id:
                remove_machine_stock(db, movement.from_machine_id, item.item_id, quantity)

        elif movement.movement_type == "transfer":
            # Перемещение
            if movement.from_warehouse_id and movement.to_warehouse_id:
                # Склад -> Склад
                transfer_warehouse_stock(
                    db,
                    movement.from_warehouse_id,
                    movement.to_warehouse_id,
                    item.item_id,
                    quantity,
                )
            elif movement.from_machine_id and movement.to_machine_id:
                # Автомат -> Автомат
                transfer_machine_stock(
                    db,
                    movement.from_machine_id,
                    movement.to_machine_id,
                    item.item_id,
                    quantity,
                )
            elif movement.from_warehouse_id and movement.to_machine_id:
                # Склад -> Автомат (кросс-перемещение)
                load_machine_from_warehouse(
                    db,
                    movement.from_warehouse_id,
                    movement.to_machine_id,
                    item.item_id,
                    quantity,
                )
            elif movement.from_machine_id and movement.to_warehouse_id:
                # Автомат -> Склад (кросс-перемещение)
                unload_machine_to_warehouse(
                    db,
                    movement.from_machine_id,
                    movement.to_warehouse_id,
                    item.item_id,
                    quantity,
                )

        elif movement.movement_type == "load_machine":
            # Загрузка автомата
            if movement.from_warehouse_id and movement.to_machine_id:
                # Загрузка со склада (перемещение)
                load_machine_from_warehouse(
                    db,
                    movement.from_warehouse_id,
                    movement.to_machine_id,
                    item.item_id,
                    quantity,
                )
            elif movement.to_machine_id:
                # Загрузка без склада отправления (закупка)
                add_machine_stock(db, movement.to_machine_id, item.item_id, quantity)

        elif movement.movement_type == "unload_machine":
            # Выгрузка автомата
            if movement.from_machine_id and movement.to_warehouse_id:
                # Выгрузка на склад
                unload_machine_to_warehouse(
                    db,
                    movement.from_machine_id,
                    movement.to_warehouse_id,
                    item.item_id,
                    quantity,
                )
            elif movement.from_machine_id:
                # Выгрузка без склада назначения (продажа)
                remove_machine_stock(db, movement.from_machine_id, item.item_id, quantity)

        elif movement.movement_type == "adjustment":
            # Корректировка остатков (устанавливает точное количество)
            if movement.from_warehouse_id or movement.to_warehouse_id:
                warehouse_id = movement.from_warehouse_id or movement.to_warehouse_id
                stock = get_warehouse_stock_by_item(db, warehouse_id, item.item_id)
                if stock:
                    stock.quantity = quantity
                    stock.last_updated = datetime.now()
            elif movement.from_machine_id or movement.to_machine_id:
                machine_id = movement.from_machine_id or movement.to_machine_id
                stock = get_machine_stock_by_item(db, machine_id, item.item_id)
                if stock:
                    stock.quantity = quantity
                    stock.last_updated = datetime.now()


def _create_bank_transaction_for_purchase(db: Session, movement: InventoryMovement) -> None:
    """Создает банковскую операцию расхода на первого попавшегося счет владельца
    склада или автомата назначения. Счет может уходить в минус.
    """
    # Определяем владельца назначения
    owner_id = None
    # Приход/загрузка: используем to_warehouse_id/to_machine_id как место назначения
    dest_warehouse_id = movement.to_warehouse_id
    dest_machine_id = movement.to_machine_id

    if dest_warehouse_id:
        warehouse = db.query(Warehouse).filter(Warehouse.id == dest_warehouse_id).first()
        owner_id = warehouse.owner_id if warehouse else None
    elif dest_machine_id:
        machine = db.query(Machine).filter(Machine.id == dest_machine_id).first()
        # Через терминал получаем владельца
        if machine and machine.terminal_id:
            from ..models import Terminal  # локальный импорт, чтобы избежать циклов
            terminal = db.query(Terminal).filter(Terminal.id == machine.terminal_id).first()
            owner_id = terminal.owner_id if terminal else None

    if not owner_id:
        return

    # Ищем первый счет владельца (любой активный)
    account = (
        db.query(Account)
        .filter(Account.owner_id == owner_id)
        .order_by(Account.id.asc())
        .first()
    )
    if not account:
        return

    # Ищем тип транзакции 'expense'
    expense_type = db.query(TransactionType).filter(TransactionType.name == "expense").first()
    if not expense_type:
        return

    # Ищем первую категорию расходов, если нет — создадим простую
    category = (
        db.query(TransactionCategory)
        .filter(TransactionCategory.transaction_type_id == expense_type.id)
        .order_by(TransactionCategory.id.asc())
        .first()
    )
    if not category:
        # Создаем базовую категорию расходов
        category = TransactionCategory(
            name="Purchases",
            transaction_type_id=expense_type.id,
            description="Авто: закупка по движению товаров",
            is_active=True,
            start_date=datetime.utcnow(),
            end_date=datetime(9999, 12, 31, 0, 0, 0),
        )
        db.add(category)
        db.flush()

    # Создаем транзакцию расхода на сумму документа
    tx = Transaction(
        date=movement.document_date or datetime.utcnow(),
        account_id=account.id,
        category_id=category.id,
        counterparty_id=movement.counterparty_id,
        amount=-movement.total_amount,  # расходы записываем со знаком минус
        transaction_type_id=expense_type.id,
        description=movement.description or "Закупка по движению товаров",
        machine_id=dest_machine_id if dest_machine_id else None,
        rent_location_id=None,
        reference_number=f"IM-{movement.id}",
        is_confirmed=True,
        created_by=movement.executed_by or movement.created_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(tx)
    # Обновляем баланс счета (овердрафт допускается, баланс может уйти в минус)
    _update_account_balance(db, account.id)

def get_inventory_movements_summary(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> dict:
    """Получить сводку по движениям товаров"""
    query = db.query(InventoryMovement)

    if date_from:
        query = query.filter(InventoryMovement.document_date >= date_from)
    if date_to:
        query = query.filter(InventoryMovement.document_date <= date_to)

    movements = query.all()

    total_movements = len(movements)
    total_amount = sum(movement.total_amount for movement in movements)

    # Группировка по типам
    type_counts = {}
    type_amounts = {}
    for movement in movements:
        movement_type = movement.movement_type
        type_counts[movement_type] = type_counts.get(movement_type, 0) + 1
        type_amounts[movement_type] = (
            type_amounts.get(movement_type, Decimal("0")) + movement.total_amount
        )

    # Группировка по статусам
    status_counts = {}
    for movement in movements:
        status = movement.status.name if movement.status else "Unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "total_movements": total_movements,
        "total_amount": float(total_amount),
        "type_counts": type_counts,
        "type_amounts": {k: float(v) for k, v in type_amounts.items()},
        "status_counts": status_counts,
    }


def get_movement_items(db: Session, movement_id: int) -> List[InventoryMovementItem]:
    """Получить позиции движения товаров"""
    return (
        db.query(InventoryMovementItem)
        .filter(InventoryMovementItem.movement_id == movement_id)
        .all()
    )


def get_movements_by_item(
    db: Session,
    item_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[InventoryMovement]:
    """Получить движения товаров по конкретному товару"""
    query = (
        db.query(InventoryMovement)
        .join(InventoryMovementItem)
        .filter(InventoryMovementItem.item_id == item_id)
    )

    if date_from:
        query = query.filter(InventoryMovement.document_date >= date_from)
    if date_to:
        query = query.filter(InventoryMovement.document_date <= date_to)

    return query.order_by(InventoryMovement.document_date.desc()).all()


def get_movements_by_warehouse(
    db: Session,
    warehouse_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[InventoryMovement]:
    """Получить движения товаров по складу"""
    query = db.query(InventoryMovement).filter(
        or_(
            InventoryMovement.from_warehouse_id == warehouse_id,
            InventoryMovement.to_warehouse_id == warehouse_id,
        )
    )

    if date_from:
        query = query.filter(InventoryMovement.document_date >= date_from)
    if date_to:
        query = query.filter(InventoryMovement.document_date <= date_to)

    return query.order_by(InventoryMovement.document_date.desc()).all()


def get_movements_by_machine(
    db: Session,
    machine_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[InventoryMovement]:
    """Получить движения товаров по автомату"""
    query = db.query(InventoryMovement).filter(
        or_(
            InventoryMovement.from_machine_id == machine_id,
            InventoryMovement.to_machine_id == machine_id,
        )
    )

    if date_from:
        query = query.filter(InventoryMovement.document_date >= date_from)
    if date_to:
        query = query.filter(InventoryMovement.document_date <= date_to)

    return query.order_by(InventoryMovement.document_date.desc()).all()
