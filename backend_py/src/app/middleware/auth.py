from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Set
import re

from app.api.auth.jwt import verify_token
from app.external.sqlalchemy.session import SessionLocal
from app.external.sqlalchemy.utils.users import get_user_by_id


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware для автоматической аутентификации всех API эндпоинтов"""
    
    def __init__(self, app, excluded_paths: List[str] = None):
        super().__init__(app)
        
        # Пути, которые не требуют аутентификации
        default_excluded = [
            "/api/auth/login",
            "/api/auth/register", 
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
            "/status",
            "/",
            "/favicon.ico",
        ]
        
        self.excluded_paths = set(default_excluded + (excluded_paths or []))
        
        # Паттерны для исключения (например, статические файлы)
        self.excluded_patterns = [
            r"^/static/.*",
            r"^/assets/.*",
            r"^/api/documents/download/.*",  # Скачивание по токену
        ]
    
    def _is_excluded_path(self, path: str) -> bool:
        """Проверяет, исключен ли путь из аутентификации"""
        # Проверяем точные совпадения
        if path in self.excluded_paths:
            return True
            
        # Проверяем паттерны
        for pattern in self.excluded_patterns:
            if re.match(pattern, path):
                return True
                
        # Проверяем API пути, которые не начинаются с /api (например, статика)
        if not path.startswith("/api"):
            return True
            
        return False
    
    def _extract_token_from_request(self, request: Request) -> tuple[str | None, str]:
        """
        Извлекает токен из заголовка Authorization
        Возвращает: (токен, тип_токена)
        где тип_токена: 'jwt' или 'api'
        """
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None, "jwt"
            
        parts = authorization.split()
        if len(parts) != 2:
            return None, "jwt"
        
        scheme = parts[0].lower()
        token = parts[1]
        
        if scheme == "bearer":
            return token, "jwt"
        elif scheme == "token":
            return token, "api"
        else:
            return None, "jwt"
    
    async def dispatch(self, request: Request, call_next):
        # Проверяем, нужна ли аутентификация для этого пути
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        # Пропускаем OPTIONS запросы (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Извлекаем токен
        token, token_type = self._extract_token_from_request(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Authorization token required",
                    "error": "missing_token"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Обрабатываем токен в зависимости от типа
        try:
            if token_type == "api":
                # Обработка API токена
                success = await self._handle_api_token(request, token)
                if not success:
                    raise ValueError("Invalid API token")
            else:
                # Обработка JWT токена (по умолчанию)
                payload = verify_token(token)
                if payload is None:
                    raise ValueError("Invalid token")
                    
                user_id = payload.get("sub")
                if user_id is None:
                    raise ValueError("Invalid token payload")
                
                # Проверяем существование пользователя для JWT
                await self._handle_jwt_user(request, user_id)
                
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid or expired token",
                    "error": "invalid_token"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        
        # Продолжаем обработку запроса
        response = await call_next(request)
        return response
    
    async def _handle_jwt_user(self, request: Request, user_id: int):
        """Обработка пользователя для JWT токена"""
        db = SessionLocal()
        try:
            user = get_user_by_id(db, user_id)
            if user is None:
                raise ValueError("User not found")
                
            if not user.is_active:
                raise ValueError("User account is inactive")
            
            # Добавляем информацию о пользователе в состояние запроса
            request.state.current_user = user
            request.state.user_id = user_id
            request.state.user_role = user.role.name if user.role else None
            request.state.auth_type = "jwt"
            
        finally:
            db.close()
    
    async def _handle_api_token(self, request: Request, token: str) -> bool:
        """Обработка API токена"""
        from app.external.sqlalchemy.utils.api_tokens import validate_api_token
        
        # Получаем IP адрес клиента
        ip_address = request.client.host if request.client else "127.0.0.1"
        
        db = SessionLocal()
        try:
            api_token = validate_api_token(db, token, ip_address)
            if not api_token:
                return False
            
            # Сохраняем информацию об API токене в request.state
            request.state.api_token = api_token
            request.state.user_id = api_token.created_by
            request.state.auth_type = "api"
            
            # Для совместимости также добавляем пользователя
            if api_token.creator:
                request.state.current_user = api_token.creator
                request.state.user_role = api_token.creator.role.name if api_token.creator.role else None
            
            return True
            
        finally:
            db.close()


# Вспомогательные функции для использования в эндпоинтах
def get_current_user_from_request(request: Request):
    """Получить текущего пользователя из состояния запроса"""
    if not hasattr(request.state, 'current_user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.current_user


def get_current_user_role(request: Request) -> str:
    """Получить роль текущего пользователя"""
    if not hasattr(request.state, 'user_role'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user_role


def require_admin_role(request: Request):
    """Проверить, что пользователь имеет роль администратора"""
    user_role = get_current_user_role(request)
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return True


def require_user_role(request: Request):
    """Проверить, что пользователь имеет роль user или admin"""
    user_role = get_current_user_role(request)
    if user_role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User privileges required"
        )
    return True
