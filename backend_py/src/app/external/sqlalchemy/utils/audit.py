from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, and_, or_
from app.external.sqlalchemy.models import AuditLog, User


def create_audit_log(
    db: Session,
    user_id: Optional[int] = None,
    action: str = "",
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    request_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    status_code: Optional[int] = None,
    error_message: Optional[str] = None,
) -> AuditLog:
    """Создать новую запись аудит-лога"""
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        request_id=request_id,
        duration_ms=duration_ms,
        status_code=status_code,
        error_message=error_message,
        created_at=datetime.utcnow(),
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    table_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    order_by: str = "created_at",
    order_direction: str = "desc",
) -> List[AuditLog]:
    """Получить список аудит-логов с фильтрацией"""
    
    query = db.query(AuditLog)
    
    # Применяем фильтры
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    
    if date_to:
        # Добавляем время до конца дня
        end_of_day = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
        query = query.filter(AuditLog.created_at <= end_of_day)
    
    if search:
        # Поиск по IP адресу или User-Agent
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.ip_address.ilike(search_pattern),
                AuditLog.user_agent.ilike(search_pattern),
                AuditLog.endpoint.ilike(search_pattern),
                AuditLog.error_message.ilike(search_pattern),
            )
        )
    
    # Сортировка
    if order_direction.lower() == "desc":
        query = query.order_by(desc(getattr(AuditLog, order_by, AuditLog.created_at)))
    else:
        query = query.order_by(asc(getattr(AuditLog, order_by, AuditLog.created_at)))
    
    return query.offset(skip).limit(limit).all()


def get_audit_log_by_id(db: Session, audit_log_id: int) -> Optional[AuditLog]:
    """Получить аудит-лог по ID"""
    return db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()


def count_audit_logs(
    db: Session,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    table_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
) -> int:
    """Подсчитать количество аудит-логов с фильтрацией"""
    
    query = db.query(func.count(AuditLog.id))
    
    # Применяем те же фильтры что и в get_audit_logs
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    
    if date_to:
        end_of_day = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
        query = query.filter(AuditLog.created_at <= end_of_day)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.ip_address.ilike(search_pattern),
                AuditLog.user_agent.ilike(search_pattern),
                AuditLog.endpoint.ilike(search_pattern),
                AuditLog.error_message.ilike(search_pattern),
            )
        )
    
    return query.scalar() or 0


def get_audit_statistics(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Получить статистику по аудит-логам"""
    
    # Базовый запрос
    base_query = db.query(AuditLog)
    
    if date_from:
        base_query = base_query.filter(AuditLog.created_at >= date_from)
    
    if date_to:
        end_of_day = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
        base_query = base_query.filter(AuditLog.created_at <= end_of_day)
    
    # Общее количество
    total_count = base_query.count()
    
    # Статистика по действиям
    action_stats = (
        base_query.with_entities(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        )
        .group_by(AuditLog.action)
        .order_by(desc('count'))
        .all()
    )
    
    # Статистика по пользователям
    user_stats = (
        base_query.join(User, AuditLog.user_id == User.id, isouter=True)
        .with_entities(
            User.id.label('user_id'),
            User.username,
            User.full_name,
            func.count(AuditLog.id).label('count')
        )
        .group_by(User.id, User.username, User.full_name)
        .order_by(desc('count'))
        .limit(10)
        .all()
    )
    
    # Статистика по таблицам
    table_stats = (
        base_query.filter(AuditLog.table_name.isnot(None))
        .with_entities(
            AuditLog.table_name,
            func.count(AuditLog.id).label('count')
        )
        .group_by(AuditLog.table_name)
        .order_by(desc('count'))
        .all()
    )
    
    # Статистика по часам (за последние 24 часа)
    hours_ago_24 = datetime.utcnow() - timedelta(hours=24)
    
    # Используем PostgreSQL-совместимую функцию для группировки по часам
    hourly_stats = (
        base_query.filter(AuditLog.created_at >= hours_ago_24)
        .with_entities(
            func.to_char(AuditLog.created_at, 'YYYY-MM-DD HH24:00:00').label('hour'),
            func.count(AuditLog.id).label('count')
        )
        .group_by('hour')
        .order_by('hour')
        .all()
    )
    
    return {
        'total_count': total_count,
        'action_stats': [
            {'action': action, 'count': count} 
            for action, count in action_stats
        ],
        'user_stats': [
            {
                'user': {
                    'id': user_id,
                    'username': username,
                    'full_name': full_name,
                } if user_id else None,
                'count': count
            }
            for user_id, username, full_name, count in user_stats
        ],
        'table_stats': [
            {'table_name': table_name, 'count': count}
            for table_name, count in table_stats
        ],
        'hourly_stats': [
            {'hour': hour, 'count': count}  # hour уже строка после to_char
            for hour, count in hourly_stats
        ]
    }


def get_available_actions(db: Session) -> List[str]:
    """Получить список всех доступных действий"""
    actions = (
        db.query(AuditLog.action)
        .distinct()
        .order_by(AuditLog.action)
        .all()
    )
    return [action[0] for action in actions if action[0]]


def get_available_tables(db: Session) -> List[str]:
    """Получить список всех таблиц в аудит-логах"""
    tables = (
        db.query(AuditLog.table_name)
        .filter(AuditLog.table_name.isnot(None))
        .distinct()
        .order_by(AuditLog.table_name)
        .all()
    )
    return [table[0] for table in tables if table[0]]


def cleanup_old_audit_logs(db: Session, days_to_keep: int = 90) -> int:
    """Удалить старые аудит-логи (старше указанного количества дней)"""
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    deleted_count = (
        db.query(AuditLog)
        .filter(AuditLog.created_at < cutoff_date)
        .count()
    )
    
    db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).delete()
    db.commit()
    
    return deleted_count


def log_user_action(
    db: Session,
    user_id: Optional[int],
    action: str,
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
) -> AuditLog:
    """Упрощенная функция для логирования действий пользователя"""
    return create_audit_log(
        db=db,
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
    )
