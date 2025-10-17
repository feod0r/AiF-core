from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import TransactionCategoryIn, TransactionCategoryUpdate
from app.external.sqlalchemy.utils import transaction_categories as transaction_category_crud
from app.external.sqlalchemy.utils.reference_tables import transaction_type_crud
from typing import List


def get_transaction_category(db: Session, category_id: int):
    """Получить категорию транзакций по ID"""
    category = transaction_category_crud.get_transaction_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория транзакций не найдена")
    return category


def get_transaction_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    transaction_type_id: int = None,
    search: str = None,
    is_active: bool = None
):
    """Получить список категорий транзакций с фильтрацией"""
    return transaction_category_crud.get_transaction_categories(
        db, 
        skip=skip, 
        limit=limit,
        transaction_type_id=transaction_type_id,
        search=search,
        is_active=is_active
    )


def get_transaction_category_by_name(db: Session, name: str):
    """Получить категорию транзакций по имени"""
    category = transaction_category_crud.get_transaction_category_by_name(db, name)
    if not category:
        raise HTTPException(status_code=404, detail=f"Категория транзакций '{name}' не найдена")
    return category


def create_transaction_category(db: Session, category_in: TransactionCategoryIn):
    """Создать новую категорию транзакций"""
    # Проверяем существование типа транзакций
    transaction_type = transaction_type_crud.get_by_id(db, category_in.transaction_type_id)
    if not transaction_type:
        raise HTTPException(status_code=400, detail=f"Тип транзакций с ID {category_in.transaction_type_id} не найден")
    
    # Проверяем уникальность имени
    existing = transaction_category_crud.get_transaction_category_by_name(db, category_in.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Категория транзакций с названием '{category_in.name}' уже существует")
    
    try:
        return transaction_category_crud.create_transaction_category(db, category_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании категории транзакций: {str(e)}")


def update_transaction_category(db: Session, category_id: int, category_update: TransactionCategoryUpdate):
    """Обновить категорию транзакций"""
    # Проверяем существование типа транзакций, если он изменяется
    if category_update.transaction_type_id:
        transaction_type = transaction_type_crud.get_by_id(db, category_update.transaction_type_id)
        if not transaction_type:
            raise HTTPException(status_code=400, detail=f"Тип транзакций с ID {category_update.transaction_type_id} не найден")
    
    # Проверяем уникальность имени, если оно изменяется
    if category_update.name:
        existing = transaction_category_crud.get_transaction_category_by_name(db, category_update.name)
        if existing and existing.id != category_id:
            raise HTTPException(status_code=400, detail=f"Категория транзакций с названием '{category_update.name}' уже существует")
    
    category = transaction_category_crud.update_transaction_category(db, category_id, category_update)
    if not category:
        raise HTTPException(status_code=404, detail="Категория транзакций не найдена")
    return category


def delete_transaction_category(db: Session, category_id: int):
    """Удалить категорию транзакций (мягкое удаление)"""
    success = transaction_category_crud.delete_transaction_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Категория транзакций не найдена")
    return {"message": "Категория транзакций успешно удалена"} 