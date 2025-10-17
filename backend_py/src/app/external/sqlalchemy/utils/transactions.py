from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from ..models import Transaction, Account
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from .accounts import update_account_balance as _update_account_balance


def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    """Получить транзакцию по ID"""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    counterparty_id: Optional[int] = None,
    transaction_type_id: Optional[int] = None,
    machine_id: Optional[int] = None,
    date_from: Optional[date | datetime] = None,
    date_to: Optional[date | datetime] = None,
    is_confirmed: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[Transaction]:
    """Получить список транзакций с фильтрацией"""
    query = db.query(Transaction)

    # Фильтры
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)

    if counterparty_id is not None:
        query = query.filter(Transaction.counterparty_id == counterparty_id)

    if transaction_type_id is not None:
        query = query.filter(Transaction.transaction_type_id == transaction_type_id)

    if machine_id is not None:
        query = query.filter(Transaction.machine_id == machine_id)

    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)

    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)

    if is_confirmed is not None:
        query = query.filter(Transaction.is_confirmed == is_confirmed)

    # Поиск по описанию и номеру ссылки
    if search:
        search_filter = or_(
            Transaction.description.ilike(f"%{search}%"),
            Transaction.reference_number.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()


def get_transactions_by_account(
    db: Session, account_id: int, skip: int = 0, limit: int = 100
) -> List[Transaction]:
    """Получить транзакции по счету"""
    return (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .order_by(Transaction.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_account_balance(db: Session, account_id: int) -> Decimal:
    """Получить текущий баланс счета"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return Decimal("0.00")

    # Рассчитываем баланс на основе подтвержденных транзакций
    confirmed_transactions = (
        db.query(func.sum(Transaction.amount).label("total"))
        .filter(
            and_(Transaction.account_id == account_id, Transaction.is_confirmed == True)
        )
        .scalar()
    )

    return confirmed_transactions or Decimal("0.00")


def create_transaction(db: Session, transaction_data) -> Transaction:
    """Создать новую транзакцию"""
    db_transaction = Transaction(
        date=transaction_data.date or datetime.utcnow(),
        account_id=transaction_data.account_id,
        to_account_id=transaction_data.to_account_id
        if hasattr(transaction_data, "to_account_id")
        else None,
        category_id=transaction_data.category_id,
        counterparty_id=transaction_data.counterparty_id,
        amount=transaction_data.amount,
        transaction_type_id=transaction_data.transaction_type_id,
        description=transaction_data.description,
        machine_id=transaction_data.machine_id,
        rent_location_id=transaction_data.rent_location_id,
        reference_number=transaction_data.reference_number,
        is_confirmed=transaction_data.is_confirmed
        if hasattr(transaction_data, "is_confirmed")
        else False,
        created_by=transaction_data.created_by
        if hasattr(transaction_data, "created_by")
        else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    # Обновляем баланс только если транзакция подтверждена
    if db_transaction.is_confirmed:
        if db_transaction.account_id:
            _update_account_balance(db, db_transaction.account_id)
        if db_transaction.to_account_id:
            _update_account_balance(db, db_transaction.to_account_id)
    return db_transaction


def update_transaction(
    db: Session, transaction_id: int, transaction_data
) -> Optional[Transaction]:
    """Обновить транзакцию"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        return None

    # Сохраняем старые значения для пересчета баланса
    old_amount = transaction.amount
    old_is_confirmed = transaction.is_confirmed
    old_account_id = transaction.account_id
    old_to_account_id = transaction.to_account_id

    # Обновляем поля
    if transaction_data.date is not None:
        transaction.date = transaction_data.date
    if transaction_data.account_id is not None:
        transaction.account_id = transaction_data.account_id
    if transaction_data.to_account_id is not None:
        transaction.to_account_id = transaction_data.to_account_id
    if transaction_data.category_id is not None:
        transaction.category_id = transaction_data.category_id
    if transaction_data.counterparty_id is not None:
        transaction.counterparty_id = transaction_data.counterparty_id
    if transaction_data.amount is not None:
        transaction.amount = transaction_data.amount
    if transaction_data.transaction_type_id is not None:
        transaction.transaction_type_id = transaction_data.transaction_type_id
    if transaction_data.description is not None:
        transaction.description = transaction_data.description
    if transaction_data.machine_id is not None:
        transaction.machine_id = transaction_data.machine_id
    if transaction_data.rent_location_id is not None:
        transaction.rent_location_id = transaction_data.rent_location_id
    if transaction_data.reference_number is not None:
        transaction.reference_number = transaction_data.reference_number
    if (
        hasattr(transaction_data, "is_confirmed")
        and transaction_data.is_confirmed is not None
    ):
        transaction.is_confirmed = transaction_data.is_confirmed

    transaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(transaction)
    # Пересчитываем балансы затронутых счетов (старого и нового)
    if old_account_id:
        _update_account_balance(db, old_account_id)
    if transaction.account_id:
        _update_account_balance(db, transaction.account_id)
    if old_to_account_id:
        _update_account_balance(db, old_to_account_id)
    if transaction.to_account_id:
        _update_account_balance(db, transaction.to_account_id)
    return transaction


def delete_transaction(db: Session, transaction_id: int) -> bool:
    """Удалить транзакцию"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        return False
    # Сохраняем счета для пересчета
    account_id = transaction.account_id
    to_account_id = transaction.to_account_id
    db.delete(transaction)
    db.commit()
    if account_id:
        _update_account_balance(db, account_id)
    if to_account_id:
        _update_account_balance(db, to_account_id)
    return True


def confirm_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    """Подтвердить транзакцию"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        return None

    if transaction.is_confirmed:
        return transaction  # Уже подтверждена

    transaction.is_confirmed = True
    transaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(transaction)
    if transaction.account_id:
        _update_account_balance(db, transaction.account_id)
    if transaction.to_account_id:
        _update_account_balance(db, transaction.to_account_id)
    return transaction


def get_transaction_summary(
    db: Session,
    account_id: Optional[int] = None,
    date_from: Optional[date | datetime] = None,
    date_to: Optional[date | datetime] = None,
) -> dict:
    """Получить сводку по транзакциям"""
    query = db.query(Transaction)

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)

    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)

    # Только подтвержденные транзакции
    query = query.filter(Transaction.is_confirmed == True)

    # Исключаем переводы из сводки
    query = query.filter(Transaction.transaction_type_id != 3)  # ID типа "transfer"

    # Суммы по типам транзакций
    income = query.filter(Transaction.amount > 0).with_entities(
        func.sum(Transaction.amount)
    ).scalar() or Decimal("0.00")

    expense = query.filter(Transaction.amount < 0).with_entities(
        func.sum(Transaction.amount)
    ).scalar() or Decimal("0.00")

    total_transactions = query.count()

    return {
        "income": float(income),
        "expense": float(expense),
        "net": float(income + expense),
        "total_transactions": total_transactions,
    }
