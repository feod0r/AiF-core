from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from ..models import Account, Transaction
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


def get_account(db: Session, account_id: int) -> Optional[Account]:
    """Получить счет по ID"""
    return db.query(Account).filter(Account.id == account_id, Account.is_active == True).first()


def get_accounts(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    owner_id: Optional[int] = None,
    account_type_id: Optional[int] = None,
    currency: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None
) -> List[Account]:
    """Получить список счетов с фильтрацией"""
    query = db.query(Account)
    
    # Фильтр по активности
    if is_active is not None:
        query = query.filter(Account.is_active == is_active)
    else:
        query = query.filter(Account.is_active == True)
    
    # Фильтр по владельцу
    if owner_id is not None:
        query = query.filter(Account.owner_id == owner_id)
    
    # Фильтр по типу счета
    if account_type_id is not None:
        query = query.filter(Account.account_type_id == account_type_id)
    
    # Фильтр по валюте
    if currency is not None:
        query = query.filter(Account.currency == currency)
    
    # Поиск по названию, номеру счета, банку
    if search:
        search_filter = or_(
            Account.name.ilike(f"%{search}%"),
            Account.account_number.ilike(f"%{search}%"),
            Account.bank_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Фильтр по дате создания от
    if start_date_from:
        try:
            from_date = datetime.fromisoformat(start_date_from.replace('Z', '+00:00'))
            query = query.filter(Account.start_date >= from_date)
        except ValueError:
            pass
    
    # Фильтр по дате создания до
    if start_date_to:
        try:
            to_date = datetime.fromisoformat(start_date_to.replace('Z', '+00:00'))
            query = query.filter(Account.start_date <= to_date)
        except ValueError:
            pass
    
    return query.offset(skip).limit(limit).all()


def get_account_by_number(db: Session, account_number: str) -> Optional[Account]:
    """Получить счет по номеру"""
    return db.query(Account).filter(
        Account.account_number == account_number, 
        Account.is_active == True
    ).first()


def create_account(db: Session, account_data) -> Account:
    """Создать новый счет"""
    initial_balance = account_data.initial_balance if hasattr(account_data, 'initial_balance') else Decimal('0.00')
    balance = account_data.balance if hasattr(account_data, 'balance') else initial_balance
    
    db_account = Account(
        name=account_data.name,
        account_type_id=account_data.account_type_id,
        owner_id=account_data.owner_id,
        balance=balance,
        initial_balance=initial_balance,
        currency=account_data.currency if hasattr(account_data, 'currency') else 'RUB',
        account_number=account_data.account_number,
        bank_name=account_data.bank_name,
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=datetime(9999, 12, 31, 0, 0, 0)
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def update_account(db: Session, account_id: int, account_data) -> Optional[Account]:
    """Обновить счет"""
    account = db.query(Account).filter(Account.id == account_id, Account.is_active == True).first()
    if not account:
        return None
    
    # Обновляем только переданные поля
    if account_data.name is not None:
        account.name = account_data.name
    if account_data.account_type_id is not None:
        account.account_type_id = account_data.account_type_id
    if account_data.owner_id is not None:
        account.owner_id = account_data.owner_id
    if account_data.balance is not None:
        account.balance = account_data.balance
    if account_data.initial_balance is not None:
        account.initial_balance = account_data.initial_balance
    if account_data.currency is not None:
        account.currency = account_data.currency
    if account_data.account_number is not None:
        account.account_number = account_data.account_number
    if account_data.bank_name is not None:
        account.bank_name = account_data.bank_name
    if account_data.is_active is not None:
        account.is_active = account_data.is_active
    
    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account_id: int) -> bool:
    """Мягкое удаление счета (soft delete)"""
    account = db.query(Account).filter(Account.id == account_id, Account.is_active == True).first()
    if not account:
        return False
    
    account.is_active = False
    account.end_date = datetime.utcnow()
    db.commit()
    return True


def calculate_account_balance(db: Session, account_id: int) -> Decimal:
    """Рассчитать баланс счета на основе транзакций и начального баланса"""
    # Получаем начальный баланс счета
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return Decimal('0.00')
    
    initial_balance = account.initial_balance or Decimal('0.00')
    
    # Получаем сумму всех подтвержденных транзакций
    # 1. Списания с счета (где account_id = текущий счет)
    debits = db.query(
        func.sum(Transaction.amount).label('total')
    ).filter(
        and_(
            Transaction.account_id == account_id,
            Transaction.is_confirmed == True
        )
    ).scalar()
    
    # 2. Зачисления на счет (где to_account_id = текущий счет) - только для переводов
    # Для зачислений берем абсолютное значение суммы (положительное)
    credits = db.query(
        func.sum(func.abs(Transaction.amount)).label('total')
    ).filter(
        and_(
            Transaction.to_account_id == account_id,
            Transaction.transaction_type_id == 3,  # Тип "transfer"
            Transaction.is_confirmed == True
        )
    ).scalar()
    
    debits_sum = debits or Decimal('0.00')
    credits_sum = credits or Decimal('0.00')
    
    # Баланс = начальный баланс + списания + зачисления
    return initial_balance + debits_sum + credits_sum


def update_account_balance(db: Session, account_id: int) -> bool:
    """Обновить баланс счета на основе транзакций"""
    account = db.query(Account).filter(Account.id == account_id, Account.is_active == True).first()
    if not account:
        return False
    
    # Рассчитываем новый баланс
    new_balance = calculate_account_balance(db, account_id)
    account.balance = new_balance
    
    db.commit()
    return True


def get_accounts_summary(db: Session, owner_id: Optional[int] = None) -> dict:
    """Получить сводку по счетам"""
    query = db.query(Account).filter(Account.is_active == True)
    
    if owner_id is not None:
        query = query.filter(Account.owner_id == owner_id)
    
    accounts = query.all()
    
    total_balance = sum(account.balance for account in accounts)
    total_accounts = len(accounts)
    
    # Группировка по валютам
    currency_balances = {}
    for account in accounts:
        currency = account.currency
        if currency not in currency_balances:
            currency_balances[currency] = Decimal('0.00')
        currency_balances[currency] += account.balance
    
    return {
        "total_balance": float(total_balance),
        "total_accounts": total_accounts,
        "currency_balances": {curr: float(bal) for curr, bal in currency_balances.items()}
    }


def get_account_transactions_count(db: Session, account_id: int) -> int:
    """Получить количество транзакций по счету"""
    return db.query(Transaction).filter(Transaction.account_id == account_id).count()


def get_account_last_transaction(db: Session, account_id: int) -> Optional[Transaction]:
    """Получить последнюю транзакцию по счету"""
    return db.query(Transaction).filter(
        Transaction.account_id == account_id
    ).order_by(Transaction.date.desc()).first() 