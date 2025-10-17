import hashlib
import secrets
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.external.sqlalchemy.models import ApiToken, User
from app.api.api_tokens.models import (
    ApiTokenCreateRequest, 
    ApiTokenUpdateRequest,
    ApiTokenFilter,
    ApiTokenStats
)


def generate_api_token() -> Tuple[str, str, str]:
    """
    Генерирует новый API токен
    Возвращает: (полный_токен, хеш_токена, префикс)
    """
    # Генерируем случайный токен
    token = secrets.token_urlsafe(32)  # 43 символа в base64
    
    # Создаем хеш токена для хранения в БД
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Префикс для идентификации (первые 8 символов)
    token_prefix = token[:8]
    
    return token, token_hash, token_prefix


def hash_token(token: str) -> str:
    """Создает хеш токена"""
    return hashlib.sha256(token.encode()).hexdigest()


def create_api_token(
    db: Session, 
    token_data: ApiTokenCreateRequest, 
    created_by: int
) -> Tuple[ApiToken, str]:
    """Создать новый API токен"""
    
    # Генерируем токен
    token, token_hash, token_prefix = generate_api_token()
    
    # Создаем запись в БД
    db_token = ApiToken(
        name=token_data.name,
        description=token_data.description,
        token_hash=token_hash,
        token_prefix=token_prefix,
        created_by=created_by,
        permissions=token_data.permissions,
        scopes=[scope.value for scope in token_data.scopes] if token_data.scopes else None,
        ip_whitelist=token_data.ip_whitelist,
        rate_limit=token_data.rate_limit,
        expires_at=token_data.expires_at
    )
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    
    return db_token, token


def get_api_token_by_id(db: Session, token_id: int) -> Optional[ApiToken]:
    """Получить API токен по ID"""
    from sqlalchemy.orm import joinedload
    from app.external.sqlalchemy.models import User
    return db.query(ApiToken).options(
        joinedload(ApiToken.creator).joinedload(User.role)
    ).filter(ApiToken.id == token_id).first()


def get_api_token_by_hash(db: Session, token_hash: str) -> Optional[ApiToken]:
    """Получить API токен по хешу"""
    from sqlalchemy.orm import joinedload
    from app.external.sqlalchemy.models import User
    return db.query(ApiToken)\
        .options(
            joinedload(ApiToken.creator).joinedload(User.role)
        )\
        .filter(ApiToken.token_hash == token_hash)\
        .first()


def get_api_tokens(
    db: Session,
    filters: Optional[ApiTokenFilter] = None,
    skip: int = 0,
    limit: int = 100,
    created_by: Optional[int] = None  # Фильтр по создателю (для обычных пользователей)
) -> List[ApiToken]:
    """Получить список API токенов с фильтрацией"""
    
    from sqlalchemy.orm import joinedload
    from app.external.sqlalchemy.models import User
    query = db.query(ApiToken).options(
        joinedload(ApiToken.creator).joinedload(User.role)
    )
    
    # Фильтр по создателю (для безопасности)
    if created_by is not None:
        query = query.filter(ApiToken.created_by == created_by)
    
    # Применяем фильтры
    if filters:
        if filters.name_contains:
            query = query.filter(ApiToken.name.ilike(f"%{filters.name_contains}%"))
        
        if filters.created_by:
            query = query.filter(ApiToken.created_by == filters.created_by)
        
        if filters.is_active is not None:
            query = query.filter(ApiToken.is_active == filters.is_active)
        
        if filters.has_scope:
            # Проверяем наличие области в JSON массиве
            query = query.filter(ApiToken.scopes.contains([filters.has_scope.value]))
        
        if filters.expires_before:
            query = query.filter(ApiToken.expires_at < filters.expires_before)
        
        if filters.expires_after:
            query = query.filter(ApiToken.expires_at > filters.expires_after)
        
        if filters.last_used_before:
            query = query.filter(ApiToken.last_used_at < filters.last_used_before)
        
        if filters.last_used_after:
            query = query.filter(ApiToken.last_used_at > filters.last_used_after)
    
    return query.offset(skip).limit(limit).all()


def update_api_token(
    db: Session, 
    token_id: int, 
    token_data: ApiTokenUpdateRequest,
    updated_by: Optional[int] = None
) -> Optional[ApiToken]:
    """Обновить API токен"""
    
    db_token = db.query(ApiToken).filter(ApiToken.id == token_id).first()
    if not db_token:
        return None
    
    # Проверяем права доступа (пользователь может редактировать только свои токены)
    if updated_by is not None and db_token.created_by != updated_by:
        return None
    
    # Обновляем поля
    if token_data.name is not None:
        db_token.name = token_data.name
    
    if token_data.description is not None:
        db_token.description = token_data.description
    
    if token_data.permissions is not None:
        db_token.permissions = token_data.permissions
    
    if token_data.scopes is not None:
        db_token.scopes = [scope.value for scope in token_data.scopes]
    
    if token_data.ip_whitelist is not None:
        db_token.ip_whitelist = token_data.ip_whitelist
    
    if token_data.rate_limit is not None:
        db_token.rate_limit = token_data.rate_limit
    
    if token_data.is_active is not None:
        db_token.is_active = token_data.is_active
    
    if token_data.expires_at is not None:
        db_token.expires_at = token_data.expires_at
    
    db_token.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_token)
    
    return db_token


def delete_api_token(
    db: Session, 
    token_id: int,
    deleted_by: Optional[int] = None
) -> bool:
    """Удалить API токен"""
    
    db_token = db.query(ApiToken).filter(ApiToken.id == token_id).first()
    if not db_token:
        return False
    
    # Проверяем права доступа
    if deleted_by is not None and db_token.created_by != deleted_by:
        return False
    
    db.delete(db_token)
    db.commit()
    
    return True


def update_token_usage(db: Session, token_hash: str, ip_address: str) -> bool:
    """Обновить статистику использования токена"""
    
    db_token = db.query(ApiToken).filter(ApiToken.token_hash == token_hash).first()
    if not db_token:
        return False
    
    db_token.last_used_at = datetime.utcnow()
    db_token.usage_count += 1
    
    db.commit()
    
    return True


def get_api_tokens_stats(db: Session, created_by: Optional[int] = None) -> ApiTokenStats:
    """Получить статистику по API токенам"""
    
    query = db.query(ApiToken)
    
    # Фильтр по создателю
    if created_by is not None:
        query = query.filter(ApiToken.created_by == created_by)
    
    all_tokens = query.all()
    
    total_tokens = len(all_tokens)
    active_tokens = sum(1 for token in all_tokens if token.is_active and not token.is_expired())
    expired_tokens = sum(1 for token in all_tokens if token.is_expired())
    inactive_tokens = sum(1 for token in all_tokens if not token.is_active)
    total_usage = sum(token.usage_count for token in all_tokens)
    
    # Статистика по пользователям
    tokens_by_user = {}
    user_query = db.query(User.username, func.count(ApiToken.id).label('count')).join(
        ApiToken, User.id == ApiToken.created_by
    ).group_by(User.username)
    
    if created_by is not None:
        user_query = user_query.filter(ApiToken.created_by == created_by)
    
    for username, count in user_query.all():
        tokens_by_user[username] = count
    
    # Наиболее используемые токены
    most_used_query = query.order_by(ApiToken.usage_count.desc()).limit(10)
    most_used_tokens = [
        {
            'id': token.id,
            'name': token.name,
            'usage_count': token.usage_count,
            'last_used_at': token.last_used_at
        }
        for token in most_used_query.all()
    ]
    
    # Недавнее использование
    recent_usage_query = query.filter(
        ApiToken.last_used_at.isnot(None)
    ).order_by(ApiToken.last_used_at.desc()).limit(10)
    
    recent_usage = [
        {
            'id': token.id,
            'name': token.name,
            'last_used_at': token.last_used_at,
            'usage_count': token.usage_count
        }
        for token in recent_usage_query.all()
    ]
    
    return ApiTokenStats(
        total_tokens=total_tokens,
        active_tokens=active_tokens,
        expired_tokens=expired_tokens,
        inactive_tokens=inactive_tokens,
        total_usage=total_usage,
        tokens_by_user=tokens_by_user,
        most_used_tokens=most_used_tokens,
        recent_usage=recent_usage
    )


def validate_api_token(db: Session, token: str, ip_address: str) -> Optional[ApiToken]:
    """
    Проверить валидность API токена
    Возвращает объект токена если валиден, иначе None
    """
    
    token_hash = hash_token(token)
    db_token = get_api_token_by_hash(db, token_hash)
    
    if not db_token:
        return None
    
    # Проверяем валидность
    if not db_token.is_valid():
        return None
    
    # Проверяем IP whitelist
    if not db_token.is_ip_allowed(ip_address):
        return None
    
    # Обновляем статистику использования (в фоновом режиме)
    try:
        update_token_usage(db, token_hash, ip_address)
    except Exception:
        pass  # Не ломаем основной процесс из-за ошибки в статистике
    
    return db_token
