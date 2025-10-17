from typing import List, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.api_tokens.models import (
    ApiTokenCreateRequest,
    ApiTokenUpdateRequest,
    ApiTokenResponse,
    ApiTokenCreateResponse,
    ApiTokenFilter,
    ApiTokenStats,
    PERMISSION_PRESETS
)
from app.external.sqlalchemy.utils.api_tokens import (
    create_api_token,
    get_api_token_by_id,
    get_api_tokens,
    update_api_token,
    delete_api_token,
    get_api_tokens_stats,
    validate_api_token
)
from app.external.sqlalchemy.models import ApiToken


def _convert_token_to_response(token: ApiToken) -> ApiTokenResponse:
    """Конвертировать SQLAlchemy объект в Pydantic модель"""
    return ApiTokenResponse(
        id=token.id,
        name=token.name,
        description=token.description,
        token_prefix=token.token_prefix,
        permissions=token.permissions or [],
        scopes=token.scopes,
        ip_whitelist=token.ip_whitelist,
        rate_limit=token.rate_limit,
        is_active=token.is_active,
        expires_at=token.expires_at,
        last_used_at=token.last_used_at,
        usage_count=token.usage_count,
        created_at=token.created_at,
        updated_at=token.updated_at,
        created_by=token.created_by,
        creator_username=token.creator.username if token.creator else None
    )


def create_api_token_controller(
    db: Session, 
    token_data: ApiTokenCreateRequest, 
    created_by: int
) -> ApiTokenCreateResponse:
    """Создать новый API токен"""
    
    try:
        db_token, full_token = create_api_token(db, token_data, created_by)
        token_response = _convert_token_to_response(db_token)
        
        return ApiTokenCreateResponse(
            token_info=token_response,
            token=full_token
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания токена: {str(e)}")


def get_api_tokens_list(
    db: Session,
    filters: Optional[ApiTokenFilter] = None,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    is_admin: bool = False
) -> List[ApiTokenResponse]:
    """Получить список API токенов"""
    
    # Обычные пользователи видят только свои токены
    created_by = None if is_admin else user_id
    
    tokens = get_api_tokens(db, filters, skip, limit, created_by)
    return [_convert_token_to_response(token) for token in tokens]


def get_api_token_by_id_controller(
    db: Session, 
    token_id: int,
    user_id: Optional[int] = None,
    is_admin: bool = False
) -> Optional[ApiTokenResponse]:
    """Получить API токен по ID"""
    
    token = get_api_token_by_id(db, token_id)
    if not token:
        return None
    
    # Проверяем права доступа
    if not is_admin and token.created_by != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому токену")
    
    return _convert_token_to_response(token)


def update_api_token_controller(
    db: Session, 
    token_id: int, 
    token_data: ApiTokenUpdateRequest,
    user_id: Optional[int] = None,
    is_admin: bool = False
) -> Optional[ApiTokenResponse]:
    """Обновить API токен"""
    
    # Проверяем существование токена
    existing_token = get_api_token_by_id(db, token_id)
    if not existing_token:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    # Проверяем права доступа
    if not is_admin and existing_token.created_by != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому токену")
    
    updated_by = None if is_admin else user_id
    token = update_api_token(db, token_id, token_data, updated_by)
    
    if not token:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    return _convert_token_to_response(token)


def delete_api_token_controller(
    db: Session, 
    token_id: int,
    user_id: Optional[int] = None,
    is_admin: bool = False
) -> bool:
    """Удалить API токен"""
    
    # Проверяем существование токена
    existing_token = get_api_token_by_id(db, token_id)
    if not existing_token:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    # Проверяем права доступа
    if not is_admin and existing_token.created_by != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому токену")
    
    deleted_by = None if is_admin else user_id
    success = delete_api_token(db, token_id, deleted_by)
    
    if not success:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    return True


def get_api_tokens_stats_controller(
    db: Session,
    user_id: Optional[int] = None,
    is_admin: bool = False
) -> ApiTokenStats:
    """Получить статистику по API токенам"""
    
    # Обычные пользователи видят статистику только по своим токенам
    created_by = None if is_admin else user_id
    
    return get_api_tokens_stats(db, created_by)


def get_permission_presets() -> dict:
    """Получить предустановленные наборы разрешений"""
    return PERMISSION_PRESETS


def validate_api_token_controller(
    db: Session,
    token: str,
    ip_address: str
) -> Optional[ApiToken]:
    """Проверить валидность API токена"""
    return validate_api_token(db, token, ip_address)


def revoke_api_token(
    db: Session,
    token_id: int,
    user_id: Optional[int] = None,
    is_admin: bool = False
) -> bool:
    """Отозвать API токен (деактивировать)"""
    
    from app.api.api_tokens.models import ApiTokenUpdateRequest
    
    try:
        token_data = ApiTokenUpdateRequest(is_active=False)
        result = update_api_token_controller(db, token_id, token_data, user_id, is_admin)
        return result is not None
    except HTTPException:
        return False


def regenerate_api_token(
    db: Session,
    token_id: int,
    user_id: Optional[int] = None,
    is_admin: bool = False
) -> Optional[ApiTokenCreateResponse]:
    """Перегенерировать API токен (создать новый с теми же настройками)"""
    
    # Получаем существующий токен
    existing_token = get_api_token_by_id(db, token_id)
    if not existing_token:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    # Проверяем права доступа
    if not is_admin and existing_token.created_by != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому токену")
    
    # Создаем новый токен с теми же параметрами
    from app.api.api_tokens.models import ApiTokenCreateRequest, ApiTokenScope
    
    new_token_data = ApiTokenCreateRequest(
        name=f"{existing_token.name} (обновленный)",
        description=existing_token.description,
        permissions=existing_token.permissions or [],
        scopes=[ApiTokenScope(scope) for scope in existing_token.scopes] if existing_token.scopes else None,
        ip_whitelist=existing_token.ip_whitelist,
        rate_limit=existing_token.rate_limit,
        expires_at=existing_token.expires_at
    )
    
    # Создаем новый токен
    new_token = create_api_token_controller(db, new_token_data, existing_token.created_by)
    
    # Деактивируем старый токен
    revoke_api_token(db, token_id, user_id, is_admin)
    
    return new_token


def check_token_permission(
    token: ApiToken,
    required_permission: str,
    resource_scope: Optional[str] = None
) -> bool:
    """
    Проверить, есть ли у токена необходимое разрешение
    
    Args:
        token: API токен
        required_permission: Требуемое разрешение (например, "read:machines")
        resource_scope: Область ресурса (опционально)
    
    Returns:
        bool: True если разрешение есть
    """
    
    if not token.is_valid():
        return False
    
    permissions = token.permissions or []
    
    # Проверяем точное совпадение разрешения
    if required_permission in permissions:
        return True
    
    # Проверяем wildcard разрешения
    action, scope = required_permission.split(':', 1) if ':' in required_permission else (required_permission, '*')
    
    wildcard_permissions = [
        f"{action}:*",  # Действие для всех ресурсов
        f"*:{scope}",   # Все действия для ресурса
        "*:*",          # Все действия для всех ресурсов
        "admin:*"       # Админские права
    ]
    
    for wildcard in wildcard_permissions:
        if wildcard in permissions:
            return True
    
    # Проверяем область действия токена
    if resource_scope and not token.has_scope(resource_scope):
        return False
    
    return False
