from datetime import datetime
from typing import Dict, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.external.sqlalchemy.utils import inventory_movements as movement_crud
from app.external.sqlalchemy.utils.counterparties import get_counterparty
from app.external.sqlalchemy.utils.items import get_item
from app.external.sqlalchemy.utils.machine_stocks import get_machine_stock_by_item
from app.external.sqlalchemy.utils.machines import get_machine
from app.external.sqlalchemy.utils.reference_tables import inventory_count_status_crud
from app.external.sqlalchemy.utils.users import get_user_by_id
from app.external.sqlalchemy.utils.warehouse_stocks import get_warehouse_stock_by_item
from app.external.sqlalchemy.utils.warehouses import get_warehouse

from .models import (
    InventoryMovementIn,
    InventoryMovementUpdate,
    MovementApproval,
    MovementExecution,
    BulkMovementApproval,
    BulkMovementExecution,
    BulkOperationResult,
)


def get_inventory_movement(db: Session, movement_id: int):
    """Получить движение товаров по ID"""
    movement = movement_crud.get_inventory_movement(db, movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Движение товаров не найдено")
    return movement


def get_inventory_movements(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    movement_type: str = None,
    status_id: int = None,
    counterparty_id: int = None,
    created_by: int = None,
    date_from: datetime = None,
    date_to: datetime = None,
    search: str = None,
    # Дополнительные фильтры по местам
    from_warehouse_id: int = None,
    to_warehouse_id: int = None,
    from_machine_id: int = None,
    to_machine_id: int = None,
):
    """Получить список движений товаров с фильтрацией"""
    return movement_crud.get_inventory_movements(
        db,
        skip=skip,
        limit=limit,
        movement_type=movement_type,
        status_id=status_id,
        counterparty_id=counterparty_id,
        created_by=created_by,
        date_from=date_from,
        date_to=date_to,
        search=search,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        from_machine_id=from_machine_id,
        to_machine_id=to_machine_id,
    )


def get_inventory_movements_count(
    db: Session,
    movement_type: str = None,
    status_id: int = None,
    counterparty_id: int = None,
    created_by: int = None,
    date_from: datetime = None,
    date_to: datetime = None,
    search: str = None,
    # Дополнительные фильтры по местам
    from_warehouse_id: int = None,
    to_warehouse_id: int = None,
    from_machine_id: int = None,
    to_machine_id: int = None,
):
    """Получить общее количество движений товаров с фильтрацией"""
    return movement_crud.get_inventory_movements_count(
        db,
        movement_type=movement_type,
        status_id=status_id,
        counterparty_id=counterparty_id,
        created_by=created_by,
        date_from=date_from,
        date_to=date_to,
        search=search,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        from_machine_id=from_machine_id,
        to_machine_id=to_machine_id,
    )


def create_inventory_movement(db: Session, movement_in: InventoryMovementIn):
    """Создать новое движение товаров"""
    # Валидация связей
    _validate_movement_links(db, movement_in)

    # Валидация бизнес-логики
    _validate_movement_business_logic(db, movement_in)

    # Преобразуем позиции в формат для CRUD
    items_data = []
    for item in movement_in.items:
        items_data.append(
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
                "price": item.price,
                "description": item.description,
            }
        )

    try:
        return movement_crud.create_inventory_movement(db, movement_in, items_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка при создании движения: {str(e)}"
        )


def update_inventory_movement(
    db: Session, movement_id: int, movement_update: InventoryMovementUpdate
):
    """Обновить движение товаров"""
    # Проверяем существование движения
    existing_movement = movement_crud.get_inventory_movement(db, movement_id)
    if not existing_movement:
        raise HTTPException(status_code=404, detail="Движение товаров не найдено")

    # Валидация связей для обновляемых полей
    _validate_movement_links(db, movement_update, existing_movement)

    # Валидация бизнес-логики
    _validate_movement_business_logic(db, movement_update, existing_movement)

    # Преобразуем позиции, если переданы
    items_data = None
    if movement_update.items is not None:
        items_data = []
        for item in movement_update.items:
            items_data.append(
                {
                    "item_id": item.item_id,
                    "quantity": item.quantity,
                    "price": item.price,
                    "description": item.description,
                }
            )

    try:
        movement = movement_crud.update_inventory_movement(
            db, movement_id, movement_update, items_data
        )
        if not movement:
            raise HTTPException(status_code=404, detail="Движение товаров не найдено")
        return movement
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка при обновлении движения: {str(e)}"
        )


def delete_inventory_movement(db: Session, movement_id: int):
    """Удалить движение товаров"""
    try:
        success = movement_crud.delete_inventory_movement(db, movement_id)
        if not success:
            raise HTTPException(status_code=404, detail="Движение товаров не найдено")
        return {"message": "Движение товаров успешно удалено"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def approve_inventory_movement(
    db: Session, movement_id: int, approval: MovementApproval
):
    """Утвердить движение товаров"""
    try:
        movement = movement_crud.approve_inventory_movement(
            db, movement_id, approval.approved_by
        )
        return movement
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def execute_inventory_movement(
    db: Session, movement_id: int, execution: MovementExecution
):
    """Выполнить движение товаров"""
    try:
        movement = movement_crud.execute_inventory_movement(
            db, movement_id, execution.executed_by
        )
        return movement
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def bulk_approve_inventory_movements(
    db: Session, bulk_approval: BulkMovementApproval
) -> BulkOperationResult:
    """Массово утвердить движения товаров"""
    success_count = 0
    error_count = 0
    errors = []

    for movement_id in bulk_approval.movement_ids:
        try:
            movement_crud.approve_inventory_movement(
                db, movement_id, bulk_approval.approved_by
            )
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append({
                "movement_id": str(movement_id),
                "error": str(e)
            })

    message = f"Успешно утверждено {success_count} движений"
    if error_count > 0:
        message += f", ошибок: {error_count}"

    return BulkOperationResult(
        success_count=success_count,
        error_count=error_count,
        errors=errors,
        message=message
    )


def bulk_execute_inventory_movements(
    db: Session, bulk_execution: BulkMovementExecution
) -> BulkOperationResult:
    """Массово выполнить движения товаров"""
    success_count = 0
    error_count = 0
    errors = []

    for movement_id in bulk_execution.movement_ids:
        try:
            movement_crud.execute_inventory_movement(
                db, movement_id, bulk_execution.executed_by
            )
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append({
                "movement_id": str(movement_id),
                "error": str(e)
            })

    message = f"Успешно выполнено {success_count} движений"
    if error_count > 0:
        message += f", ошибок: {error_count}"

    return BulkOperationResult(
        success_count=success_count,
        error_count=error_count,
        errors=errors,
        message=message
    )


def get_inventory_movements_summary(
    db: Session, date_from: datetime = None, date_to: datetime = None
):
    """Получить сводку по движениям товаров"""
    return movement_crud.get_inventory_movements_summary(db, date_from, date_to)


def get_movement_items(db: Session, movement_id: int):
    """Получить позиции движения товаров"""
    items = movement_crud.get_movement_items(db, movement_id)
    if not items:
        raise HTTPException(status_code=404, detail="Позиции движения не найдены")
    return items


def get_movements_by_item(
    db: Session, item_id: int, date_from: datetime = None, date_to: datetime = None
):
    """Получить движения товаров по конкретному товару"""
    return movement_crud.get_movements_by_item(db, item_id, date_from, date_to)


def get_movements_by_warehouse(
    db: Session, warehouse_id: int, date_from: datetime = None, date_to: datetime = None
):
    """Получить движения товаров по складу"""
    return movement_crud.get_movements_by_warehouse(
        db, warehouse_id, date_from, date_to
    )


def get_movements_by_machine(
    db: Session, machine_id: int, date_from: datetime = None, date_to: datetime = None
):
    """Получить движения товаров по автомату"""
    return movement_crud.get_movements_by_machine(db, machine_id, date_from, date_to)


def get_movement_detail(db: Session, movement_id: int):
    """Получить детальную информацию о движении товаров"""
    movement = movement_crud.get_inventory_movement(db, movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Движение товаров не найдено")

    # Получаем позиции
    items = movement_crud.get_movement_items(db, movement_id)

    # Определяем права доступа
    is_approved = movement.approved_at is not None
    is_executed = movement.executed_at is not None
    can_edit = not is_approved
    can_approve = not is_approved
    can_execute = is_approved and not is_executed

    # Создаем детальный объект
    detail = {
        "id": movement.id,
        "movement_type": movement.movement_type,
        "document_date": movement.document_date,
        "status": movement.status,
        "description": movement.description,
        "from_warehouse": movement.from_warehouse,
        "to_warehouse": movement.to_warehouse,
        "from_machine": movement.from_machine,
        "to_machine": movement.to_machine,
        "counterparty": movement.counterparty,
        "created_by_user": movement.created_by_user,
        "approved_by_user": movement.approved_by_user,
        "executed_by_user": movement.executed_by_user,
        "created_at": movement.created_at,
        "approved_at": movement.approved_at,
        "executed_at": movement.executed_at,
        "total_amount": movement.total_amount,
        "currency": movement.currency,
        "items": items,
        "is_approved": is_approved,
        "is_executed": is_executed,
        "can_edit": can_edit,
        "can_approve": can_approve,
        "can_execute": can_execute,
    }

    return detail


def _validate_movement_links(db: Session, movement_data, existing_movement=None):
    """Валидация связей движения товаров"""

    # Проверяем статус
    if hasattr(movement_data, "status_id") and movement_data.status_id is not None:
        status = inventory_count_status_crud.get_by_id(db, movement_data.status_id)
        if not status:
            raise HTTPException(
                status_code=400,
                detail=f"Статус с ID {movement_data.status_id} не найден",
            )

    # Проверяем склады

    if (
        hasattr(movement_data, "from_warehouse_id")
        and movement_data.from_warehouse_id is not None
    ):
        try:
            get_warehouse(db, movement_data.from_warehouse_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Склад отправления с ID {movement_data.from_warehouse_id} не найден",
            )

    if (
        hasattr(movement_data, "to_warehouse_id")
        and movement_data.to_warehouse_id is not None
    ):
        try:
            get_warehouse(db, movement_data.to_warehouse_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Склад назначения с ID {movement_data.to_warehouse_id} не найден",
            )

    # Проверяем автоматы

    if (
        hasattr(movement_data, "from_machine_id")
        and movement_data.from_machine_id is not None
    ):
        try:
            get_machine(db, movement_data.from_machine_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Автомат отправления с ID {movement_data.from_machine_id} не найден",
            )

    if (
        hasattr(movement_data, "to_machine_id")
        and movement_data.to_machine_id is not None
    ):
        try:
            get_machine(db, movement_data.to_machine_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Автомат назначения с ID {movement_data.to_machine_id} не найден",
            )

    # Проверяем контрагента
    if (
        hasattr(movement_data, "counterparty_id")
        and movement_data.counterparty_id is not None
    ):
        try:
            get_counterparty(db, movement_data.counterparty_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Контрагент с ID {movement_data.counterparty_id} не найден",
            )

    # Проверяем пользователей
    if hasattr(movement_data, "created_by") and movement_data.created_by is not None:
        try:
            get_user_by_id(db, movement_data.created_by)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Пользователь с ID {movement_data.created_by} не найден",
            )

    # Проверяем товары в позициях
    if hasattr(movement_data, "items") and movement_data.items is not None:
        for item in movement_data.items:
            try:
                get_item(db, item.item_id)
            except HTTPException:
                raise HTTPException(
                    status_code=400, detail=f"Товар с ID {item.item_id} не найден"
                )


def _validate_movement_business_logic(
    db: Session, movement_data, existing_movement=None
):
    """Валидация бизнес-логики движения товаров"""

    movement_type = getattr(movement_data, "movement_type", None)
    if existing_movement:
        movement_type = movement_type or existing_movement.movement_type

    # Получаем все поля отправления и назначения
    from_warehouse_id = getattr(movement_data, "from_warehouse_id", None) or (
        existing_movement.from_warehouse_id if existing_movement else None
    )
    to_warehouse_id = getattr(movement_data, "to_warehouse_id", None) or (
        existing_movement.to_warehouse_id if existing_movement else None
    )
    from_machine_id = getattr(movement_data, "from_machine_id", None) or (
        existing_movement.from_machine_id if existing_movement else None
    )
    to_machine_id = getattr(movement_data, "to_machine_id", None) or (
        existing_movement.to_machine_id if existing_movement else None
    )
    counterparty_id = getattr(movement_data, "counterparty_id", None) or (
        existing_movement.counterparty_id if existing_movement else None
    )

    # Определяем логику на основе заполненных полей
    has_from = bool(from_warehouse_id or from_machine_id)
    has_to = bool(to_warehouse_id or to_machine_id)
    has_counterparty = bool(counterparty_id)

    if movement_type == "receipt":
        # Приход: должно быть место назначения и контрагент
        if not has_to:
            raise HTTPException(
                status_code=400,
                detail="Для прихода должно быть указано место назначения (склад или автомат)",
            )
        if not has_counterparty:
            raise HTTPException(
                status_code=400,
                detail="Для прихода должен быть указан контрагент (поставщик)",
            )

    elif movement_type == "issue" or movement_type == "sale":
        # Расход/продажа: должно быть место отправления
        if not has_from:
            raise HTTPException(
                status_code=400,
                detail="Для расхода должно быть указано место отправления (склад или автомат)",
            )
        if movement_type == "sale" and not has_counterparty:
            raise HTTPException(
                status_code=400,
                detail="Для продажи должен быть указан контрагент (покупатель)",
            )

    elif movement_type == "transfer":
        # Перемещение: должны быть места отправления и назначения
        if not has_from or not has_to:
            raise HTTPException(
                status_code=400,
                detail="Для перемещения должны быть указаны места отправления и назначения",
            )

    elif movement_type == "load_machine":
        # Загрузка автомата: должен быть автомат назначения
        if not to_machine_id:
            raise HTTPException(
                status_code=400,
                detail="Для загрузки автомата должен быть указан автомат назначения",
            )
            
    elif movement_type == "unload_machine":
        # Выгрузка автомата: должен быть автомат отправления
        if not from_machine_id:
            raise HTTPException(
                status_code=400,
                detail="Для выгрузки автомата должен быть указан автомат отправления",
            )

    elif movement_type == "adjustment":
        # Корректировка: должно быть указано место
        if not has_from and not has_to:
            raise HTTPException(
                status_code=400,
                detail="Для корректировки должно быть указано место (склад или автомат)",
            )
