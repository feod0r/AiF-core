from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from .models import TransactionIn, TransactionOut, TransactionUpdate, TransactionSummary
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List, Optional
from datetime import date, datetime

router = APIRouter()


@router.get("/transactions", response_model=List[TransactionOut])
def read_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    account_id: Optional[int] = Query(None, description="Фильтр по ID счета"),
    category_id: Optional[int] = Query(None, description="Фильтр по ID категории"),
    counterparty_id: Optional[int] = Query(
        None, description="Фильтр по ID контрагента"
    ),
    transaction_type_id: Optional[int] = Query(
        None, description="Фильтр по ID типа транзакций"
    ),
    machine_id: Optional[int] = Query(None, description="Фильтр по ID автомата"),
    date_from: Optional[date | datetime] = Query(None, description="Фильтр по дате с"),
    date_to: Optional[date | datetime] = Query(None, description="Фильтр по дате по"),
    is_confirmed: Optional[bool] = Query(None, description="Фильтр по подтверждению"),
    search: Optional[str] = Query(
        None, description="Поиск по описанию и номеру ссылки"
    ),
    db: Session = Depends(get_db),
):
    """Получить список транзакций с фильтрацией"""
    return controllers.get_transactions(
        db,
        skip=skip,
        limit=limit,
        account_id=account_id,
        category_id=category_id,
        counterparty_id=counterparty_id,
        transaction_type_id=transaction_type_id,
        machine_id=machine_id,
        date_from=date_from,
        date_to=date_to,
        is_confirmed=is_confirmed,
        search=search,
    )


@router.get("/transactions/summary", response_model=TransactionSummary)
def read_transaction_summary(
    account_id: Optional[int] = Query(None, description="ID счета для фильтрации"),
    date_from: Optional[date | datetime] = Query(None, description="Дата с"),
    date_to: Optional[date | datetime] = Query(None, description="Дата по"),
    db: Session = Depends(get_db),
):
    """Получить сводку по транзакциям"""
    return controllers.get_transaction_summary(db, account_id, date_from, date_to)


@router.get("/transactions/{transaction_id}", response_model=TransactionOut)
def read_transaction(
    transaction_id: int = Path(..., description="ID транзакции"),
    db: Session = Depends(get_db),
):
    """Получить транзакцию по ID"""
    return controllers.get_transaction(db, transaction_id)


@router.get("/transactions/account/{account_id}", response_model=List[TransactionOut])
def read_transactions_by_account(
    account_id: int = Path(..., description="ID счета"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить транзакции по счету"""
    return controllers.get_transactions_by_account(db, account_id, skip, limit)


@router.get("/transactions/account/{account_id}/balance")
def read_account_balance(
    account_id: int = Path(..., description="ID счета"), db: Session = Depends(get_db)
):
    """Получить баланс счета"""
    return controllers.get_account_balance(db, account_id)


@router.post("/transactions", response_model=TransactionOut)
def create_transaction(transaction: TransactionIn, db: Session = Depends(get_db)):
    """Создать новую транзакцию"""
    return controllers.create_transaction(db, transaction)


@router.put("/transactions/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int = Path(..., description="ID транзакции"),
    transaction: TransactionUpdate = None,
    db: Session = Depends(get_db),
):
    """Обновить транзакцию"""
    return controllers.update_transaction(db, transaction_id, transaction)


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int = Path(..., description="ID транзакции"),
    db: Session = Depends(get_db),
):
    """Удалить транзакцию"""
    return controllers.delete_transaction(db, transaction_id)


@router.post("/transactions/{transaction_id}/confirm", response_model=TransactionOut)
def confirm_transaction(
    transaction_id: int = Path(..., description="ID транзакции"),
    db: Session = Depends(get_db),
):
    """Подтвердить транзакцию"""
    return controllers.confirm_transaction(db, transaction_id)
