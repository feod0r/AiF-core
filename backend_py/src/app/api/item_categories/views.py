from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from .models import ItemCategoryIn, ItemCategoryOut, ItemCategoryUpdate, ItemCategorySummary, ItemCategoryDetail, ItemCategoryTree, ItemCategoryPath
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List, Optional

router = APIRouter()

@router.get("/item-categories", response_model=List[ItemCategoryOut])
def read_item_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_type_id: Optional[int] = Query(None, description="Фильтр по ID типа категории"),
    parent_id: Optional[int] = Query(None, description="Фильтр по ID родительской категории"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    search: Optional[str] = Query(None, description="Поиск по названию и описанию"),
    include_children: bool = Query(False, description="Включить дочерние категории"),
    db: Session = Depends(get_db)
):
    """Получить список категорий товаров с фильтрацией"""
    return controllers.get_item_categories(
        db, 
        skip=skip, 
        limit=limit,
        category_type_id=category_type_id,
        parent_id=parent_id,
        is_active=is_active,
        search=search,
        include_children=include_children
    )

@router.get("/item-categories/summary", response_model=ItemCategorySummary)
def read_categories_summary(
    db: Session = Depends(get_db)
):
    """Получить сводку по категориям товаров"""
    return controllers.get_categories_summary(db)

@router.get("/item-categories/{category_id}", response_model=ItemCategoryOut)
def read_item_category(
    category_id: int = Path(..., description="ID категории товаров"),
    db: Session = Depends(get_db)
):
    """Получить категорию товаров по ID"""
    return controllers.get_item_category(db, category_id)

@router.get("/item-categories/name/{name}", response_model=ItemCategoryOut)
def read_item_category_by_name(
    name: str = Path(..., description="Название категории товаров"),
    db: Session = Depends(get_db)
):
    """Получить категорию товаров по названию"""
    return controllers.get_item_category_by_name(db, name)

@router.get("/item-categories/{category_id}/detail", response_model=ItemCategoryDetail)
def read_item_category_detail(
    category_id: int = Path(..., description="ID категории товаров"),
    db: Session = Depends(get_db)
):
    """Получить детальную информацию о категории товаров"""
    return controllers.get_category_detail(db, category_id)

@router.get("/item-categories/root", response_model=List[ItemCategoryOut])
def read_root_categories(
    db: Session = Depends(get_db)
):
    """Получить только корневые категории"""
    return controllers.get_root_categories(db)

@router.get("/item-categories/{category_id}/children", response_model=List[ItemCategoryOut])
def read_category_children(
    category_id: int = Path(..., description="ID родительской категории"),
    db: Session = Depends(get_db)
):
    """Получить дочерние категории"""
    return controllers.get_category_children(db, category_id)

@router.get("/item-categories/{category_id}/tree", response_model=List[ItemCategoryTree])
def read_category_tree(
    category_id: int = Path(..., description="ID корневой категории"),
    db: Session = Depends(get_db)
):
    """Получить дерево категорий"""
    return controllers.get_category_tree(db, category_id)

@router.get("/item-categories/{category_id}/path", response_model=List[ItemCategoryPath])
def read_category_path(
    category_id: int = Path(..., description="ID категории"),
    db: Session = Depends(get_db)
):
    """Получить путь к категории"""
    return controllers.get_category_path(db, category_id)

@router.get("/item-categories/type/{category_type_id}", response_model=List[ItemCategoryOut])
def read_categories_by_type(
    category_type_id: int = Path(..., description="ID типа категории"),
    db: Session = Depends(get_db)
):
    """Получить все категории определенного типа"""
    return controllers.get_categories_by_type(db, category_type_id)

@router.post("/item-categories", response_model=ItemCategoryOut)
def create_item_category(
    category: ItemCategoryIn,
    db: Session = Depends(get_db)
):
    """Создать новую категорию товаров"""
    return controllers.create_item_category(db, category)

@router.put("/item-categories/{category_id}", response_model=ItemCategoryOut)
def update_item_category(
    category_id: int = Path(..., description="ID категории товаров"),
    category: ItemCategoryUpdate = None,
    db: Session = Depends(get_db)
):
    """Обновить категорию товаров"""
    return controllers.update_item_category(db, category_id, category)

@router.delete("/item-categories/{category_id}")
def delete_item_category(
    category_id: int = Path(..., description="ID категории товаров"),
    db: Session = Depends(get_db)
):
    """Удалить категорию товаров (мягкое удаление)"""
    return controllers.delete_item_category(db, category_id) 