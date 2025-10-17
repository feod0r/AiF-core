from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.terminal_operations.models import (
    TerminalOperationCreate,
    TerminalOperationUpdate,
)

from ..models import (
    Account,
    Terminal,
    TerminalOperation,
    Transaction,
    TransactionType,
    TransactionCategory,
)


def get_terminal_operation(
    db: Session, operation_id: int
) -> Optional[TerminalOperation]:
    """Получить операцию терминала по ID"""
    return (
        db.query(TerminalOperation).filter(TerminalOperation.id == operation_id).first()
    )


def get_terminal_operations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    operation_date: Optional[date | datetime] = None,
    terminal_id: Optional[int] = None,
    is_closed: Optional[bool] = None,
) -> List[TerminalOperation]:
    """Получить список операций терминалов с фильтрацией"""
    query = db.query(TerminalOperation)

    if operation_date is not None:
        query = query.filter(TerminalOperation.operation_date == operation_date)

    if terminal_id is not None:
        query = query.filter(TerminalOperation.terminal_id == terminal_id)

    if is_closed is not None:
        query = query.filter(TerminalOperation.is_closed == is_closed)

    return (
        query.order_by(
            TerminalOperation.operation_date.desc(), TerminalOperation.terminal_id
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_terminal_operation(
    db: Session, operation_data: TerminalOperationCreate
) -> TerminalOperation:
    """Создать операцию терминала"""
    try:
        db_operation = TerminalOperation(
            operation_date=operation_data.operation_date,
            terminal_id=operation_data.terminal_id,
            amount=operation_data.amount,
            transaction_count=operation_data.transaction_count,
            commission=operation_data.commission,
        )

        db.add(db_operation)
        db.commit()
        db.refresh(db_operation)
        return db_operation
    except Exception as e:
        # Если произошла ошибка уникального ограничения, откатываем и пробуем обновить
        if "unique constraint" in str(
            e
        ).lower() and "unique_terminal_operation_per_day" in str(e):
            db.rollback()

            # Ищем существующую операцию
            existing_operation = (
                db.query(TerminalOperation)
                .filter(
                    and_(
                        TerminalOperation.operation_date
                        == operation_data.operation_date,
                        TerminalOperation.terminal_id == operation_data.terminal_id,
                    )
                )
                .first()
            )

            if existing_operation:
                # Проверяем, что операция не закрыта
                if existing_operation.is_closed:
                    raise ValueError("Нельзя изменять закрытую операцию")

                # Обновляем существующую операцию
                existing_operation.amount = operation_data.amount
                existing_operation.transaction_count = operation_data.transaction_count
                existing_operation.commission = operation_data.commission
                existing_operation.updated_at = datetime.utcnow()

                db.commit()
                db.refresh(existing_operation)
                return existing_operation
            else:
                raise ValueError("Операция не найдена для обновления")
        else:
            # Для других ошибок просто откатываем и пробрасываем
            db.rollback()
            raise e


def update_terminal_operation(
    db: Session, operation_id: int, operation_data: TerminalOperationUpdate
) -> Optional[TerminalOperation]:
    """Обновить операцию терминала"""
    db_operation = get_terminal_operation(db, operation_id)
    if not db_operation:
        return None

    if db_operation.is_closed:
        raise ValueError("Нельзя изменять закрытую операцию")

    update_data = operation_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_operation, field, value)

    db_operation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_operation)
    return db_operation


def delete_terminal_operation(db: Session, operation_id: int) -> bool:
    """Удалить операцию терминала"""
    db_operation = get_terminal_operation(db, operation_id)
    if not db_operation:
        return False

    if db_operation.is_closed:
        raise ValueError("Нельзя удалять закрытую операцию")

    db.delete(db_operation)
    db.commit()
    return True


def close_day_operations(db: Session, operation_date: date, closed_by: int) -> dict:
    """Закрыть день - зачислить средства на расчетные счета терминалов"""
    # Получаем все незакрытые операции за указанную дату
    operations = (
        db.query(TerminalOperation)
        .filter(
            and_(
                TerminalOperation.operation_date == operation_date,
                TerminalOperation.is_closed == False,
            )
        )
        .all()
    )

    if not operations:
        return {
            "success": True,
            "message": "Нет операций для закрытия",
            "closed_operations_count": 0,
            "total_amount_processed": Decimal("0.00"),
            "affected_accounts": [],
        }

    # Группируем операции по расчетным счетам
    account_totals = {}
    for operation in operations:
        terminal = operation.terminal
        if not terminal or not terminal.account_id:
            continue

        account_id = terminal.account_id
        if account_id not in account_totals:
            account_totals[account_id] = {
                "account": terminal.account,
                "total_amount": Decimal("0.00"),
                "total_commission": Decimal("0.00"),
                "operations": [],
            }

        # Сумма к зачислению = сумма покупок - комиссия
        net_amount = operation.amount - operation.commission
        account_totals[account_id]["total_amount"] += net_amount
        account_totals[account_id]["total_commission"] += operation.commission
        account_totals[account_id]["operations"].append(operation)

    # Создаем транзакции зачисления для каждого счета
    income_transaction_type = (
        db.query(TransactionType).filter(TransactionType.name == "income").first()
    )

    if not income_transaction_type:
        raise ValueError("Тип транзакции 'income' не найден")

    # Ищем категорию для операций терминалов
    terminal_category = (
        db.query(TransactionCategory)
        .filter(TransactionCategory.name == "Терминалы")
        .first()
    )
    if not terminal_category:
        # Если нет специальной категории, берем первую доступную
        terminal_category = db.query(TransactionCategory).first()
        if not terminal_category:
            raise ValueError("Не найдено ни одной категории транзакций")

    affected_accounts = []
    total_amount_processed = Decimal("0.00")

    for account_id, account_data in account_totals.items():
        account = account_data["account"]
        net_amount = account_data["total_amount"]

        if net_amount > 0:
            # Создаем транзакцию зачисления
            transaction = Transaction(
                account_id=account_id,
                category_id=terminal_category.id,
                transaction_type_id=income_transaction_type.id,
                amount=net_amount,
                description=f"Зачисление за {operation_date} (операций терминалов: {len(account_data['operations'])})",
                date=datetime.utcnow(),
                is_confirmed=False,  # Автоматически подтверждаем
                created_by=closed_by,
            )

            db.add(transaction)
            total_amount_processed += net_amount

            affected_accounts.append(
                {
                    "account_id": account_id,
                    "account_number": account.account_number,
                    "amount": float(net_amount),
                    "commission": float(account_data["total_commission"]),
                    "operations_count": len(account_data["operations"]),
                }
            )

    # Помечаем все операции как закрытые
    for operation in operations:
        operation.is_closed = True
        operation.closed_at = datetime.utcnow()
        operation.closed_by = closed_by

    db.commit()

    return {
        "success": True,
        "message": f"Закрыто операций: {len(operations)}, обработано счетов: {len(affected_accounts)}",
        "closed_operations_count": len(operations),
        "total_amount_processed": total_amount_processed,
        "affected_accounts": affected_accounts,
    }


def get_terminal_operations_summary(
    db: Session,
    date_from: Optional[date | datetime] = None,
    date_to: Optional[date | datetime] = None,
) -> dict:
    """Получить сводку по операциям терминалов"""
    query = db.query(TerminalOperation)

    if date_from:
        query = query.filter(TerminalOperation.operation_date >= date_from)
    if date_to:
        query = query.filter(TerminalOperation.operation_date <= date_to)

    operations = query.all()

    total_operations = len(operations)
    total_amount = sum(op.amount for op in operations)
    total_commission = sum(op.commission for op in operations)
    total_transactions = sum(op.transaction_count for op in operations)
    closed_operations = len([op for op in operations if op.is_closed])
    open_operations = total_operations - closed_operations

    return {
        "total_operations": total_operations,
        "total_amount": total_amount,
        "total_commission": total_commission,
        "total_transactions": total_transactions,
        "closed_operations": closed_operations,
        "open_operations": open_operations,
    }
