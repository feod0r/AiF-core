from typing import List, Optional, Union
from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.orm import Session

from app.api.audit.models import (
    AuditLogOut,
    AuditLogCreate,
    AuditLogFilter,
    AuditLogsList,
    AuditStatistics,
    AuditResponse,
    CleanupResult
)
from app.api.audit import controllers
from app.external.sqlalchemy.session import get_db
from app.api.auth.middleware_dependencies import require_admin, get_current_user

router = APIRouter()


def parse_optional_int(value: Union[str, int, None]) -> Optional[int]:
    """Парсинг опционального integer из query параметра"""
    if value is None or value == "" or value == "null" or value == "undefined":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_optional_str(value: Union[str, None]) -> Optional[str]:
    """Парсинг опционального string из query параметра"""
    if value is None or value == "" or value == "null" or value == "undefined":
        return None
    return value


@router.post("/audit/logs", response_model=AuditLogOut, tags=["audit"])
def create_audit_log(
    request: Request,
    audit_data: AuditLogCreate,
    db: Session = Depends(get_db)
):
    """Создать новую запись аудит-лога"""
    require_admin(request)  # Только админы могут создавать логи вручную
    
    return controllers.create_audit_log_entry(db, audit_data)


@router.get("/audit/logs", response_model=AuditLogsList, tags=["audit"])
def get_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(50, ge=1, le=1000, description="Количество записей"),
    user_id: Optional[str] = Query(None, description="ID пользователя"),
    action: Optional[str] = Query(None, description="Действие"),
    table_name: Optional[str] = Query(None, description="Название таблицы"),
    date_from: Optional[str] = Query(None, description="Дата от (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Дата до (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Поиск по IP, User-Agent"),
    order_by: str = Query("created_at", description="Поле сортировки"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$", description="Направление"),
    db: Session = Depends(get_db)
):
    """Получить список аудит-логов с фильтрацией"""
    require_admin(request)  # Только админы могут просматривать аудит
    
    filters = AuditLogFilter(
        page=page,
        limit=limit,
        user_id=parse_optional_int(user_id),
        action=parse_optional_str(action),
        table_name=parse_optional_str(table_name),
        date_from=parse_optional_str(date_from),
        date_to=parse_optional_str(date_to),
        search=parse_optional_str(search),
        order_by=order_by,
        order_direction=order_direction
    )
    
    return controllers.get_audit_logs_list(db, filters)


@router.get("/audit/logs/{log_id}", response_model=AuditLogOut, tags=["audit"])
def get_audit_log(
    request: Request,
    log_id: int,
    db: Session = Depends(get_db)
):
    """Получить аудит-лог по ID"""
    require_admin(request)
    
    return controllers.get_audit_log_by_id_controller(db, log_id)


@router.get("/audit/stats", response_model=AuditStatistics, tags=["audit"])
def get_audit_statistics(
    request: Request,
    date_from: Optional[str] = Query(None, description="Дата от (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Дата до (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Получить статистику аудита"""
    require_admin(request)
    
    return controllers.get_audit_statistics_controller(
        db, 
        parse_optional_str(date_from), 
        parse_optional_str(date_to)
    )


@router.get("/audit/actions", response_model=List[str], tags=["audit"])
def get_available_actions(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить список доступных действий"""
    require_admin(request)
    
    return controllers.get_available_actions_controller(db)


@router.get("/audit/tables", response_model=List[str], tags=["audit"])
def get_available_tables(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить список доступных таблиц"""
    require_admin(request)
    
    return controllers.get_available_tables_controller(db)


@router.delete("/audit/cleanup", response_model=CleanupResult, tags=["audit"])
def cleanup_old_audit_logs(
    request: Request,
    days_to_keep: int = Query(90, ge=1, description="Количество дней для хранения"),
    db: Session = Depends(get_db)
):
    """Очистить старые аудит-логи"""
    require_admin(request)
    
    return controllers.cleanup_old_logs_controller(db, days_to_keep)


# Вспомогательный эндпоинт для получения текущего пользователя (для логирования)
@router.get("/audit/current-user", tags=["audit"])
def get_current_user_for_audit(request: Request):
    """Получить информацию о текущем пользователе для аудита"""
    try:
        user = get_current_user(request)
        return {
            "id": user.id,
            "username": user.username,
            "full_name": getattr(user, 'full_name', None),
            "role": user.role.name if user.role else None
        }
    except:
        return None
