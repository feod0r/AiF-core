from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db

from . import controllers
from .models import (
    WarehouseDetail,
    WarehouseIn,
    WarehouseOut,
    WarehouseSummary,
    WarehouseUpdate,
    WarehouseWithStocks,
)

router = APIRouter()


@router.get("/warehouses", response_model=List[WarehouseOut])
def read_warehouses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    owner_id: Optional[int] = Query(None, description="Фильтр по ID владельца"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    search: Optional[str] = Query(
        None, description="Поиск по названию и адресу"
    ),
    db: Session = Depends(get_db),
):
    """Получить список складов с фильтрацией"""
    return controllers.get_warehouses(
        db,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        is_active=is_active,
        search=search,
    )


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseOut)
def read_warehouse(
    warehouse_id: int = Path(..., description="ID склада"),
    db: Session = Depends(get_db),
):
    """Получить склад по ID"""
    return controllers.get_warehouse(db, warehouse_id)


@router.get("/warehouses/name/{name}", response_model=WarehouseOut)
def read_warehouse_by_name(
    name: str = Path(..., description="Название склада"), db: Session = Depends(get_db)
):
    """Получить склад по названию"""
    return controllers.get_warehouse_by_name(db, name)


@router.get("/warehouses/{warehouse_id}/detail", response_model=WarehouseDetail)
def read_warehouse_detail(
    warehouse_id: int = Path(..., description="ID склада"),
    db: Session = Depends(get_db),
):
    """Получить детальную информацию о складе"""
    return controllers.get_warehouse_detail(db, warehouse_id)


@router.get("/warehouses/owner/{owner_id}", response_model=List[WarehouseOut])
def read_warehouses_by_owner(
    owner_id: int = Path(..., description="ID владельца"), db: Session = Depends(get_db)
):
    """Получить все склады владельца"""
    return controllers.get_warehouses_by_owner(db, owner_id)


@router.get("/warehouses/with-stocks", response_model=List[WarehouseWithStocks])
def read_warehouses_with_stocks(
    owner_id: Optional[int] = Query(None, description="ID владельца для фильтрации"),
    db: Session = Depends(get_db),
):
    """Получить склады с информацией о наличии товаров"""
    return controllers.get_warehouses_with_stocks(db, owner_id)


@router.post("/warehouses", response_model=WarehouseOut)
def create_warehouse(warehouse: WarehouseIn, db: Session = Depends(get_db)):
    """Создать новый склад"""
    return controllers.create_warehouse(db, warehouse)


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(
    warehouse_id: int = Path(..., description="ID склада"),
    warehouse: WarehouseUpdate = None,
    db: Session = Depends(get_db),
):
    """Обновить склад"""
    return controllers.update_warehouse(db, warehouse_id, warehouse)


@router.delete("/warehouses/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int = Path(..., description="ID склада"),
    db: Session = Depends(get_db),
):
    """Удалить склад (мягкое удаление)"""
    return controllers.delete_warehouse(db, warehouse_id)


@router.get("/warehouses/summary", response_model=WarehouseSummary)
def read_warehouses_summary(
    owner_id: Optional[int] = Query(None, description="ID владельца для фильтрации"),
    db: Session = Depends(get_db),
):
    """Получить сводку по складам"""
    return controllers.get_warehouse_summary(db, owner_id)
