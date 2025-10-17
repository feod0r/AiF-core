from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from .models import TransactionCategoryIn, TransactionCategoryOut, TransactionCategoryUpdate
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List, Optional

router = APIRouter()

@router.get("/transaction-categories", response_model=List[TransactionCategoryOut])
def read_transaction_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transaction_type_id: Optional[int] = Query(None, description="Фильтр по ID типа транзакций"),
    search: Optional[str] = Query(None, description="Поиск по названию и описанию"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    db: Session = Depends(get_db)
):
    """Получить список категорий транзакций с фильтрацией"""
    return controllers.get_transaction_categories(
        db, 
        skip=skip, 
        limit=limit,
        transaction_type_id=transaction_type_id,
        search=search,
        is_active=is_active
    )

@router.get("/transaction-categories/{category_id}", response_model=TransactionCategoryOut)
def read_transaction_category(
    category_id: int = Path(..., description="ID категории транзакций"),
    db: Session = Depends(get_db)
):
    """Получить категорию транзакций по ID"""
    return controllers.get_transaction_category(db, category_id)

@router.get("/transaction-categories/name/{name}", response_model=TransactionCategoryOut)
def read_transaction_category_by_name(
    name: str = Path(..., description="Название категории транзакций"),
    db: Session = Depends(get_db)
):
    """Получить категорию транзакций по имени"""
    return controllers.get_transaction_category_by_name(db, name)

@router.post("/transaction-categories", response_model=TransactionCategoryOut)
def create_transaction_category(
    category: TransactionCategoryIn,
    db: Session = Depends(get_db)
):
    """Создать новую категорию транзакций"""
    return controllers.create_transaction_category(db, category)

@router.put("/transaction-categories/{category_id}", response_model=TransactionCategoryOut)
def update_transaction_category(
    category_id: int = Path(..., description="ID категории транзакций"),
    category: TransactionCategoryUpdate = None,
    db: Session = Depends(get_db)
):
    """Обновить категорию транзакций"""
    return controllers.update_transaction_category(db, category_id, category)

@router.delete("/transaction-categories/{category_id}")
def delete_transaction_category(
    category_id: int = Path(..., description="ID категории транзакций"),
    db: Session = Depends(get_db)
):
    """Удалить категорию транзакций (мягкое удаление)"""
    return controllers.delete_transaction_category(db, category_id) 