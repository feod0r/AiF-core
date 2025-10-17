from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.auth.jwt import verify_token
from app.external.sqlalchemy.session import get_db
from app.external.sqlalchemy.utils.users import get_user_by_id

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Получение текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    """Получение активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_admin(current_user=Depends(get_current_active_user)):
    """Требование прав администратора"""
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def require_user_role(current_user=Depends(get_current_active_user)):
    """Требование роли пользователя (admin или user)"""
    if current_user.role.name not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


# --- Новые функции для работы с middleware ---

def get_current_user_from_middleware(request: Request, db: Session = Depends(get_db)):
    """Получение текущего пользователя из middleware (JWT или API токен)"""
    # Проверяем, что middleware установил пользователя
    if not hasattr(request.state, 'current_user') or not request.state.current_user:
        # Если нет current_user, пробуем получить по user_id
        if hasattr(request.state, 'user_id') and request.state.user_id:
            user = get_user_by_id(db, request.state.user_id)
            if user:
                return user
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return request.state.current_user


def get_current_active_user_from_middleware(request: Request, db: Session = Depends(get_db)):
    """Получение активного пользователя из middleware"""
    current_user = get_current_user_from_middleware(request, db)
    
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_admin_from_middleware(request: Request, db: Session = Depends(get_db)):
    """Требование прав администратора (работает с middleware)"""
    current_user = get_current_active_user_from_middleware(request, db)
    
    # Для API токенов проверяем разрешения
    if hasattr(request.state, 'auth_type') and request.state.auth_type == "api":
        if hasattr(request.state, 'api_token') and request.state.api_token:
            api_token = request.state.api_token
            # Проверяем права администратора для API токена
            if not (api_token.has_permission("admin:*") or 
                   api_token.has_permission("read:users") and 
                   api_token.has_permission("write:users")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Insufficient permissions for API token"
                )
        return current_user
    
    # Для JWT токенов проверяем роль
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def require_user_role_from_middleware(request: Request, db: Session = Depends(get_db)):
    """Требование роли пользователя (admin или user) - работает с middleware"""
    current_user = get_current_active_user_from_middleware(request, db)
    
    # Для API токенов проверяем разрешения
    if hasattr(request.state, 'auth_type') and request.state.auth_type == "api":
        if hasattr(request.state, 'api_token') and request.state.api_token:
            api_token = request.state.api_token
            # Для пользовательской роли требуем минимальные права чтения
            if not (api_token.has_permission("read:*") or 
                   api_token.has_permission("admin:*")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Insufficient permissions for API token"
                )
        return current_user
    
    # Для JWT токенов проверяем роль
    if current_user.role.name not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user
