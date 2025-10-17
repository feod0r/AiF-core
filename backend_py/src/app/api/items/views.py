from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db

from .controllers import (
    create_item,
    delete_item,
    get_item,
    get_item_by_barcode,
    get_item_by_sku,
    get_item_detail,
    get_items,
    get_items_by_category,
    get_items_summary,
    get_items_with_stock_info,
    get_low_stock_items,
    update_item,
)
from .models import (
    ItemDetail,
    ItemFilter,
    ItemIn,
    ItemOut,
    ItemSummary,
    ItemUpdate,
    ItemWithStockInfo,
    LowStockItem,
)

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=List[ItemOut])
def read_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[int] = Query(None, description="ID категории"),
    is_active: Optional[bool] = Query(None, description="Активность товара"),
    has_stock: Optional[bool] = Query(None, description="Наличие остатков"),
    search: Optional[str] = Query(
        None, description="Поиск по названию, артикулу, описанию, штрихкоду"
    ),
    db: Session = Depends(get_db),
):
    """Получить список товаров с фильтрацией"""
    return get_items(
        db=db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        is_active=is_active,
        has_stock=has_stock,
        search=search,
    )


@router.get("/summary", response_model=ItemSummary)
def read_items_summary(db: Session = Depends(get_db)):
    """Получить сводку по товарам"""
    return get_items_summary(db=db)


@router.get("/{item_id}", response_model=ItemOut)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """Получить товар по ID"""
    return get_item(db=db, item_id=item_id)


@router.get("/{item_id}/detail", response_model=ItemDetail)
def read_item_detail(item_id: int, db: Session = Depends(get_db)):
    """Получить детальную информацию о товаре"""
    return get_item_detail(db=db, item_id=item_id)


@router.get("/sku/{sku}", response_model=ItemOut)
def read_item_by_sku(sku: str, db: Session = Depends(get_db)):
    """Получить товар по артикулу"""
    return get_item_by_sku(db=db, sku=sku)


@router.get("/barcode/{barcode}", response_model=ItemOut)
def read_item_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """Получить товар по штрихкоду"""
    return get_item_by_barcode(db=db, barcode=barcode)


@router.post("/", response_model=ItemOut)
def create_item_endpoint(item_in: ItemIn, db: Session = Depends(get_db)):
    """Создать новый товар"""
    return create_item(db=db, item_in=item_in)


@router.put("/{item_id}", response_model=ItemOut)
def update_item_endpoint(
    item_id: int, item_update: ItemUpdate, db: Session = Depends(get_db)
):
    """Обновить товар"""
    return update_item(db=db, item_id=item_id, item_update=item_update)


@router.delete("/{item_id}")
def delete_item_endpoint(item_id: int, db: Session = Depends(get_db)):
    """Удалить товар"""
    return delete_item(db=db, item_id=item_id)


# Специальные эндпоинты для фильтрации


@router.get("/category/{category_id}", response_model=List[ItemOut])
def read_items_by_category(category_id: int, db: Session = Depends(get_db)):
    """Получить все товары определенной категории"""
    return get_items_by_category(db=db, category_id=category_id)


@router.get("/with-stock-info", response_model=List[ItemWithStockInfo])
def read_items_with_stock_info(
    warehouse_id: Optional[int] = Query(None, description="ID склада для детализации"),
    db: Session = Depends(get_db),
):
    """Получить товары с информацией об остатках"""
    return get_items_with_stock_info(db=db, warehouse_id=warehouse_id)


@router.get("/low-stock", response_model=List[LowStockItem])
def read_low_stock_items(
    warehouse_id: Optional[int] = Query(None, description="ID склада"),
    db: Session = Depends(get_db),
):
    """Получить товары с низкими остатками"""
    return get_low_stock_items(db=db, warehouse_id=warehouse_id)


# Эндпоинты для фильтрации по статусам


@router.get("/active", response_model=List[ItemOut])
def read_active_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить активные товары"""
    return get_items(db=db, skip=skip, limit=limit, is_active=True)


@router.get("/inactive", response_model=List[ItemOut])
def read_inactive_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить неактивные товары"""
    return get_items(db=db, skip=skip, limit=limit, is_active=False)


@router.get("/with-stock", response_model=List[ItemOut])
def read_items_with_stock(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить товары с остатками"""
    return get_items(db=db, skip=skip, limit=limit, has_stock=True)


@router.get("/without-stock", response_model=List[ItemOut])
def read_items_without_stock(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить товары без остатков"""
    return get_items(db=db, skip=skip, limit=limit, has_stock=False)


# Эндпоинты для поиска


@router.get("/search/name", response_model=List[ItemOut])
def search_items_by_name(
    name: str = Query(..., description="Название товара для поиска"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Поиск товаров по названию"""
    return get_items(db=db, skip=skip, limit=limit, search=name)


@router.get("/search/sku", response_model=List[ItemOut])
def search_items_by_sku(
    sku: str = Query(..., description="Артикул для поиска"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Поиск товаров по артикулу"""
    return get_items(db=db, skip=skip, limit=limit, search=sku)


@router.get("/search/barcode", response_model=List[ItemOut])
def search_items_by_barcode(
    barcode: str = Query(..., description="Штрихкод для поиска"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Поиск товаров по штрихкоду"""
    return get_items(db=db, skip=skip, limit=limit, search=barcode)


# Эндпоинты для единиц измерения


@router.get("/units", response_model=List[str])
def read_available_units():
    """Получить список доступных единиц измерения"""
    return ["шт", "кг", "л", "м", "м²", "м³", "упак", "компл"]


# Эндпоинты для массовых операций


@router.post("/bulk/create", response_model=List[ItemOut])
def create_items_bulk(items: List[ItemIn], db: Session = Depends(get_db)):
    """Создать несколько товаров"""
    created_items = []
    for item_in in items:
        try:
            created_item = create_item(db=db, item_in=item_in)
            created_items.append(created_item)
        except HTTPException as e:
            # Пропускаем товары с ошибками и продолжаем
            continue

    if not created_items:
        raise HTTPException(
            status_code=400, detail="Не удалось создать ни одного товара"
        )

    return created_items


@router.put("/bulk/update", response_model=List[ItemOut])
def update_items_bulk(
    updates: List[dict],  # Список {item_id: int, update_data: ItemUpdate}
    db: Session = Depends(get_db),
):
    """Обновить несколько товаров"""
    updated_items = []
    for update_data in updates:
        try:
            item_id = update_data.get("item_id")
            item_update = ItemUpdate(**update_data.get("update_data", {}))
            updated_item = update_item(db=db, item_id=item_id, item_update=item_update)
            updated_items.append(updated_item)
        except (HTTPException, ValueError) as e:
            # Пропускаем товары с ошибками и продолжаем
            continue

    if not updated_items:
        raise HTTPException(
            status_code=400, detail="Не удалось обновить ни одного товара"
        )

    return updated_items


@router.delete("/bulk/delete")
def delete_items_bulk(item_ids: List[int], db: Session = Depends(get_db)):
    """Удалить несколько товаров"""
    deleted_count = 0
    for item_id in item_ids:
        try:
            result = delete_item(db=db, item_id=item_id)
            if result:
                deleted_count += 1
        except HTTPException:
            # Пропускаем товары с ошибками и продолжаем
            continue

    return {
        "message": f"Удалено товаров: {deleted_count} из {len(item_ids)}",
        "deleted_count": deleted_count,
        "total_count": len(item_ids),
    }
