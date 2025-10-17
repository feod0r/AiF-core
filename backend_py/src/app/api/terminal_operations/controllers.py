import datetime
import json
import os
import time
from datetime import date
from typing import List, Optional

import httpx
from fastapi import HTTPException
from loguru import logger
from sqlalchemy.orm import Session
from app.external.sqlalchemy.utils import owners as owners_crud
from app.external.sqlalchemy.utils import terminal_operations as terminal_ops_crud
from app.external.sqlalchemy.utils import terminals as terminals_crud
from app.settings.generated_settings import Settings

from .models import (
    CloseDayRequest,
    CloseDayResponse,
    TerminalOperationCreate,
    TerminalOperationUpdate,
    VendistaSyncRequest,
    VendistaSyncResponse,
    VendistaTerminalInfo,
)


def get_terminal_operation(db: Session, operation_id: int):
    """Получить операцию терминала по ID"""
    operation = terminal_ops_crud.get_terminal_operation(db, operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Операция терминала не найдена")
    return operation


def get_terminal_operations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    operation_date: Optional[date | datetime.datetime] = None,
    terminal_id: Optional[int] = None,
    is_closed: Optional[bool] = None,
):
    """Получить список операций терминалов с фильтрацией"""
    return terminal_ops_crud.get_terminal_operations(
        db=db,
        skip=skip,
        limit=limit,
        operation_date=operation_date,
        terminal_id=terminal_id,
        is_closed=is_closed,
    )


def create_terminal_operation(db: Session, operation_data: TerminalOperationCreate):
    """Создать новую операцию терминала"""
    try:
        return terminal_ops_crud.create_terminal_operation(db, operation_data)
    except ValueError as e:
        # Обрабатываем ошибки валидации (например, попытка изменить закрытую операцию)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Для других ошибок возвращаем общее сообщение
        raise HTTPException(
            status_code=400, detail=f"Ошибка при создании операции: {str(e)}"
        )


def update_terminal_operation(
    db: Session, operation_id: int, operation_data: TerminalOperationUpdate
):
    """Обновить операцию терминала"""
    try:
        operation = terminal_ops_crud.update_terminal_operation(
            db, operation_id, operation_data
        )
        if not operation:
            raise HTTPException(status_code=404, detail="Операция терминала не найдена")
        return operation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка при обновлении операции: {str(e)}"
        )


def delete_terminal_operation(db: Session, operation_id: int):
    """Удалить операцию терминала"""
    try:
        success = terminal_ops_crud.delete_terminal_operation(db, operation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Операция терминала не найдена")
        return {"message": "Операция терминала успешно удалена"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def close_day_operations(db: Session, close_data: CloseDayRequest) -> CloseDayResponse:
    """Закрыть день - зачислить средства на расчетные счета"""
    try:
        result = terminal_ops_crud.close_day_operations(
            db, close_data.operation_date, close_data.closed_by
        )

        return CloseDayResponse(
            success=result["success"],
            message=result["message"],
            closed_operations_count=result["closed_operations_count"],
            total_amount_processed=result["total_amount_processed"],
            affected_accounts=result["affected_accounts"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка при закрытии дня: {str(e)}"
        )


def get_terminal_operations_summary(
    db: Session,
    date_from: Optional[date | datetime.datetime] = None,
    date_to: Optional[date | datetime.datetime] = None,
):
    """Получить сводку по операциям терминалов"""
    return terminal_ops_crud.get_terminal_operations_summary(
        db, date_from=date_from, date_to=date_to
    )


async def sync_vendista_data(
    db: Session, sync_data: VendistaSyncRequest
) -> VendistaSyncResponse:
    """Синхронизировать данные из Vendista API"""
    try:
        # Получаем настройки
        settings = Settings()

        # Получаем все активные терминалы с данными владельцев
        terminals = terminals_crud.get_active_terminals(db)

        if not terminals:
            return VendistaSyncResponse(
                success=False,
                message="Нет активных терминалов для синхронизации",
                synced_terminals=0,
                total_amount=0,
                total_transactions=0,
            )

        synced_count = 0
        total_amount = 0
        total_transactions = 0
        errors = []
        token_cache = {}

        # URL для Vendista API из настроек
        token_url = settings.vendista_token_url
        report_url = settings.vendista_report_url

        if not token_url or not report_url:
            return VendistaSyncResponse(
                success=False,
                message="Не настроены URL для Vendista API",
                synced_terminals=0,
                total_amount=0,
                total_transactions=0,
            )

        # Группируем терминалы по владельцам
        terminals_by_owner = {}
        for terminal in terminals:
            if not terminal.owner_id:
                errors.append(f"Терминал {terminal.name}: нет привязки к владельцу")
                continue

            if terminal.owner_id not in terminals_by_owner:
                terminals_by_owner[terminal.owner_id] = []
            terminals_by_owner[terminal.owner_id].append(terminal)

        # Обрабатываем каждого владельца
        for owner_id, owner_terminals in terminals_by_owner.items():
            try:
                # Получаем владельца
                owner = owners_crud.get_owner(db, owner_id)
                if not owner:
                    errors.append(f"Владелец с ID {owner_id} не найден")
                    continue

                if not owner.vendista_user or not owner.vendista_pass:
                    errors.append(
                        f"Владелец {owner.name}: нет данных для входа в Vendista"
                    )
                    continue

                # Получаем токен (кешируем по владельцу)
                if owner.id in token_cache:
                    token = token_cache[owner.id]
                else:

                    async def get_token():
                        async with httpx.AsyncClient() as client:
                            response = await client.get(
                                f"{token_url}?login={owner.vendista_user}&password={owner.vendista_pass}"
                            )
                            if response.status_code != 200:
                                raise Exception(
                                    f"Ошибка получения токена: {response.text}"
                                )
                            return response.json()

                    try:
                        token_data = await get_token()
                        token = token_data.get("token")
                        if not token:
                            raise Exception("Токен не получен")
                        token_cache[owner.id] = token
                    except Exception as e:
                        errors.append(
                            f"Владелец {owner.name}: ошибка получения токена - {str(e)}"
                        )
                        continue

                # Получаем данные отчета для всех терминалов владельца (без указания TermId)
                async def get_report():
                    async with httpx.AsyncClient() as client:
                        req = f"{report_url}?DateFrom={sync_data.sync_date}&DateTo={sync_data.sync_date + datetime.timedelta(days=1)}&OrderByColumn=0&OrderDesc=false&token={token}"

                        response = await client.get(req)

                        if response.status_code != 200:
                            raise Exception(f"Ошибка получения отчета: {response.text}")
                        return response.json()

                try:
                    report_data = await get_report()
                    items = report_data.get("items", [])

                    # Создаем словарь для быстрого поиска терминалов по Vendista ID
                    terminal_map = {
                        str(terminal.terminal): terminal
                        for terminal in owner_terminals
                        if terminal.terminal
                    }

                    # Обрабатываем каждый терминал из ответа API
                    for item in items:
                        terminal_id_vendista = str(item.get("terminal_id"))
                        tid = item.get("tid")

                        # Ищем соответствующий терминал в нашей базе
                        terminal = terminal_map.get(terminal_id_vendista)
                        if not terminal:
                            # Попробуем найти по TID
                            terminal = next(
                                (
                                    t
                                    for t in owner_terminals
                                    if t.terminal and str(t.terminal) == tid
                                ),
                                None,
                            )

                        if not terminal:
                            logger.warning(
                                f"Терминал с Vendista ID {terminal_id_vendista} (TID: {tid}) не найден в базе"
                            )
                            continue

                        incoming_amount = item.get("incoming_amount", 0) / 100
                        incoming_count = item.get("incoming_count", 0)
                        comission = float(
                            item.get("comission", incoming_count * 350) / 100
                        )

                        # Создаем или обновляем операцию терминала
                        operation_data = TerminalOperationCreate(
                            operation_date=sync_data.sync_date,
                            terminal_id=terminal.id,
                            amount=incoming_amount,
                            transaction_count=incoming_count,
                            commission=comission,
                        )

                        try:
                            # Пытаемся создать новую операцию (или обновить существующую)
                            terminal_ops_crud.create_terminal_operation(
                                db, operation_data
                            )

                            synced_count += 1
                            total_amount += incoming_amount
                            total_transactions += incoming_count

                            logger.info(
                                f"Синхронизирован терминал {terminal.name}: сумма={incoming_amount}, транзакций={incoming_count}"
                            )
                        except ValueError as e:
                            # Обрабатываем ошибки валидации (например, попытка изменить закрытую операцию)
                            errors.append(f"Терминал {terminal.name}: {str(e)}")
                        except Exception as e:
                            # Для других ошибок логируем и продолжаем
                            errors.append(
                                f"Терминал {terminal.name}: ошибка синхронизации - {str(e)}"
                            )

                    # Создаем записи с нулевыми значениями для терминалов, которых нет в ответе API
                    synced_terminal_ids = {item.get("terminal_id") for item in items}
                    for terminal in owner_terminals:
                        if (
                            terminal.terminal
                            and terminal.terminal not in synced_terminal_ids
                        ):
                            # Создаем запись с нулевыми значениями
                            operation_data = TerminalOperationCreate(
                                operation_date=sync_data.sync_date,
                                terminal_id=terminal.id,
                                amount=0,
                                transaction_count=0,
                                commission=0,
                            )

                            try:
                                terminal_ops_crud.create_terminal_operation(
                                    db, operation_data
                                )

                                synced_count += 1
                                logger.info(
                                    f"Создана пустая запись для терминала {terminal.name}"
                                )
                            except ValueError as e:
                                errors.append(f"Терминал {terminal.name}: {str(e)}")
                            except Exception as e:
                                errors.append(
                                    f"Терминал {terminal.name}: ошибка синхронизации - {str(e)}"
                                )

                except Exception as e:
                    errors.append(
                        f"Владелец {owner.name}: ошибка получения данных - {str(e)}"
                    )
                    continue

                # Небольшая задержка между запросами к разным владельцам
                time.sleep(0.5)

            except Exception as e:
                errors.append(
                    f"Владелец {owner.name if 'owner' in locals() else f'ID {owner_id}'}: общая ошибка - {str(e)}"
                )
                continue

        db.commit()

        message = f"Синхронизировано {synced_count} терминалов"
        if errors:
            message += f". Ошибки: {len(errors)}"

        return VendistaSyncResponse(
            success=True,
            message=message,
            synced_terminals=synced_count,
            total_amount=total_amount,
            total_transactions=total_transactions,
            errors=errors,
        )

    except Exception as e:
        logger.exception("Ошибка во время синхронизации Vendista")
        db.rollback()
        return VendistaSyncResponse(
            success=False,
            message=f"Ошибка синхронизации: {str(e)}",
            synced_terminals=0,
            total_amount=0,
            total_transactions=0,
            errors=[str(e)],
        )
