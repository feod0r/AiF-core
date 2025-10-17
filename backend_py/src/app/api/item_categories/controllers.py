from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import ItemCategoryIn, ItemCategoryUpdate
from app.external.sqlalchemy.utils import item_categories as item_category_crud
from app.external.sqlalchemy.utils.reference_tables import item_category_type_crud
from typing import List


def get_item_category(db: Session, category_id: int):
    """Получить категорию товаров по ID"""
    category = item_category_crud.get_item_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория товаров не найдена")
    return category


def get_item_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category_type_id: int = None,
    parent_id: int = None,
    is_active: bool = None,
    search: str = None,
    include_children: bool = False
):
    """Получить список категорий товаров с фильтрацией"""
    return item_category_crud.get_item_categories(
        db, 
        skip=skip, 
        limit=limit,
        category_type_id=category_type_id,
        parent_id=parent_id,
        is_active=is_active,
        search=search,
        include_children=include_children
    )


def get_item_category_by_name(db: Session, name: str):
    """Получить категорию товаров по названию"""
    category = item_category_crud.get_item_category_by_name(db, name)
    if not category:
        raise HTTPException(status_code=404, detail=f"Категория товаров '{name}' не найдена")
    return category


def get_root_categories(db: Session):
    """Получить только корневые категории"""
    return item_category_crud.get_root_categories(db)


def get_category_children(db: Session, category_id: int):
    """Получить дочерние категории"""
    # Проверяем существование родительской категории
    parent = item_category_crud.get_item_category(db, category_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Родительская категория не найдена")
    
    return item_category_crud.get_category_children(db, category_id)


def get_category_tree(db: Session, category_id: int):
    """Получить дерево категорий"""
    # Проверяем существование корневой категории
    root = item_category_crud.get_item_category(db, category_id)
    if not root:
        raise HTTPException(status_code=404, detail="Корневая категория не найдена")
    
    return item_category_crud.get_category_tree(db, category_id)


def get_category_path(db: Session, category_id: int):
    """Получить путь к категории"""
    path = item_category_crud.get_category_path(db, category_id)
    if not path:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return path


def create_item_category(db: Session, category_in: ItemCategoryIn):
    """Создать новую категорию товаров"""
    # Валидация связей
    _validate_category_links(db, category_in)
    
    # Проверяем уникальность названия в рамках родительской категории
    if category_in.parent_id:
        existing = item_category_crud.get_item_category_by_name(db, category_in.name)
        if existing and existing.parent_id == category_in.parent_id:
            raise HTTPException(status_code=400, detail=f"Категория с названием '{category_in.name}' уже существует в данной родительской категории")
    else:
        # Для корневых категорий проверяем уникальность глобально
        existing = item_category_crud.get_item_category_by_name(db, category_in.name)
        if existing and existing.parent_id is None:
            raise HTTPException(status_code=400, detail=f"Корневая категория с названием '{category_in.name}' уже существует")
    
    try:
        return item_category_crud.create_item_category(db, category_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании категории: {str(e)}")


def update_item_category(db: Session, category_id: int, category_update: ItemCategoryUpdate):
    """Обновить категорию товаров"""
    # Проверяем существование категории
    existing_category = item_category_crud.get_item_category(db, category_id)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Категория товаров не найдена")
    
    # Валидация связей для обновляемых полей
    _validate_category_links(db, category_update, existing_category)
    
    # Проверяем, не пытаемся ли мы сделать категорию родителем самой себя
    if hasattr(category_update, 'parent_id') and category_update.parent_id == category_id:
        raise HTTPException(status_code=400, detail="Категория не может быть родителем самой себя")
    
    # Проверяем уникальность названия при обновлении
    if category_update.name:
        existing = item_category_crud.get_item_category_by_name(db, category_update.name)
        if existing and existing.id != category_id:
            parent_id = category_update.parent_id if hasattr(category_update, 'parent_id') else existing_category.parent_id
            if existing.parent_id == parent_id:
                raise HTTPException(status_code=400, detail=f"Категория с названием '{category_update.name}' уже существует в данной родительской категории")
    
    category = item_category_crud.update_item_category(db, category_id, category_update)
    if not category:
        raise HTTPException(status_code=404, detail="Категория товаров не найдена")
    return category


def delete_item_category(db: Session, category_id: int):
    """Удалить категорию товаров (мягкое удаление)"""
    success = item_category_crud.delete_item_category(db, category_id)
    if not success:
        # Проверяем, существует ли категория
        category = item_category_crud.get_item_category(db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Категория товаров не найдена")
        else:
            raise HTTPException(status_code=400, detail="Нельзя удалить категорию, у которой есть дочерние категории")
    
    return {"message": "Категория товаров успешно удалена"}


def get_categories_by_type(db: Session, category_type_id: int):
    """Получить все категории определенного типа"""
    return item_category_crud.get_categories_by_type(db, category_type_id)


def get_categories_summary(db: Session):
    """Получить сводку по категориям товаров"""
    return item_category_crud.get_categories_summary(db)


def get_category_detail(db: Session, category_id: int):
    """Получить детальную информацию о категории"""
    category = item_category_crud.get_item_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория товаров не найдена")
    
    # Получаем дополнительную информацию
    children = item_category_crud.get_category_children(db, category_id)
    path = item_category_crud.get_category_path(db, category_id)
    
    # Создаем детальный объект
    detail = {
        "id": category.id,
        "name": category.name,
        "category_type": category.category_type,
        "description": category.description,
        "parent_id": category.parent_id,
        "parent_name": path[-2].name if len(path) > 1 else None,
        "is_active": category.is_active,
        "start_date": category.start_date,
        "end_date": category.end_date,
        "children_count": len(children),
        "path": [{"id": p.id, "name": p.name, "level": i} for i, p in enumerate(path)]
    }
    
    return detail


def _validate_category_links(db: Session, category_data, existing_category=None):
    """Валидация связей категории товаров"""
    
    # Проверяем тип категории
    if hasattr(category_data, 'category_type_id') and category_data.category_type_id is not None:
        category_type = item_category_type_crud.get_by_id(db, category_data.category_type_id)
        if not category_type:
            raise HTTPException(status_code=400, detail=f"Тип категории с ID {category_data.category_type_id} не найден")
    
    # Проверяем родительскую категорию
    if hasattr(category_data, 'parent_id') and category_data.parent_id is not None:
        parent_category = item_category_crud.get_item_category(db, category_data.parent_id)
        if not parent_category:
            raise HTTPException(status_code=400, detail=f"Родительская категория с ID {category_data.parent_id} не найдена") 