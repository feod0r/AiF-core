from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import AccountIn, AccountUpdate
from app.external.sqlalchemy.utils import accounts as account_crud
from app.external.sqlalchemy.utils.reference_tables import account_type_crud
from app.external.sqlalchemy.utils.owners import get_owner
from typing import List


def get_account(db: Session, account_id: int):
    """Получить счет по ID"""
    account = account_crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return account


def get_accounts(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    owner_id: int = None,
    account_type_id: int = None,
    currency: str = None,
    is_active: bool = None,
    search: str = None,
    start_date_from: str = None,
    start_date_to: str = None
):
    """Получить список счетов с фильтрацией"""
    return account_crud.get_accounts(
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


def get_account_by_number(db: Session, account_number: str):
    """Получить счет по номеру"""
    account = account_crud.get_account_by_number(db, account_number)
    if not account:
        raise HTTPException(status_code=404, detail=f"Счет с номером {account_number} не найден")
    return account


def create_account(db: Session, account_in: AccountIn):
    """Создать новый счет"""
    # Валидация связей
    _validate_account_links(db, account_in)
    
    # Проверяем уникальность номера счета, если он указан
    if account_in.account_number:
        existing = account_crud.get_account_by_number(db, account_in.account_number)
        if existing:
            raise HTTPException(status_code=400, detail=f"Счет с номером {account_in.account_number} уже существует")
    
    try:
        return account_crud.create_account(db, account_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании счета: {str(e)}")


def update_account(db: Session, account_id: int, account_update: AccountUpdate):
    """Обновить счет"""
    # Проверяем существование счета
    existing_account = account_crud.get_account(db, account_id)
    if not existing_account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    
    # Валидация связей для обновляемых полей
    _validate_account_links(db, account_update, existing_account)
    
    # Проверяем уникальность номера счета, если он изменяется
    if account_update.account_number:
        existing = account_crud.get_account_by_number(db, account_update.account_number)
        if existing and existing.id != account_id:
            raise HTTPException(status_code=400, detail=f"Счет с номером {account_update.account_number} уже существует")
    
    account = account_crud.update_account(db, account_id, account_update)
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return account


def delete_account(db: Session, account_id: int):
    """Удалить счет (мягкое удаление)"""
    success = account_crud.delete_account(db, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return {"message": "Счет успешно удален"}


def update_account_balance(db: Session, account_id: int):
    """Обновить баланс счета на основе транзакций"""
    success = account_crud.update_account_balance(db, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Счет не найден")
    
    # Получаем обновленный счет
    account = account_crud.get_account(db, account_id)
    return {"message": "Баланс счета обновлен", "balance": float(account.balance)}


def get_account_balance(db: Session, account_id: int):
    """Получить баланс счета"""
    balance = account_crud.calculate_account_balance(db, account_id)
    return {"balance": float(balance)}


def get_accounts_summary(db: Session, owner_id: int = None):
    """Получить сводку по счетам"""
    return account_crud.get_accounts_summary(db, owner_id)


def update_all_accounts_balances(db: Session):
    """Обновить балансы всех счетов на основе транзакций"""
    try:
        # Получаем все активные счета
        accounts = account_crud.get_accounts(db, skip=0, limit=10000, is_active=True)
        updated_count = 0
        
        for account in accounts:
            success = account_crud.update_account_balance(db, account.id)
            if success:
                updated_count += 1
        
        return {
            "message": f"Обновлены балансы {updated_count} счетов",
            "updated_count": updated_count,
            "total_accounts": len(accounts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении балансов: {str(e)}")


def get_account_detail(db: Session, account_id: int):
    """Получить детальную информацию о счете"""
    account = account_crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    
    # Получаем дополнительную информацию
    transactions_count = account_crud.get_account_transactions_count(db, account_id)
    last_transaction = account_crud.get_account_last_transaction(db, account_id)
    
    # Создаем детальный объект
    detail = {
        "id": account.id,
        "name": account.name,
        "account_type": account.account_type,
        "owner": account.owner,
        "balance": account.balance,
        "initial_balance": account.initial_balance,
        "currency": account.currency,
        "account_number": account.account_number,
        "bank_name": account.bank_name,
        "is_active": account.is_active,
        "start_date": account.start_date,
        "end_date": account.end_date,
        "transactions_count": transactions_count,
        "last_transaction_date": last_transaction.date if last_transaction else None
    }
    
    return detail


def _validate_account_links(db: Session, account_data, existing_account=None):
    """Валидация связей счета"""
    
    # Проверяем тип счета
    if hasattr(account_data, 'account_type_id') and account_data.account_type_id is not None:
        account_type = account_type_crud.get_by_id(db, account_data.account_type_id)
        if not account_type:
            raise HTTPException(status_code=400, detail=f"Тип счета с ID {account_data.account_type_id} не найден")
    
    # Проверяем владельца
    if hasattr(account_data, 'owner_id') and account_data.owner_id is not None:
        try:
            get_owner(db, account_data.owner_id)
        except HTTPException:
            raise HTTPException(status_code=400, detail=f"Владелец с ID {account_data.owner_id} не найден") 