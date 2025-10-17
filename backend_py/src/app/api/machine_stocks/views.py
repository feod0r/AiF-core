from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db

from .controllers import (
    add_machine_stock,
    create_machine_stock,
    delete_machine_stock,
    get_low_stock_machines,
    get_machine_stock,
    get_machine_stock_by_item,
    get_machine_stocks,
    get_machine_stocks_count,
    get_machine_stocks_by_item,
    get_machine_stocks_by_machine,
    get_machine_stocks_grouped_by_machines,
    get_machine_stocks_summary,
    get_machine_utilization,
    get_stock_detail,
    load_machine_from_warehouse,
    remove_machine_stock,
    transfer_machine_stock,
    unload_machine_to_warehouse,
    update_machine_stock,
)
from .models import (
    LowStockMachine,
    MachineLoadOperation,
    MachineStockDetail,
    MachineStockFilter,
    MachineStockIn,
    MachineStockOperation,
    MachineStockOut,
    MachineStockSummary,
    MachineStockTransfer,
    MachineStockUpdate,
    MachineUnloadOperation,
    MachineUtilization,
)

router = APIRouter(prefix="/machine-stocks", tags=["machine-stocks"])


@router.get("/", response_model=List[MachineStockOut])
def read_machine_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    machine_id: Optional[int] = Query(None, description="ID автомата"),
    item_id: Optional[int] = Query(None, description="ID товара"),
    category_id: Optional[int] = Query(None, description="ID категории товара"),
    low_stock: Optional[bool] = Query(None, description="Низкие остатки"),
    search: Optional[str] = Query(
        None, description="Поиск по названию товара, артикулу, штрихкоду"
    ),
    db: Session = Depends(get_db),
):
    """Получить список остатков в автоматах с фильтрацией"""
    return get_machine_stocks(
        db=db,
        skip=skip,
        limit=limit,
        machine_id=machine_id,
        item_id=item_id,
        category_id=category_id,
        low_stock=low_stock,
        search=search,
    )


@router.get("/summary", response_model=MachineStockSummary)
def read_machine_stocks_summary(
    machine_id: Optional[int] = Query(None, description="ID автомата"),
    db: Session = Depends(get_db),
):
    """Получить сводку по остаткам в автоматах"""
    return get_machine_stocks_summary(db=db, machine_id=machine_id)


@router.get("/count")
def read_machine_stocks_count(
    machine_id: Optional[int] = Query(None, description="ID автомата"),
    item_id: Optional[int] = Query(None, description="ID товара"),
    category_id: Optional[int] = Query(None, description="ID категории товара"),
    low_stock: Optional[bool] = Query(None, description="Низкие остатки"),
    search: Optional[str] = Query(
        None, description="Поиск по названию товара, артикулу, штрихкоду"
    ),
    db: Session = Depends(get_db),
):
    """Получить количество остатков в автоматах с фильтрацией"""
    return {"count": get_machine_stocks_count(
        db=db,
        machine_id=machine_id,
        item_id=item_id,
        category_id=category_id,
        low_stock=low_stock,
        search=search,
    )}


@router.get("/grouped-by-machines", response_model=List[dict])
def read_machine_stocks_grouped_by_machines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    machine_id: Optional[int] = Query(None, description="ID автомата"),
    item_id: Optional[int] = Query(None, description="ID товара"),
    category_id: Optional[int] = Query(None, description="ID категории товара"),
    low_stock: Optional[bool] = Query(None, description="Низкие остатки"),
    search: Optional[str] = Query(
        None, description="Поиск по названию товара, артикулу, штрихкоду"
    ),
    db: Session = Depends(get_db),
):
    """Получить остатки в автоматах, сгруппированные по автоматам"""
    return get_machine_stocks_grouped_by_machines(
        db=db,
        skip=skip,
        limit=limit,
        machine_id=machine_id,
        item_id=item_id,
        category_id=category_id,
        low_stock=low_stock,
        search=search,
    )


@router.get("/{stock_id}", response_model=MachineStockOut)
def read_machine_stock(stock_id: int, db: Session = Depends(get_db)):
    """Получить остаток в автомате по ID"""
    return get_machine_stock(db=db, stock_id=stock_id)


@router.get("/{stock_id}/detail", response_model=MachineStockDetail)
def read_stock_detail(stock_id: int, db: Session = Depends(get_db)):
    """Получить детальную информацию об остатке в автомате"""
    return get_stock_detail(db=db, stock_id=stock_id)


@router.get("/machine/{machine_id}/item/{item_id}", response_model=MachineStockOut)
def read_machine_stock_by_item(
    machine_id: int, item_id: int, db: Session = Depends(get_db)
):
    """Получить остаток в автомате по товару и автомату"""
    return get_machine_stock_by_item(db=db, machine_id=machine_id, item_id=item_id)


@router.post("/", response_model=MachineStockOut)
def create_machine_stock_endpoint(
    stock_in: MachineStockIn, db: Session = Depends(get_db)
):
    """Создать новый остаток в автомате"""
    return create_machine_stock(db=db, stock_in=stock_in)


@router.put("/{stock_id}", response_model=MachineStockOut)
def update_machine_stock_endpoint(
    stock_id: int, stock_update: MachineStockUpdate, db: Session = Depends(get_db)
):
    """Обновить остаток в автомате"""
    return update_machine_stock(db=db, stock_id=stock_id, stock_update=stock_update)


@router.delete("/{stock_id}")
def delete_machine_stock_endpoint(stock_id: int, db: Session = Depends(get_db)):
    """Удалить остаток в автомате"""
    return delete_machine_stock(db=db, stock_id=stock_id)


# Операции с остатками


@router.post("/machine/{machine_id}/item/{item_id}/add", response_model=MachineStockOut)
def add_stock_endpoint(
    machine_id: int,
    item_id: int,
    operation: MachineStockOperation,
    db: Session = Depends(get_db),
):
    """Добавить товар в автомат"""
    return add_machine_stock(
        db=db, machine_id=machine_id, item_id=item_id, operation=operation
    )


@router.post(
    "/machine/{machine_id}/item/{item_id}/remove", response_model=MachineStockOut
)
def remove_stock_endpoint(
    machine_id: int,
    item_id: int,
    operation: MachineStockOperation,
    db: Session = Depends(get_db),
):
    """Убрать товар из автомата"""
    return remove_machine_stock(
        db=db, machine_id=machine_id, item_id=item_id, operation=operation
    )


@router.post("/transfer", response_model=dict)
def transfer_stock_endpoint(
    transfer: MachineStockTransfer, db: Session = Depends(get_db)
):
    """Переместить товар между автоматами"""
    return transfer_machine_stock(db=db, transfer=transfer)


# Операции загрузки/выгрузки со складов


@router.post("/machine/{machine_id}/item/{item_id}/load", response_model=dict)
def load_machine_endpoint(
    machine_id: int,
    item_id: int,
    operation: MachineLoadOperation,
    db: Session = Depends(get_db),
):
    """Загрузить автомат товаром со склада"""
    return load_machine_from_warehouse(
        db=db, machine_id=machine_id, item_id=item_id, operation=operation
    )


@router.post("/machine/{machine_id}/item/{item_id}/unload", response_model=dict)
def unload_machine_endpoint(
    machine_id: int,
    item_id: int,
    operation: MachineUnloadOperation,
    db: Session = Depends(get_db),
):
    """Выгрузить товар из автомата на склад"""
    return unload_machine_to_warehouse(
        db=db, machine_id=machine_id, item_id=item_id, operation=operation
    )


# Специальные эндпоинты для фильтрации


@router.get("/machine/{machine_id}", response_model=List[MachineStockOut])
def read_stocks_by_machine(machine_id: int, db: Session = Depends(get_db)):
    """Получить все остатки в конкретном автомате"""
    return get_machine_stocks_by_machine(db=db, machine_id=machine_id)


@router.get("/item/{item_id}", response_model=List[MachineStockOut])
def read_stocks_by_item(item_id: int, db: Session = Depends(get_db)):
    """Получить все остатки конкретного товара во всех автоматах"""
    return get_machine_stocks_by_item(db=db, item_id=item_id)


@router.get("/low-stock", response_model=List[LowStockMachine])
def read_low_stock_machines(db: Session = Depends(get_db)):
    """Получить автоматы с товарами, у которых низкие остатки"""
    return get_low_stock_machines(db=db)


@router.get("/utilization", response_model=List[MachineUtilization])
def read_machine_utilization(
    machine_id: Optional[int] = Query(None, description="ID автомата"),
    db: Session = Depends(get_db),
):
    """Получить информацию о загрузке автоматов"""
    return get_machine_utilization(db=db, machine_id=machine_id)


# Эндпоинты для фильтрации по статусам


@router.get("/low-stock-items", response_model=List[MachineStockOut])
def read_low_stock_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить товары с низкими остатками в автоматах"""
    return get_machine_stocks(db=db, skip=skip, limit=limit, low_stock=True)


@router.get("/normal-stock-items", response_model=List[MachineStockOut])
def read_normal_stock_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить товары с нормальными остатками в автоматах"""
    return get_machine_stocks(db=db, skip=skip, limit=limit, low_stock=False)


@router.get("/full-machines", response_model=List[MachineStockOut])
def read_full_machines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить товары в полностью загруженных автоматах"""
    stocks = get_machine_stocks(db=db, skip=skip, limit=limit)
    full_machines = []
    for stock in stocks:
        if stock.capacity and stock.quantity >= stock.capacity:
            full_machines.append(stock)
    return full_machines


# Эндпоинты для аналитики


@router.get("/machine/{machine_id}/summary", response_model=MachineStockSummary)
def read_machine_summary(machine_id: int, db: Session = Depends(get_db)):
    """Получить сводку по конкретному автомату"""
    return get_machine_stocks_summary(db=db, machine_id=machine_id)


@router.get("/item/{item_id}/summary", response_model=dict)
def read_item_stock_summary(item_id: int, db: Session = Depends(get_db)):
    """Получить сводку по остаткам конкретного товара во всех автоматах"""
    stocks = get_machine_stocks_by_item(db=db, item_id=item_id)

    total_quantity = sum(stock.quantity for stock in stocks)
    total_capacity = sum(stock.capacity for stock in stocks if stock.capacity)
    total_utilization = 0
    if total_capacity > 0:
        total_utilization = float(total_quantity / total_capacity * 100)

    machines_with_stock = len([stock for stock in stocks if stock.quantity > 0])
    low_stock_machines = len(
        [stock for stock in stocks if stock.quantity <= stock.min_quantity]
    )
    full_machines = len(
        [
            stock
            for stock in stocks
            if stock.capacity and stock.quantity >= stock.capacity
        ]
    )

    return {
        "item_id": item_id,
        "total_quantity": float(total_quantity),
        "total_capacity": float(total_capacity),
        "total_utilization": total_utilization,
        "machines_with_stock": machines_with_stock,
        "low_stock_machines": low_stock_machines,
        "full_machines": full_machines,
        "stocks": [
            {
                "machine_id": stock.machine_id,
                "machine_name": stock.machine.name if stock.machine else None,
                "quantity": float(stock.quantity),
                "capacity": float(stock.capacity) if stock.capacity else None,
                "min_quantity": float(stock.min_quantity),
                "utilization_percent": float(stock.quantity / stock.capacity * 100)
                if stock.capacity
                else None,
            }
            for stock in stocks
        ],
    }


# Эндпоинты для массовых операций


@router.post("/bulk/add", response_model=List[MachineStockOut])
def add_stocks_bulk(
    operations: List[dict],  # Список {machine_id: int, item_id: int, quantity: Decimal}
    db: Session = Depends(get_db),
):
    """Добавить товары в автоматы (массовая операция)"""
    added_stocks = []
    for operation_data in operations:
        try:
            operation = MachineStockOperation(quantity=operation_data["quantity"])
            stock = add_machine_stock(
                db=db,
                machine_id=operation_data["machine_id"],
                item_id=operation_data["item_id"],
                operation=operation,
            )
            added_stocks.append(stock)
        except HTTPException:
            # Пропускаем операции с ошибками и продолжаем
            continue

    if not added_stocks:
        raise HTTPException(
            status_code=400, detail="Не удалось добавить ни одного товара"
        )

    return added_stocks


@router.post("/bulk/remove", response_model=List[MachineStockOut])
def remove_stocks_bulk(
    operations: List[dict],  # Список {machine_id: int, item_id: int, quantity: Decimal}
    db: Session = Depends(get_db),
):
    """Убрать товары из автоматов (массовая операция)"""
    removed_stocks = []
    for operation_data in operations:
        try:
            operation = MachineStockOperation(quantity=operation_data["quantity"])
            stock = remove_machine_stock(
                db=db,
                machine_id=operation_data["machine_id"],
                item_id=operation_data["item_id"],
                operation=operation,
            )
            removed_stocks.append(stock)
        except HTTPException:
            # Пропускаем операции с ошибками и продолжаем
            continue

    if not removed_stocks:
        raise HTTPException(
            status_code=400, detail="Не удалось убрать ни одного товара"
        )

    return removed_stocks


@router.post("/bulk/transfer", response_model=List[dict])
def transfer_stocks_bulk(
    transfers: List[MachineStockTransfer], db: Session = Depends(get_db)
):
    """Переместить товары между автоматами (массовая операция)"""
    transfer_results = []
    for transfer in transfers:
        try:
            result = transfer_machine_stock(db=db, transfer=transfer)
            transfer_results.append(result)
        except HTTPException:
            # Пропускаем операции с ошибками и продолжаем
            continue

    if not transfer_results:
        raise HTTPException(
            status_code=400, detail="Не удалось выполнить ни одного перемещения"
        )

    return transfer_results


@router.post("/bulk/load", response_model=List[dict])
def load_machines_bulk(
    operations: List[
        dict
    ],  # Список {machine_id: int, item_id: int, warehouse_id: int, quantity: Decimal}
    db: Session = Depends(get_db),
):
    """Загрузить автоматы товарами со складов (массовая операция)"""
    load_results = []
    for operation_data in operations:
        try:
            operation = MachineLoadOperation(
                warehouse_id=operation_data["warehouse_id"],
                quantity=operation_data["quantity"],
            )
            result = load_machine_from_warehouse(
                db=db,
                machine_id=operation_data["machine_id"],
                item_id=operation_data["item_id"],
                operation=operation,
            )
            load_results.append(result)
        except HTTPException:
            # Пропускаем операции с ошибками и продолжаем
            continue

    if not load_results:
        raise HTTPException(
            status_code=400, detail="Не удалось загрузить ни одного автомата"
        )

    return load_results


@router.post("/bulk/unload", response_model=List[dict])
def unload_machines_bulk(
    operations: List[
        dict
    ],  # Список {machine_id: int, item_id: int, warehouse_id: int, quantity: Decimal}
    db: Session = Depends(get_db),
):
    """Выгрузить товары из автоматов на склады (массовая операция)"""
    unload_results = []
    for operation_data in operations:
        try:
            operation = MachineUnloadOperation(
                warehouse_id=operation_data["warehouse_id"],
                quantity=operation_data["quantity"],
            )
            result = unload_machine_to_warehouse(
                db=db,
                machine_id=operation_data["machine_id"],
                item_id=operation_data["item_id"],
                operation=operation,
            )
            unload_results.append(result)
        except HTTPException:
            # Пропускаем операции с ошибками и продолжаем
            continue

    if not unload_results:
        raise HTTPException(
            status_code=400, detail="Не удалось выгрузить ни одного автомата"
        )

    return unload_results


# Эндпоинты для отчетов


@router.get("/report/low-stock", response_model=List[dict])
def get_low_stock_report(
    machine_id: Optional[int] = Query(None, description="ID автомата"),
    db: Session = Depends(get_db),
):
    """Получить отчет по товарам с низкими остатками в автоматах"""
    if machine_id:
        stocks = get_machine_stocks(db=db, machine_id=machine_id, low_stock=True)
    else:
        stocks = get_machine_stocks(db=db, low_stock=True)

    report = []
    for stock in stocks:
        report.append(
            {
                "machine_id": stock.machine_id,
                "machine_name": stock.machine.name if stock.machine else None,
                "item_id": stock.item_id,
                "item_name": stock.item.name if stock.item else None,
                "item_sku": stock.item.sku if stock.item else None,
                "current_quantity": float(stock.quantity),
                "min_quantity": float(stock.min_quantity),
                "shortage": float(stock.min_quantity - stock.quantity),
                "capacity": float(stock.capacity) if stock.capacity else None,
            }
        )

    return report


@router.get("/report/full-machines", response_model=List[dict])
def get_full_machines_report(
    machine_id: Optional[int] = Query(None, description="ID автомата"),
    db: Session = Depends(get_db),
):
    """Получить отчет по полностью загруженным автоматам"""
    if machine_id:
        stocks = get_machine_stocks(db=db, machine_id=machine_id)
    else:
        stocks = get_machine_stocks(db=db)

    report = []
    for stock in stocks:
        if stock.capacity and stock.quantity >= stock.capacity:
            report.append(
                {
                    "machine_id": stock.machine_id,
                    "machine_name": stock.machine.name if stock.machine else None,
                    "item_id": stock.item_id,
                    "item_name": stock.item.name if stock.item else None,
                    "item_sku": stock.item.sku if stock.item else None,
                    "current_quantity": float(stock.quantity),
                    "capacity": float(stock.capacity),
                    "utilization_percent": float(stock.quantity / stock.capacity * 100),
                }
            )

    return report


@router.get("/report/utilization", response_model=List[dict])
def get_utilization_report(
    machine_id: Optional[int] = Query(None, description="ID автомата"),
    db: Session = Depends(get_db),
):
    """Получить отчет по загрузке автоматов"""
    utilization_data = get_machine_utilization(db=db, machine_id=machine_id)

    report = []
    for util in utilization_data:
        report.append(
            {
                "machine_id": util.machine_id,
                "machine_name": util.machine_name,
                "total_capacity": util.total_capacity,
                "total_quantity": util.total_quantity,
                "utilization_percent": util.utilization_percent,
                "items_count": util.items_count,
                "low_stock_items": util.low_stock_items,
                "full_items": util.full_items,
            }
        )

    return report
