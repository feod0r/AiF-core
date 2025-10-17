from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from ..models import ItemCategory
from typing import List, Optional
from datetime import datetime


def get_item_category(db: Session, category_id: int) -> Optional[ItemCategory]:
    """Получить категорию товаров по ID"""
    from sqlalchemy.orm import joinedload
    
    return db.query(ItemCategory).options(
        joinedload(ItemCategory.parent),
        joinedload(ItemCategory.category_type)
    ).filter(ItemCategory.id == category_id, ItemCategory.is_active == True).first()


def get_item_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category_type_id: Optional[int] = None,
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    include_children: bool = False
) -> List[ItemCategory]:
    """Получить список категорий товаров с фильтрацией"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(ItemCategory).options(
        joinedload(ItemCategory.parent),
        joinedload(ItemCategory.category_type)
    )
    
    # Фильтр по активности
    if is_active is not None:
        query = query.filter(ItemCategory.is_active == is_active)
    else:
        query = query.filter(ItemCategory.is_active == True)
    
    # Фильтр по типу категории
    if category_type_id is not None:
        query = query.filter(ItemCategory.category_type_id == category_type_id)
    
    # Фильтр по родительской категории
    if parent_id is not None:
        query = query.filter(ItemCategory.parent_id == parent_id)
    elif not include_children:
        # По умолчанию показываем только корневые категории
        query = query.filter(ItemCategory.parent_id == None)
    
    # Поиск по названию и описанию
    if search:
        search_filter = or_(
            ItemCategory.name.ilike(f"%{search}%"),
            ItemCategory.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    return query.offset(skip).limit(limit).all()


def get_item_category_by_name(db: Session, name: str) -> Optional[ItemCategory]:
    """Получить категорию товаров по названию"""
    return db.query(ItemCategory).filter(
        ItemCategory.name == name, 
        ItemCategory.is_active == True
    ).first()


def get_root_categories(db: Session) -> List[ItemCategory]:
    """Получить только корневые категории (без родителей)"""
    return db.query(ItemCategory).filter(
        ItemCategory.parent_id == None, 
        ItemCategory.is_active == True
    ).all()


def get_category_children(db: Session, category_id: int) -> List[ItemCategory]:
    """Получить дочерние категории"""
    return db.query(ItemCategory).filter(
        ItemCategory.parent_id == category_id, 
        ItemCategory.is_active == True
    ).all()


def get_category_tree(db: Session, category_id: int) -> List[ItemCategory]:
    """Получить дерево категорий (рекурсивно)"""
    def get_children_recursive(parent_id):
        children = db.query(ItemCategory).filter(
            ItemCategory.parent_id == parent_id, 
            ItemCategory.is_active == True
        ).all()
        result = []
        for child in children:
            child_data = {
                'id': child.id,
                'name': child.name,
                'category_type_id': child.category_type_id,
                'description': child.description,
                'parent_id': child.parent_id,
                'children': get_children_recursive(child.id)
            }
            result.append(child_data)
        return result
    
    root_category = get_item_category(db, category_id)
    if not root_category:
        return []
    
    return get_children_recursive(category_id)


def create_item_category(db: Session, category_data) -> ItemCategory:
    """Создать новую категорию товаров"""
    db_category = ItemCategory(
        name=category_data.name,
        category_type_id=category_data.category_type_id,
        description=category_data.description,
        parent_id=category_data.parent_id if hasattr(category_data, 'parent_id') else None,
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=datetime(9999, 12, 31, 0, 0, 0)
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_item_category(db: Session, category_id: int, category_data) -> Optional[ItemCategory]:
    """Обновить категорию товаров"""
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id, ItemCategory.is_active == True).first()
    if not category:
        return None
    
    # Обновляем только переданные поля
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.category_type_id is not None:
        category.category_type_id = category_data.category_type_id
    if category_data.description is not None:
        category.description = category_data.description
    if hasattr(category_data, 'parent_id'):
        category.parent_id = category_data.parent_id
    if category_data.is_active is not None:
        category.is_active = category_data.is_active
    
    db.commit()
    db.refresh(category)
    return category


def delete_item_category(db: Session, category_id: int) -> bool:
    """Мягкое удаление категории товаров (soft delete)"""
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id, ItemCategory.is_active == True).first()
    if not category:
        return False
    
    # Проверяем, есть ли дочерние категории
    children = get_category_children(db, category_id)
    if children:
        # Если есть дочерние категории, нельзя удалить
        return False
    
    category.is_active = False
    category.end_date = datetime.utcnow()
    db.commit()
    return True


def get_categories_by_type(db: Session, category_type_id: int) -> List[ItemCategory]:
    """Получить все категории определенного типа"""
    return db.query(ItemCategory).filter(
        ItemCategory.category_type_id == category_type_id, 
        ItemCategory.is_active == True
    ).all()


def get_category_path(db: Session, category_id: int) -> List[ItemCategory]:
    """Получить путь к категории (от корня до текущей)"""
    path = []
    current_category = get_item_category(db, category_id)
    
    while current_category:
        path.insert(0, current_category)
        if current_category.parent_id:
            current_category = get_item_category(db, current_category.parent_id)
        else:
            break
    
    return path


def get_categories_summary(db: Session) -> dict:
    """Получить сводку по категориям товаров"""
    total_categories = db.query(ItemCategory).filter(ItemCategory.is_active == True).count()
    root_categories = db.query(ItemCategory).filter(
        ItemCategory.parent_id == None, 
        ItemCategory.is_active == True
    ).count()
    
    # Группировка по типам категорий
    from sqlalchemy import func
    type_counts = db.query(
        ItemCategory.category_type_id,
        func.count(ItemCategory.id).label('count')
    ).filter(ItemCategory.is_active == True).group_by(ItemCategory.category_type_id).all()
    
    return {
        "total_categories": total_categories,
        "root_categories": root_categories,
        "type_counts": {str(type_id): count for type_id, count in type_counts}
    } 