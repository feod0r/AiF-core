from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.api.audit.models import (
    AuditLogOut,
    AuditLogCreate,
    AuditLogFilter,
    AuditStatistics,
    AuditLogsList,
    CleanupResult,
    UserSimple,
)
from app.external.sqlalchemy.utils.audit import (
    create_audit_log,
    get_audit_logs,
    get_audit_log_by_id,
    count_audit_logs,
    get_audit_statistics,
    get_available_actions,
    get_available_tables,
    cleanup_old_audit_logs,
)


def _convert_user_to_simple(user) -> Optional[UserSimple]:
    """Конвертировать User в UserSimple"""
    if not user:
        return None

    try:
        role_data = None
        if hasattr(user, "role") and user.role:
            role_data = {
                "name": getattr(user.role, "name", ""),
                "description": getattr(user.role, "description", ""),
            }

        return UserSimple(
            id=getattr(user, "id", 0),
            username=getattr(user, "username", ""),
            full_name=getattr(user, "full_name", None),
            role=role_data,
        )
    except Exception as e:
        print(f"Error converting user to simple: {e}")
        return None


def _convert_audit_log_to_out(audit_log) -> AuditLogOut:
    """Конвертировать AuditLog в AuditLogOut"""
    user_simple = _convert_user_to_simple(audit_log.user) if audit_log.user else None

    return AuditLogOut(
        id=audit_log.id,
        user=user_simple,
        action=audit_log.action,
        table_name=audit_log.table_name,
        record_id=audit_log.record_id,
        old_values=audit_log.old_values,
        new_values=audit_log.new_values,
        ip_address=audit_log.ip_address,
        user_agent=audit_log.user_agent,
        endpoint=audit_log.endpoint,
        method=audit_log.method,
        request_id=audit_log.request_id,
        duration_ms=audit_log.duration_ms,
        status_code=audit_log.status_code,
        error_message=audit_log.error_message,
        created_at=audit_log.created_at,
    )


def create_audit_log_entry(db: Session, audit_data: AuditLogCreate) -> AuditLogOut:
    """Создать новую запись аудит-лога"""
    try:
        audit_log = create_audit_log(
            db=db,
            user_id=audit_data.user_id,
            action=audit_data.action,
            table_name=audit_data.table_name,
            record_id=audit_data.record_id,
            old_values=audit_data.old_values,
            new_values=audit_data.new_values,
            ip_address=audit_data.ip_address,
            user_agent=audit_data.user_agent,
            endpoint=audit_data.endpoint,
            method=audit_data.method,
            request_id=audit_data.request_id,
            duration_ms=audit_data.duration_ms,
            status_code=audit_data.status_code,
            error_message=audit_data.error_message,
        )

        return _convert_audit_log_to_out(audit_log)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create audit log: {str(e)}"
        )


def get_audit_logs_list(db: Session, filters: AuditLogFilter) -> AuditLogsList:
    """Получить список аудит-логов с фильтрацией"""
    try:
        # Конвертируем строки дат в datetime объекты
        date_from = None
        date_to = None

        if filters.date_from:
            try:
                date_from = datetime.strptime(filters.date_from, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD"
                )

        if filters.date_to:
            try:
                date_to = datetime.strptime(filters.date_to, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD"
                )

        # Вычисляем skip для пагинации
        skip = (filters.page - 1) * filters.limit

        # Получаем логи
        audit_logs = get_audit_logs(
            db=db,
            skip=skip,
            limit=filters.limit,
            user_id=filters.user_id,
            action=filters.action,
            table_name=filters.table_name,
            date_from=date_from,
            date_to=date_to,
            search=filters.search,
            order_by=filters.order_by,
            order_direction=filters.order_direction,
        )

        # Получаем общее количество для пагинации
        total_count = count_audit_logs(
            db=db,
            user_id=filters.user_id,
            action=filters.action,
            table_name=filters.table_name,
            date_from=date_from,
            date_to=date_to,
            search=filters.search,
        )

        # Конвертируем в выходные модели
        logs_out = [_convert_audit_log_to_out(log) for log in audit_logs]

        # Формируем информацию о пагинации
        total_pages = (total_count + filters.limit - 1) // filters.limit
        pagination = {
            "current_page": filters.page,
            "page_size": filters.limit,
            "total_items": total_count,
            "total_pages": total_pages,
            "has_next": filters.page < total_pages,
            "has_prev": filters.page > 1,
        }

        return AuditLogsList(logs=logs_out, pagination=pagination)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get audit logs: {str(e)}"
        )


def get_audit_log_by_id_controller(db: Session, log_id: int) -> AuditLogOut:
    """Получить аудит-лог по ID"""
    audit_log = get_audit_log_by_id(db, log_id)

    if not audit_log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return _convert_audit_log_to_out(audit_log)


def get_audit_statistics_controller(
    db: Session, date_from: Optional[str] = None, date_to: Optional[str] = None
) -> AuditStatistics:
    """Получить статистику аудита"""
    try:
        # Конвертируем даты
        parsed_date_from = None
        parsed_date_to = None

        if date_from:
            try:
                parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD"
                )

        if date_to:
            try:
                parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD"
                )

        # Получаем статистику
        stats = get_audit_statistics(
            db=db, date_from=parsed_date_from, date_to=parsed_date_to
        )

        return AuditStatistics(**stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get audit statistics: {str(e)}"
        )


def get_available_actions_controller(db: Session) -> List[str]:
    """Получить список доступных действий"""
    try:
        return get_available_actions(db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get available actions: {str(e)}"
        )


def get_available_tables_controller(db: Session) -> List[str]:
    """Получить список доступных таблиц"""
    try:
        return get_available_tables(db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get available tables: {str(e)}"
        )


def cleanup_old_logs_controller(db: Session, days_to_keep: int = 90) -> CleanupResult:
    """Очистить старые аудит-логи"""
    try:
        if days_to_keep < 1:
            raise HTTPException(
                status_code=400, detail="days_to_keep must be at least 1"
            )

        deleted_count = cleanup_old_audit_logs(db, days_to_keep)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        return CleanupResult(
            deleted_count=deleted_count,
            cutoff_date=cutoff_date,
            message=f"Deleted {deleted_count} audit logs older than {days_to_keep} days",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup audit logs: {str(e)}"
        )
