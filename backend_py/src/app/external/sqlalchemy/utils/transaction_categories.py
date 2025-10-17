from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..models import TransactionCategory
from typing import List, Optional
from datetime import datetime


def get_transaction_category(db: Session, category_id: int) -> Optional[TransactionCategory]:
    """Получить категорию транзакций по ID"""
    return db.query(TransactionCategory).filter(
        TransactionCategory.id == category_id, 
        TransactionCategory.is_active == True
    ).first()


def get_transaction_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    transaction_type_id: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[TransactionCategory]:
    """Получить список категорий транзакций с фильтрацией"""
    query = db.query(TransactionCategory)
    
    # Фильтр по активности
    if is_active is not None:
        query = query.filter(TransactionCategory.is_active == is_active)
    else:
        query = query.filter(TransactionCategory.is_active == True)
    
    # Фильтр по типу транзакций
    if transaction_type_id is not None:
        query = query.filter(TransactionCategory.transaction_type_id == transaction_type_id)
    
    # Поиск по названию и описанию
    if search:
        search_filter = or_(
            TransactionCategory.name.ilike(f"%{search}%"),
            TransactionCategory.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    return query.offset(skip).limit(limit).all()


def get_transaction_category_by_name(db: Session, name: str) -> Optional[TransactionCategory]:
    """Получить категорию транзакций по имени"""
    return db.query(TransactionCategory).filter(
        TransactionCategory.name == name, 
        TransactionCategory.is_active == True
    ).first()


def create_transaction_category(db: Session, category_data) -> TransactionCategory:
    """Создать новую категорию транзакций"""
    db_category = TransactionCategory(
        name=category_data.name,
        transaction_type_id=category_data.transaction_type_id,
        description=category_data.description,
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=datetime(9999, 12, 31, 0, 0, 0)
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_transaction_category(db: Session, category_id: int, category_data) -> Optional[TransactionCategory]:
    """Обновить категорию транзакций"""
    category = db.query(TransactionCategory).filter(
        TransactionCategory.id == category_id, 
        TransactionCategory.is_active == True
    ).first()
    
    if not category:
        return None
    
    # Обновляем только переданные поля
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.transaction_type_id is not None:
        category.transaction_type_id = category_data.transaction_type_id
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.is_active is not None:
        category.is_active = category_data.is_active
    
    db.commit()
    db.refresh(category)
    return category


def delete_transaction_category(db: Session, category_id: int) -> bool:
    """Мягкое удаление категории транзакций (soft delete)"""
    category = db.query(TransactionCategory).filter(
        TransactionCategory.id == category_id, 
        TransactionCategory.is_active == True
    ).first()
    
    if not category:
        return False
    
    category.is_active = False
    category.end_date = datetime.utcnow()
    db.commit()
    return True 