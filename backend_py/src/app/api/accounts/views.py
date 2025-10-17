from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from .models import AccountIn, AccountOut, AccountUpdate, AccountSummary, AccountDetail
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List, Optional

router = APIRouter()

@router.get("/accounts", response_model=List[AccountOut])
def read_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    owner_id: Optional[int] = Query(None, description="Фильтр по ID владельца"),
    account_type_id: Optional[int] = Query(None, description="Фильтр по ID типа счета"),
    currency: Optional[str] = Query(None, description="Фильтр по валюте"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    search: Optional[str] = Query(None, description="Поиск по названию, номеру счета, банку"),
    start_date_from: Optional[str] = Query(None, description="Дата создания от в ISO формате"),
    start_date_to: Optional[str] = Query(None, description="Дата создания до в ISO формате"),
    db: Session = Depends(get_db)
):
    """Получить список счетов с фильтрацией"""
    return controllers.get_accounts(
        db, 
        skip=skip, 
        limit=limit,
        owner_id=owner_id,
        account_type_id=account_type_id,
        currency=currency,
        is_active=is_active,
        search=search,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )

@router.get("/accounts/{account_id}", response_model=AccountOut)
def read_account(
    account_id: int = Path(..., description="ID счета"),
    db: Session = Depends(get_db)
):
    """Получить счет по ID"""
    return controllers.get_account(db, account_id)

@router.get("/accounts/number/{account_number}", response_model=AccountOut)
def read_account_by_number(
    account_number: str = Path(..., description="Номер счета"),
    db: Session = Depends(get_db)
):
    """Получить счет по номеру"""
    return controllers.get_account_by_number(db, account_number)

@router.get("/accounts/{account_id}/detail", response_model=AccountDetail)
def read_account_detail(
    account_id: int = Path(..., description="ID счета"),
    db: Session = Depends(get_db)
):
    """Получить детальную информацию о счете"""
    return controllers.get_account_detail(db, account_id)

@router.get("/accounts/{account_id}/balance")
def read_account_balance(
    account_id: int = Path(..., description="ID счета"),
    db: Session = Depends(get_db)
):
    """Получить баланс счета"""
    return controllers.get_account_balance(db, account_id)

@router.post("/accounts", response_model=AccountOut)
def create_account(
    account: AccountIn,
    db: Session = Depends(get_db)
):
    """Создать новый счет"""
    return controllers.create_account(db, account)

@router.put("/accounts/{account_id}", response_model=AccountOut)
def update_account(
    account_id: int = Path(..., description="ID счета"),
    account: AccountUpdate = None,
    db: Session = Depends(get_db)
):
    """Обновить счет"""
    return controllers.update_account(db, account_id, account)

@router.delete("/accounts/{account_id}")
def delete_account(
    account_id: int = Path(..., description="ID счета"),
    db: Session = Depends(get_db)
):
    """Удалить счет (мягкое удаление)"""
    return controllers.delete_account(db, account_id)

@router.post("/accounts/{account_id}/update-balance")
def update_account_balance(
    account_id: int = Path(..., description="ID счета"),
    db: Session = Depends(get_db)
):
    """Обновить баланс счета на основе транзакций"""
    return controllers.update_account_balance(db, account_id)

@router.get("/accounts/summary", response_model=AccountSummary)
def read_accounts_summary(
    owner_id: Optional[int] = Query(None, description="ID владельца для фильтрации"),
    db: Session = Depends(get_db)
):
    """Получить сводку по счетам"""
    return controllers.get_accounts_summary(db, owner_id)

@router.post("/accounts/update-all-balances")
def update_all_accounts_balances(
    db: Session = Depends(get_db)
):
    """Обновить балансы всех счетов на основе транзакций"""
    return controllers.update_all_accounts_balances(db) 