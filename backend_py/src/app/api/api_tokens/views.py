from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.api_tokens.models import (
    ApiTokenCreateRequest,
    ApiTokenUpdateRequest,
    ApiTokenResponse,
    ApiTokenCreateResponse,
    ApiTokenFilter,
    ApiTokenStats,
    ApiTokenScope
)
from app.api.api_tokens import controllers
from app.external.sqlalchemy.session import get_db
from app.api.auth.middleware_dependencies import get_current_user, get_user_id, require_admin

router = APIRouter()


@router.post("/api-tokens", response_model=ApiTokenCreateResponse, tags=["api_tokens"])
def create_api_token(
    request: Request,
    token_data: ApiTokenCreateRequest,
    db: Session = Depends(get_db)
):
    """Создать новый API токен"""
    
    user_id = get_user_id(request)
    
    return controllers.create_api_token_controller(db, token_data, user_id)


@router.get("/api-tokens", response_model=List[ApiTokenResponse], tags=["api_tokens"])
def get_api_tokens(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name_contains: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    has_scope: Optional[ApiTokenScope] = Query(None),
    db: Session = Depends(get_db)
):
    """Получить список API токенов"""
    
    user = get_current_user(request)
    user_id = user.id
    is_admin = user.role.name == "admin" if user.role else False
    
    filters = ApiTokenFilter(
        name_contains=name_contains,
        created_by=created_by,
        is_active=is_active,
        has_scope=has_scope
    )
    
    return controllers.get_api_tokens_list(db, filters, skip, limit, user_id, is_admin)


@router.get("/api-tokens/{token_id}", response_model=ApiTokenResponse, tags=["api_tokens"])
def get_api_token(
    request: Request,
    token_id: int,
    db: Session = Depends(get_db)
):
    """Получить API токен по ID"""
    
    user = get_current_user(request)
    user_id = user.id
    is_admin = user.role.name == "admin" if user.role else False
    
    token = controllers.get_api_token_by_id_controller(db, token_id, user_id, is_admin)
    if not token:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    return token


@router.put("/api-tokens/{token_id}", response_model=ApiTokenResponse, tags=["api_tokens"])
def update_api_token(
    request: Request,
    token_id: int,
    token_data: ApiTokenUpdateRequest,
    db: Session = Depends(get_db)
):
    """Обновить API токен"""
    
    user = get_current_user(request)
    user_id = user.id
    is_admin = user.role.name == "admin" if user.role else False
    
    return controllers.update_api_token_controller(db, token_id, token_data, user_id, is_admin)


@router.delete("/api-tokens/{token_id}", tags=["api_tokens"])
def delete_api_token(
    request: Request,
    token_id: int,
    db: Session = Depends(get_db)
):
    """Удалить API токен"""
    
    user = get_current_user(request)
    user_id = user.id
    is_admin = user.role.name == "admin" if user.role else False
    
    success = controllers.delete_api_token_controller(db, token_id, user_id, is_admin)
    if not success:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    return {"message": "Токен успешно удален"}


@router.post("/api-tokens/{token_id}/revoke", tags=["api_tokens"])
def revoke_api_token(
    request: Request,
    token_id: int,
    db: Session = Depends(get_db)
):
    """Отозвать (деактивировать) API токен"""
    
    user = get_current_user(request)
    user_id = user.id
    is_admin = user.role.name == "admin" if user.role else False
    
    success = controllers.revoke_api_token(db, token_id, user_id, is_admin)
    if not success:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    return {"message": "Токен успешно отозван"}


@router.post("/api-tokens/{token_id}/regenerate", response_model=ApiTokenCreateResponse, tags=["api_tokens"])
def regenerate_api_token(
    request: Request,
    token_id: int,
    db: Session = Depends(get_db)
):
    """Перегенерировать API токен"""
    
    user = get_current_user(request)
    user_id = user.id
    is_admin = user.role.name == "admin" if user.role else False
    
    new_token = controllers.regenerate_api_token(db, token_id, user_id, is_admin)
    if not new_token:
        raise HTTPException(status_code=404, detail="Токен не найден")
    
    return new_token


@router.get("/api-tokens/stats/summary", response_model=ApiTokenStats, tags=["api_tokens"])
def get_api_tokens_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить статистику по API токенам"""
    
    user = get_current_user(request)
    user_id = user.id
    is_admin = user.role.name == "admin" if user.role else False
    
    return controllers.get_api_tokens_stats_controller(db, user_id, is_admin)


@router.get("/api-tokens/presets/permissions", tags=["api_tokens"])
def get_permission_presets(request: Request):
    """Получить предустановленные наборы разрешений"""
    
    get_current_user(request)  # Проверяем авторизацию
    
    return controllers.get_permission_presets()


@router.get("/api-tokens/scopes/available", tags=["api_tokens"])
def get_available_scopes(request: Request):
    """Получить список доступных областей доступа"""
    
    get_current_user(request)  # Проверяем авторизацию
    
    return {
        "scopes": [
            {"value": scope.value, "label": scope.value.title().replace('_', ' ')}
            for scope in ApiTokenScope
        ]
    }


@router.get("/api-tokens/permissions/available", tags=["api_tokens"])
def get_available_permissions(request: Request):
    """Получить список доступных разрешений"""
    
    get_current_user(request)  # Проверяем авторизацию
    
    from app.api.api_tokens.models import ApiTokenPermission
    
    permissions = []
    scopes = [scope.value for scope in ApiTokenScope]
    
    for permission in ApiTokenPermission:
        for scope in scopes:
            permissions.append(f"{permission.value}:{scope}")
    
    # Добавляем wildcard разрешения
    for permission in ApiTokenPermission:
        permissions.append(f"{permission.value}:*")
    
    permissions.extend(["*:*", "admin:*"])
    
    return {
        "permissions": permissions,
        "permission_actions": [p.value for p in ApiTokenPermission],
        "permission_scopes": scopes
    }


# Административные эндпоинты
@router.get("/admin/api-tokens", response_model=List[ApiTokenResponse], tags=["admin", "api_tokens"])
def admin_get_all_api_tokens(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name_contains: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    has_scope: Optional[ApiTokenScope] = Query(None),
    db: Session = Depends(get_db)
):
    """Получить все API токены (только для администраторов)"""
    
    require_admin(request)
    
    filters = ApiTokenFilter(
        name_contains=name_contains,
        created_by=created_by,
        is_active=is_active,
        has_scope=has_scope
    )
    
    return controllers.get_api_tokens_list(db, filters, skip, limit, None, True)


@router.get("/admin/api-tokens/stats", response_model=ApiTokenStats, tags=["admin", "api_tokens"])
def admin_get_api_tokens_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить полную статистику по API токенам (только для администраторов)"""
    
    require_admin(request)
    
    return controllers.get_api_tokens_stats_controller(db, None, True)
