from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import TransactionIn, TransactionUpdate, TransactionFilter
from app.external.sqlalchemy.utils import transactions as transaction_crud
from app.external.sqlalchemy.utils.reference_tables import (
    account_type_crud,
    transaction_type_crud,
)
from app.external.sqlalchemy.utils.transaction_categories import (
    get_transaction_category,
)
from app.external.sqlalchemy.utils.counterparties import get_counterparty
from app.external.sqlalchemy.utils.machines import get_machine
from app.external.sqlalchemy.utils.rent import get_rent
from app.external.sqlalchemy.utils.users import get_user_by_id
from typing import List
from datetime import date, datetime


def get_transaction(db: Session, transaction_id: int):
    """Получить транзакцию по ID"""
    transaction = transaction_crud.get_transaction(db, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    return transaction


def get_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    account_id: int = None,
    category_id: int = None,
    counterparty_id: int = None,
    transaction_type_id: int = None,
    machine_id: int = None,
    date_from: date = None,
    date_to: date = None,
    is_confirmed: bool = None,
    search: str = None,
):
    """Получить список транзакций с фильтрацией"""
    return transaction_crud.get_transactions(
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


def get_transactions_by_account(
    db: Session, account_id: int, skip: int = 0, limit: int = 100
):
    """Получить транзакции по счету"""
    return transaction_crud.get_transactions_by_account(db, account_id, skip, limit)


def get_account_balance(db: Session, account_id: int):
    """Получить баланс счета"""
    balance = transaction_crud.get_account_balance(db, account_id)
    return {"balance": float(balance)}


def create_transaction(db: Session, transaction_in: TransactionIn):
    """Создать новую транзакцию"""
    # Валидация связей
    _validate_transaction_links(db, transaction_in)

    try:
        return transaction_crud.create_transaction(db, transaction_in)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка при создании транзакции: {str(e)}"
        )


def update_transaction(
    db: Session, transaction_id: int, transaction_update: TransactionUpdate
):
    """Обновить транзакцию"""
    # Проверяем существование транзакции
    existing_transaction = transaction_crud.get_transaction(db, transaction_id)
    if not existing_transaction:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    # Валидация связей для обновляемых полей
    _validate_transaction_links(db, transaction_update, existing_transaction)

    transaction = transaction_crud.update_transaction(
        db, transaction_id, transaction_update
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    return transaction


def delete_transaction(db: Session, transaction_id: int):
    """Удалить транзакцию"""
    success = transaction_crud.delete_transaction(db, transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    return {"message": "Транзакция успешно удалена"}


def confirm_transaction(db: Session, transaction_id: int):
    """Подтвердить транзакцию"""
    transaction = transaction_crud.confirm_transaction(db, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    return transaction


def get_transaction_summary(
    db: Session,
    account_id: int = None,
    date_from: date | datetime = None,
    date_to: date | datetime = None,
):
    """Получить сводку по транзакциям"""
    return transaction_crud.get_transaction_summary(db, account_id, date_from, date_to)


def _validate_transaction_links(
    db: Session, transaction_data, existing_transaction=None
):
    """Валидация связей транзакции"""

    # Проверяем счет
    if (
        hasattr(transaction_data, "account_id")
        and transaction_data.account_id is not None
    ):
        # Здесь нужно будет добавить проверку существования счета
        # когда создадим API для счетов
        pass

    # Проверяем категорию транзакций
    if (
        hasattr(transaction_data, "category_id")
        and transaction_data.category_id is not None
    ):
        try:
            get_transaction_category(db, transaction_data.category_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Категория транзакций с ID {transaction_data.category_id} не найдена",
            )

    # Проверяем контрагента
    if (
        hasattr(transaction_data, "counterparty_id")
        and transaction_data.counterparty_id is not None
    ):
        try:
            get_counterparty(db, transaction_data.counterparty_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Контрагент с ID {transaction_data.counterparty_id} не найден",
            )

    # Проверяем тип транзакций
    if (
        hasattr(transaction_data, "transaction_type_id")
        and transaction_data.transaction_type_id is not None
    ):
        transaction_type = transaction_type_crud.get_by_id(
            db, transaction_data.transaction_type_id
        )
        if not transaction_type:
            raise HTTPException(
                status_code=400,
                detail=f"Тип транзакций с ID {transaction_data.transaction_type_id} не найден",
            )

    # Проверяем автомат
    if (
        hasattr(transaction_data, "machine_id")
        and transaction_data.machine_id is not None
    ):
        try:
            get_machine(db, transaction_data.machine_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Автомат с ID {transaction_data.machine_id} не найден",
            )

    # Проверяем аренду
    if (
        hasattr(transaction_data, "rent_location_id")
        and transaction_data.rent_location_id is not None
    ):
        try:
            get_rent(db, transaction_data.rent_location_id)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Аренда с ID {transaction_data.rent_location_id} не найдена",
            )

    # Проверяем пользователя
    if (
        hasattr(transaction_data, "created_by")
        and transaction_data.created_by is not None
    ):
        try:
            get_user(db, transaction_data.created_by)
        except HTTPException:
            raise HTTPException(
                status_code=400,
                detail=f"Пользователь с ID {transaction_data.created_by} не найден",
            )
