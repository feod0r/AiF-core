from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db
from app.middleware.auth import (
    get_current_user_from_request,
    get_current_user_role,
    require_admin_role as _require_admin_role,
    require_user_role as _require_user_role,
)


def get_current_user(request: Request):
    """Получение текущего пользователя из middleware"""
    return get_current_user_from_request(request)


def get_current_active_user(request: Request):
    """Получение активного пользователя из middleware"""
    user = get_current_user_from_request(request)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def require_admin(request: Request):
    """Требование прав администратора через middleware"""
    _require_admin_role(request)
    return get_current_active_user(request)


def require_user_role(request: Request):
    """Требование роли пользователя через middleware"""
    _require_user_role(request)
    return get_current_active_user(request)


def get_user_role(request: Request) -> str:
    """Получение роли пользователя из middleware"""
    return get_current_user_role(request)


def get_user_id(request: Request) -> int:
    """Получение ID пользователя из middleware"""
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user_id
