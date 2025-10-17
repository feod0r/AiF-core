from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db
from . import controllers
from .models import (
    TerminalOperationOut,
    TerminalOperationCreate,
    TerminalOperationUpdate,
    CloseDayRequest,
    CloseDayResponse,
    TerminalOperationSummary,
    VendistaSyncRequest,
    VendistaSyncResponse,
)

router = APIRouter(prefix="/api/terminal-operations", tags=["terminal_operations"])


@router.get("/", response_model=List[TerminalOperationOut])
def read_terminal_operations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    operation_date: Optional[date | datetime] = Query(
        None, description="Дата операции"
    ),
    terminal_id: Optional[int] = Query(None, description="ID терминала"),
    is_closed: Optional[bool] = Query(None, description="Закрыта ли операция"),
    db: Session = Depends(get_db),
):
    """Получить список операций терминалов"""
    return controllers.get_terminal_operations(
        db=db,
        skip=skip,
        limit=limit,
        operation_date=operation_date,
        terminal_id=terminal_id,
        is_closed=is_closed,
    )


@router.post("/", response_model=TerminalOperationOut)
def create_terminal_operation(
    operation_data: TerminalOperationCreate,
    db: Session = Depends(get_db),
):
    """Создать новую операцию терминала"""
    return controllers.create_terminal_operation(db=db, operation_data=operation_data)


@router.get("/{operation_id}", response_model=TerminalOperationOut)
def read_terminal_operation(
    operation_id: int,
    db: Session = Depends(get_db),
):
    """Получить операцию терминала по ID"""
    return controllers.get_terminal_operation(db=db, operation_id=operation_id)


@router.put("/{operation_id}", response_model=TerminalOperationOut)
def update_terminal_operation(
    operation_id: int,
    operation_data: TerminalOperationUpdate,
    db: Session = Depends(get_db),
):
    """Обновить операцию терминала"""
    return controllers.update_terminal_operation(
        db=db, operation_id=operation_id, operation_data=operation_data
    )


@router.delete("/{operation_id}")
def delete_terminal_operation(
    operation_id: int,
    db: Session = Depends(get_db),
):
    """Удалить операцию терминала"""
    return controllers.delete_terminal_operation(db=db, operation_id=operation_id)


@router.post("/close-day", response_model=CloseDayResponse)
def close_day_operations(
    close_data: CloseDayRequest,
    db: Session = Depends(get_db),
):
    """Закрыть день - зачислить средства на расчетные счета терминалов"""
    return controllers.close_day_operations(db=db, close_data=close_data)


@router.get("/summary/stats", response_model=TerminalOperationSummary)
def get_terminal_operations_summary(
    date_from: Optional[date | datetime] = Query(None, description="Дата с"),
    date_to: Optional[date | datetime] = Query(None, description="Дата по"),
    db: Session = Depends(get_db),
):
    """Получить сводку по операциям терминалов"""
    return controllers.get_terminal_operations_summary(
        db=db, date_from=date_from, date_to=date_to
    )


@router.post("/sync-vendista", response_model=VendistaSyncResponse)
async def sync_vendista_data(
    sync_data: VendistaSyncRequest,
    db: Session = Depends(get_db),
):
    """Синхронизировать данные из Vendista API"""
    return await controllers.sync_vendista_data(db=db, sync_data=sync_data)
