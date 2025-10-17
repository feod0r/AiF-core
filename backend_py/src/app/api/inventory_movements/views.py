from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db

from .controllers import (
    approve_inventory_movement,
    bulk_approve_inventory_movements,
    bulk_execute_inventory_movements,
    create_inventory_movement,
    delete_inventory_movement,
    execute_inventory_movement,
    get_inventory_movement,
    get_inventory_movements,
    get_inventory_movements_count,
    get_inventory_movements_summary,
    get_movement_detail,
    get_movement_items,
    get_movements_by_item,
    get_movements_by_machine,
    get_movements_by_warehouse,
    update_inventory_movement,
)
from .models import (
    BulkMovementApproval,
    BulkMovementExecution,
    BulkOperationResult,
    InventoryMovementDetail,
    InventoryMovementIn,
    InventoryMovementOut,
    InventoryMovementSummary,
    InventoryMovementUpdate,
    MovementApproval,
    MovementExecution,
    MovementFilter,
)

router = APIRouter(prefix="/inventory-movements", tags=["inventory-movements"])


@router.get("/", response_model=List[InventoryMovementOut])
def read_inventory_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    movement_type: Optional[str] = Query(None, description="Тип движения"),
    status_id: Optional[int] = Query(None, description="ID статуса"),
    # Новые параметры для точной фильтрации по местам
    from_warehouse_id: Optional[int] = Query(None, description="ID склада отправления"),
    to_warehouse_id: Optional[int] = Query(None, description="ID склада назначения"),
    from_machine_id: Optional[int] = Query(None, description="ID автомата отправления"),
    to_machine_id: Optional[int] = Query(None, description="ID автомата назначения"),
    counterparty_id: Optional[int] = Query(None, description="ID контрагента"),
    created_by: Optional[int] = Query(None, description="ID создателя"),
    date_from: Optional[datetime] = Query(None, description="Дата с"),
    date_to: Optional[datetime] = Query(None, description="Дата по"),
    search: Optional[str] = Query(
        None, description="Поиск по номеру документа или описанию"
    ),
    db: Session = Depends(get_db),
):
    """Получить список движений товаров с фильтрацией"""
    return get_inventory_movements(
        db=db,
        skip=skip,
        limit=limit,
        movement_type=movement_type,
        status_id=status_id,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        from_machine_id=from_machine_id,
        to_machine_id=to_machine_id,
        counterparty_id=counterparty_id,
        created_by=created_by,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )


@router.get("/summary", response_model=InventoryMovementSummary)
def read_inventory_movements_summary(
    date_from: Optional[datetime] = Query(None, description="Дата с"),
    date_to: Optional[datetime] = Query(None, description="Дата по"),
    db: Session = Depends(get_db),
):
    """Получить сводку по движениям товаров"""
    return get_inventory_movements_summary(db=db, date_from=date_from, date_to=date_to)


@router.get("/count")
def read_inventory_movements_count(
    movement_type: Optional[str] = Query(None, description="Тип движения"),
    status_id: Optional[int] = Query(None, description="ID статуса"),
    from_warehouse_id: Optional[int] = Query(None, description="ID склада отправления"),
    to_warehouse_id: Optional[int] = Query(None, description="ID склада назначения"),
    from_machine_id: Optional[int] = Query(None, description="ID автомата отправления"),
    to_machine_id: Optional[int] = Query(None, description="ID автомата назначения"),
    counterparty_id: Optional[int] = Query(None, description="ID контрагента"),
    created_by: Optional[int] = Query(None, description="ID создателя"),
    date_from: Optional[datetime] = Query(None, description="Дата с"),
    date_to: Optional[datetime] = Query(None, description="Дата по"),
    search: Optional[str] = Query(None, description="Поиск по номеру документа или описанию"),
    db: Session = Depends(get_db),
):
    """Получить общее количество движений товаров с фильтрацией"""
    return get_inventory_movements_count(
        db=db,
        movement_type=movement_type,
        status_id=status_id,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        from_machine_id=from_machine_id,
        to_machine_id=to_machine_id,
        counterparty_id=counterparty_id,
        created_by=created_by,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )


@router.get("/{movement_id}", response_model=InventoryMovementOut)
def read_inventory_movement(movement_id: int, db: Session = Depends(get_db)):
    """Получить движение товаров по ID"""
    return get_inventory_movement(db=db, movement_id=movement_id)


@router.get("/{movement_id}/detail", response_model=InventoryMovementDetail)
def read_inventory_movement_detail(movement_id: int, db: Session = Depends(get_db)):
    """Получить детальную информацию о движении товаров"""
    return get_movement_detail(db=db, movement_id=movement_id)


@router.get("/{movement_id}/items", response_model=List[dict])
def read_movement_items(movement_id: int, db: Session = Depends(get_db)):
    """Получить позиции движения товаров"""
    return get_movement_items(db=db, movement_id=movement_id)


@router.post("/", response_model=InventoryMovementOut)
def create_inventory_movement_endpoint(
    movement_in: InventoryMovementIn, db: Session = Depends(get_db)
):
    """Создать новое движение товаров"""
    return create_inventory_movement(db=db, movement_in=movement_in)


@router.put("/{movement_id}", response_model=InventoryMovementOut)
def update_inventory_movement_endpoint(
    movement_id: int,
    movement_update: InventoryMovementUpdate,
    db: Session = Depends(get_db),
):
    """Обновить движение товаров"""
    return update_inventory_movement(
        db=db, movement_id=movement_id, movement_update=movement_update
    )


@router.delete("/{movement_id}")
def delete_inventory_movement_endpoint(movement_id: int, db: Session = Depends(get_db)):
    """Удалить движение товаров"""
    return delete_inventory_movement(db=db, movement_id=movement_id)


@router.post("/{movement_id}/approve", response_model=InventoryMovementOut)
def approve_inventory_movement_endpoint(
    movement_id: int, approval: MovementApproval, db: Session = Depends(get_db)
):
    """Утвердить движение товаров"""
    return approve_inventory_movement(db=db, movement_id=movement_id, approval=approval)


@router.post("/{movement_id}/execute", response_model=InventoryMovementOut)
def execute_inventory_movement_endpoint(
    movement_id: int, execution: MovementExecution, db: Session = Depends(get_db)
):
    """Выполнить движение товаров (провести по остаткам)"""
    return execute_inventory_movement(
        db=db, movement_id=movement_id, execution=execution
    )


@router.post("/bulk-approve", response_model=BulkOperationResult)
def bulk_approve_inventory_movements_endpoint(
    bulk_approval: BulkMovementApproval, db: Session = Depends(get_db)
):
    """Массово утвердить движения товаров"""
    return bulk_approve_inventory_movements(db=db, bulk_approval=bulk_approval)


@router.post("/bulk-execute", response_model=BulkOperationResult)
def bulk_execute_inventory_movements_endpoint(
    bulk_execution: BulkMovementExecution, db: Session = Depends(get_db)
):
    """Массово выполнить движения товаров"""
    return bulk_execute_inventory_movements(db=db, bulk_execution=bulk_execution)


# Специальные эндпоинты для фильтрации


@router.get("/item/{item_id}", response_model=List[InventoryMovementOut])
def read_movements_by_item(
    item_id: int,
    date_from: Optional[datetime] = Query(None, description="Дата с"),
    date_to: Optional[datetime] = Query(None, description="Дата по"),
    db: Session = Depends(get_db),
):
    """Получить движения товаров по конкретному товару"""
    return get_movements_by_item(
        db=db, item_id=item_id, date_from=date_from, date_to=date_to
    )


@router.get("/warehouse/{warehouse_id}", response_model=List[InventoryMovementOut])
def read_movements_by_warehouse(
    warehouse_id: int,
    date_from: Optional[datetime] = Query(None, description="Дата с"),
    date_to: Optional[datetime] = Query(None, description="Дата по"),
    db: Session = Depends(get_db),
):
    """Получить движения товаров по складу"""
    return get_movements_by_warehouse(
        db=db, warehouse_id=warehouse_id, date_from=date_from, date_to=date_to
    )


@router.get("/machine/{machine_id}", response_model=List[InventoryMovementOut])
def read_movements_by_machine(
    machine_id: int,
    date_from: Optional[datetime] = Query(None, description="Дата с"),
    date_to: Optional[datetime] = Query(None, description="Дата по"),
    db: Session = Depends(get_db),
):
    """Получить движения товаров по автомату"""
    return get_movements_by_machine(
        db=db, machine_id=machine_id, date_from=date_from, date_to=date_to
    )


# Эндпоинты для типов движений


@router.get("/type/receipt", response_model=List[InventoryMovementOut])
def read_receipt_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить приходные движения товаров"""
    return get_inventory_movements(
        db=db, skip=skip, limit=limit, movement_type="receipt"
    )


@router.get("/type/issue", response_model=List[InventoryMovementOut])
def read_issue_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить расходные движения товаров"""
    return get_inventory_movements(db=db, skip=skip, limit=limit, movement_type="issue")


@router.get("/type/transfer", response_model=List[InventoryMovementOut])
def read_transfer_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить перемещения товаров"""
    return get_inventory_movements(
        db=db, skip=skip, limit=limit, movement_type="transfer"
    )


@router.get("/type/adjustment", response_model=List[InventoryMovementOut])
def read_adjustment_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить корректировки остатков"""
    return get_inventory_movements(
        db=db, skip=skip, limit=limit, movement_type="adjustment"
    )


@router.get("/type/load-machine", response_model=List[InventoryMovementOut])
def read_load_machine_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить загрузки автоматов"""
    return get_inventory_movements(
        db=db, skip=skip, limit=limit, movement_type="load_machine"
    )


@router.get("/type/unload-machine", response_model=List[InventoryMovementOut])
def read_unload_machine_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить выгрузки автоматов"""
    return get_inventory_movements(
        db=db, skip=skip, limit=limit, movement_type="unload_machine"
    )


# Эндпоинты для статусов


@router.get("/status/draft", response_model=List[InventoryMovementOut])
def read_draft_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить черновики движений товаров"""
    # Предполагаем, что статус "Черновик" имеет ID 1
    return get_inventory_movements(db=db, skip=skip, limit=limit, status_id=1)


@router.get("/status/approved", response_model=List[InventoryMovementOut])
def read_approved_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить утвержденные движения товаров"""
    # Предполагаем, что статус "Утвержден" имеет ID 2
    return get_inventory_movements(db=db, skip=skip, limit=limit, status_id=2)


@router.get("/status/executed", response_model=List[InventoryMovementOut])
def read_executed_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить выполненные движения товаров"""
    # Предполагаем, что статус "Выполнен" имеет ID 3
    return get_inventory_movements(db=db, skip=skip, limit=limit, status_id=3)
