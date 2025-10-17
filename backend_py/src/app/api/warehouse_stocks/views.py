from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db

from .controllers import (
    add_warehouse_stock,
    create_warehouse_stock,
    delete_warehouse_stock,
    get_low_stock_warehouses,
    get_stock_detail,
    get_warehouse_stock,
    get_warehouse_stock_by_item,
    get_warehouse_stocks,
    get_warehouse_stocks_by_item,
    get_warehouse_stocks_by_warehouse,
    get_warehouse_stocks_summary,
    release_warehouse_stock,
    remove_warehouse_stock,
    reserve_warehouse_stock,
    transfer_warehouse_stock,
    update_warehouse_stock,
)
from .models import (
    LowStockWarehouse,
    StockFilter,
    StockOperation,
    StockReservation,
    StockTransfer,
    WarehouseStockDetail,
    WarehouseStockIn,
    WarehouseStockOut,
    WarehouseStockSummary,
    WarehouseStockUpdate,
)

router = APIRouter(prefix="/warehouse-stocks", tags=["warehouse-stocks"])


@router.get("/", response_model=List[WarehouseStockOut])
def read_warehouse_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    warehouse_id: Optional[int] = Query(None, description="ID склада"),
    item_id: Optional[int] = Query(None, description="ID товара"),
    low_stock: Optional[bool] = Query(None, description="Низкие остатки"),
    search: Optional[str] = Query(
        None, description="Поиск по названию товара, артикулу, штрихкоду"
    ),
    db: Session = Depends(get_db),
):
    """Получить список складских остатков с фильтрацией"""
    return get_warehouse_stocks(
        db=db,
        skip=skip,
        limit=limit,
        warehouse_id=warehouse_id,
        item_id=item_id,
        low_stock=low_stock,
        search=search,
    )


@router.get("/summary", response_model=WarehouseStockSummary)
def read_warehouse_stocks_summary(
    warehouse_id: Optional[int] = Query(None, description="ID склада"),
    db: Session = Depends(get_db),
):
    """Получить сводку по складским остаткам"""
    return get_warehouse_stocks_summary(db=db, warehouse_id=warehouse_id)


@router.get("/{stock_id}", response_model=WarehouseStockOut)
def read_warehouse_stock(stock_id: int, db: Session = Depends(get_db)):
    """Получить складской остаток по ID"""
    return get_warehouse_stock(db=db, stock_id=stock_id)


@router.get("/{stock_id}/detail", response_model=WarehouseStockDetail)
def read_stock_detail(stock_id: int, db: Session = Depends(get_db)):
    """Получить детальную информацию о складском остатке"""
    return get_stock_detail(db=db, stock_id=stock_id)


@router.get(
    "/warehouse/{warehouse_id}/item/{item_id}", response_model=WarehouseStockOut
)
def read_warehouse_stock_by_item(
    warehouse_id: int, item_id: int, db: Session = Depends(get_db)
):
    """Получить складской остаток по товару и складу"""
    return get_warehouse_stock_by_item(
        db=db, warehouse_id=warehouse_id, item_id=item_id
    )


@router.post("/", response_model=WarehouseStockOut)
def create_warehouse_stock_endpoint(
    stock_in: WarehouseStockIn, db: Session = Depends(get_db)
):
    """Создать новый складской остаток"""
    return create_warehouse_stock(db=db, stock_in=stock_in)


@router.put("/{stock_id}", response_model=WarehouseStockOut)
def update_warehouse_stock_endpoint(
    stock_id: int, stock_update: WarehouseStockUpdate, db: Session = Depends(get_db)
):
    """Обновить складской остаток"""
    return update_warehouse_stock(db=db, stock_id=stock_id, stock_update=stock_update)


@router.delete("/{stock_id}")
def delete_warehouse_stock_endpoint(stock_id: int, db: Session = Depends(get_db)):
    """Удалить складской остаток"""
    return delete_warehouse_stock(db=db, stock_id=stock_id)


# Операции с остатками


@router.post(
    "/warehouse/{warehouse_id}/item/{item_id}/add", response_model=WarehouseStockOut
)
def add_stock_endpoint(
    warehouse_id: int,
    item_id: int,
    operation: StockOperation,
    db: Session = Depends(get_db),
):
    """Добавить товар на склад (приход)"""
    return add_warehouse_stock(
        db=db, warehouse_id=warehouse_id, item_id=item_id, operation=operation
    )


@router.post(
    "/warehouse/{warehouse_id}/item/{item_id}/remove", response_model=WarehouseStockOut
)
def remove_stock_endpoint(
    warehouse_id: int,
    item_id: int,
    operation: StockOperation,
    db: Session = Depends(get_db),
):
    """Убрать товар со склада (расход)"""
    return remove_warehouse_stock(
        db=db, warehouse_id=warehouse_id, item_id=item_id, operation=operation
    )


@router.post(
    "/warehouse/{warehouse_id}/item/{item_id}/reserve", response_model=WarehouseStockOut
)
def reserve_stock_endpoint(
    warehouse_id: int,
    item_id: int,
    reservation: StockReservation,
    db: Session = Depends(get_db),
):
    """Зарезервировать товар на складе"""
    return reserve_warehouse_stock(
        db=db, warehouse_id=warehouse_id, item_id=item_id, reservation=reservation
    )


@router.post(
    "/warehouse/{warehouse_id}/item/{item_id}/release", response_model=WarehouseStockOut
)
def release_stock_endpoint(
    warehouse_id: int,
    item_id: int,
    reservation: StockReservation,
    db: Session = Depends(get_db),
):
    """Снять резервирование товара на складе"""
    return release_warehouse_stock(
        db=db, warehouse_id=warehouse_id, item_id=item_id, reservation=reservation
    )


@router.post("/transfer", response_model=dict)
def transfer_stock_endpoint(transfer: StockTransfer, db: Session = Depends(get_db)):
    """Переместить товар между складами"""
    return transfer_warehouse_stock(db=db, transfer=transfer)


# Специальные эндпоинты для фильтрации


@router.get("/warehouse/{warehouse_id}", response_model=List[WarehouseStockOut])
def read_stocks_by_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    """Получить все остатки на конкретном складе"""
    return get_warehouse_stocks_by_warehouse(db=db, warehouse_id=warehouse_id)


@router.get("/item/{item_id}", response_model=List[WarehouseStockOut])
def read_stocks_by_item(item_id: int, db: Session = Depends(get_db)):
    """Получить все остатки конкретного товара на всех складах"""
    return get_warehouse_stocks_by_item(db=db, item_id=item_id)


@router.get("/low-stock", response_model=List[LowStockWarehouse])
def read_low_stock_warehouses(db: Session = Depends(get_db)):
    """Получить склады с товарами, у которых низкие остатки"""
    return get_low_stock_warehouses(db=db)


# Эндпоинты для фильтрации по статусам


@router.get("/low-stock-items", response_model=List[WarehouseStockOut])
def read_low_stock_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить товары с низкими остатками"""
    return get_warehouse_stocks(db=db, skip=skip, limit=limit, low_stock=True)


@router.get("/normal-stock-items", response_model=List[WarehouseStockOut])
def read_normal_stock_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить товары с нормальными остатками"""
    return get_warehouse_stocks(db=db, skip=skip, limit=limit, low_stock=False)


@router.get("/overstock-items", response_model=List[WarehouseStockOut])
def read_overstock_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить товары с избыточными остатками (превышение максимального количества)"""
    stocks = get_warehouse_stocks(db=db, skip=skip, limit=limit)
    overstock_items = []
    for stock in stocks:
        if stock.max_quantity and stock.quantity > stock.max_quantity:
            overstock_items.append(stock)
    return overstock_items


# Эндпоинты для аналитики


@router.get("/warehouse/{warehouse_id}/summary", response_model=WarehouseStockSummary)
def read_warehouse_summary(warehouse_id: int, db: Session = Depends(get_db)):
    """Получить сводку по конкретному складу"""
    return get_warehouse_stocks_summary(db=db, warehouse_id=warehouse_id)


@router.get("/item/{item_id}/summary", response_model=dict)
def read_item_stock_summary(item_id: int, db: Session = Depends(get_db)):
    """Получить сводку по остаткам конкретного товара на всех складах"""
    stocks = get_warehouse_stocks_by_item(db=db, item_id=item_id)

    total_quantity = sum(stock.quantity for stock in stocks)
    total_reserved = sum(stock.reserved_quantity for stock in stocks)
    total_available = total_quantity - total_reserved

    warehouses_with_stock = len([stock for stock in stocks if stock.quantity > 0])
    low_stock_warehouses = len(
        [stock for stock in stocks if stock.quantity <= stock.min_quantity]
    )

    return {
        "item_id": item_id,
        "total_quantity": float(total_quantity),
        "total_reserved": float(total_reserved),
        "total_available": float(total_available),
        "warehouses_with_stock": warehouses_with_stock,
        "low_stock_warehouses": low_stock_warehouses,
        "stocks": [
            {
                "warehouse_id": stock.warehouse_id,
                "warehouse_name": stock.warehouse.name if stock.warehouse else None,
                "quantity": float(stock.quantity),
                "reserved_quantity": float(stock.reserved_quantity),
                "available_quantity": float(stock.quantity - stock.reserved_quantity),
                "min_quantity": float(stock.min_quantity),
                "max_quantity": float(stock.max_quantity)
                if stock.max_quantity
                else None,
                "location": stock.location,
            }
            for stock in stocks
        ],
    }


# Эндпоинты для массовых операций


@router.post("/bulk/add", response_model=List[WarehouseStockOut])
def add_stocks_bulk(
    operations: List[
        dict
    ],  # Список {warehouse_id: int, item_id: int, quantity: Decimal}
    db: Session = Depends(get_db),
):
    """Добавить товары на склады (массовая операция)"""
    added_stocks = []
    for operation_data in operations:
        try:
            operation = StockOperation(quantity=operation_data["quantity"])
            stock = add_warehouse_stock(
                db=db,
                warehouse_id=operation_data["warehouse_id"],
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


@router.post("/bulk/remove", response_model=List[WarehouseStockOut])
def remove_stocks_bulk(
    operations: List[
        dict
    ],  # Список {warehouse_id: int, item_id: int, quantity: Decimal}
    db: Session = Depends(get_db),
):
    """Убрать товары со складов (массовая операция)"""
    removed_stocks = []
    for operation_data in operations:
        try:
            operation = StockOperation(quantity=operation_data["quantity"])
            stock = remove_warehouse_stock(
                db=db,
                warehouse_id=operation_data["warehouse_id"],
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
def transfer_stocks_bulk(transfers: List[StockTransfer], db: Session = Depends(get_db)):
    """Переместить товары между складами (массовая операция)"""
    transfer_results = []
    for transfer in transfers:
        try:
            result = transfer_warehouse_stock(db=db, transfer=transfer)
            transfer_results.append(result)
        except HTTPException:
            # Пропускаем операции с ошибками и продолжаем
            continue

    if not transfer_results:
        raise HTTPException(
            status_code=400, detail="Не удалось выполнить ни одного перемещения"
        )

    return transfer_results


# Эндпоинты для отчетов


@router.get("/report/low-stock", response_model=List[dict])
def get_low_stock_report(
    warehouse_id: Optional[int] = Query(None, description="ID склада"),
    db: Session = Depends(get_db),
):
    """Получить отчет по товарам с низкими остатками"""
    if warehouse_id:
        stocks = get_warehouse_stocks(db=db, warehouse_id=warehouse_id, low_stock=True)
    else:
        stocks = get_warehouse_stocks(db=db, low_stock=True)

    report = []
    for stock in stocks:
        report.append(
            {
                "warehouse_id": stock.warehouse_id,
                "warehouse_name": stock.warehouse.name if stock.warehouse else None,
                "item_id": stock.item_id,
                "item_name": stock.item.name if stock.item else None,
                "item_sku": stock.item.sku if stock.item else None,
                "current_quantity": float(stock.quantity),
                "min_quantity": float(stock.min_quantity),
                "shortage": float(stock.min_quantity - stock.quantity),
                "location": stock.location,
            }
        )

    return report


@router.get("/report/overstock", response_model=List[dict])
def get_overstock_report(
    warehouse_id: Optional[int] = Query(None, description="ID склада"),
    db: Session = Depends(get_db),
):
    """Получить отчет по товарам с избыточными остатками"""
    if warehouse_id:
        stocks = get_warehouse_stocks(db=db, warehouse_id=warehouse_id)
    else:
        stocks = get_warehouse_stocks(db=db)

    report = []
    for stock in stocks:
        if stock.max_quantity and stock.quantity > stock.max_quantity:
            report.append(
                {
                    "warehouse_id": stock.warehouse_id,
                    "warehouse_name": stock.warehouse.name if stock.warehouse else None,
                    "item_id": stock.item_id,
                    "item_name": stock.item.name if stock.item else None,
                    "item_sku": stock.item.sku if stock.item else None,
                    "current_quantity": float(stock.quantity),
                    "max_quantity": float(stock.max_quantity),
                    "excess": float(stock.quantity - stock.max_quantity),
                    "utilization_percent": float(
                        stock.quantity / stock.max_quantity * 100
                    ),
                    "location": stock.location,
                }
            )

    return report
