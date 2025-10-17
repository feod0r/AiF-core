import time
import uuid
import json
from typing import Optional, Dict, Any, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import SessionLocal
from app.external.sqlalchemy.utils.audit import log_user_action


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware для автоматического логирования HTTP запросов"""
    
    def __init__(
        self, 
        app: ASGIApp,
        excluded_paths: list = None,
        excluded_methods: list = None,
        log_get_requests: bool = False,  # По умолчанию не логируем GET запросы
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 1024 * 10  # 10KB
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/api/docs",
            "/api/redoc", 
            "/openapi.json",
            "/api/status",
            "/api/audit/logs",  # Избегаем циклического логирования аудита
            "/api/audit/stats",
            "/api/audit/actions",
            "/api/audit/tables",
        ]
        self.excluded_methods = excluded_methods or ["OPTIONS", "HEAD"]
        self.log_get_requests = log_get_requests
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size

    def _should_log_request(self, request: Request) -> bool:
        """Определить, нужно ли логировать запрос"""
        # Проверяем метод
        if request.method in self.excluded_methods:
            return False
        
        # Проверяем GET запросы, если они отключены
        if request.method == "GET" and not self.log_get_requests:
            return False
        
        # Проверяем путь
        path = request.url.path
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return False
        
        return True

    def _extract_user_info(self, request: Request) -> Optional[int]:
        """Извлечь информацию о пользователе из request.state"""
        try:
            return getattr(request.state, 'user_id', None)
        except:
            return None

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Получить IP адрес клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback на стандартный IP
        client_host = request.client.host if request.client else None
        return client_host

    def _extract_table_and_id_from_path(self, path: str, method: str) -> Tuple[Optional[str], Optional[int]]:
        """Извлечь название таблицы и ID записи из пути API"""
        try:
            # Удаляем /api/ префикс
            if path.startswith('/api/'):
                path = path[5:]
            
            parts = path.strip('/').split('/')
            if len(parts) == 0:
                return None, None
            
            # Первая часть - обычно название ресурса
            resource = parts[0]
            
            # Маппинг API эндпоинтов на таблицы
            table_mapping = {
                'auth': None,  # Добавляем auth для избежания ошибок
                'users': 'users',
                'machines': 'machines',
                'terminals': 'terminals',
                'owners': 'owners',
                'counterparties': 'counterparties',
                'transactions': 'transactions',
                'accounts': 'accounts',
                'items': 'items',
                'warehouses': 'warehouses',
                'inventory-movements': 'inventory_movements',
                'reports': 'reports',
                'info-cards': 'info_cards',
                'terminal-operations': 'terminal_operations',
                'documents': 'documents',
                'audit': None,  # Аудит не привязан к конкретной таблице
                'status': None,  # Статус системы
            }
            
            table_name = table_mapping.get(resource)
            
            # Пытаемся извлечь ID записи
            record_id = None
            if len(parts) >= 2 and table_name is not None:
                # Только для ресурсов с таблицами пытаемся извлечь ID
                try:
                    # Проверяем что вторая часть пути - это число (ID записи)
                    if parts[1].isdigit():
                        record_id = int(parts[1])
                    # Если не число, то это специальный эндпоинт, не ID
                except (ValueError, IndexError):
                    # Если не удается преобразовать в int, это не ID записи
                    record_id = None
            
            return table_name, record_id
            
        except Exception as e:
            # Логируем ошибку, но не ломаем middleware
            print(f"Error extracting table and ID from path '{path}': {e}")
            return None, None

    def _determine_action(self, method: str, path: str) -> str:
        """Определить тип действия на основе HTTP метода и пути"""
        if method == "GET":
            return "READ"
        elif method == "POST":
            if "login" in path:
                return "LOGIN"
            return "CREATE"
        elif method == "PUT":
            return "UPDATE"
        elif method == "PATCH":
            return "UPDATE"
        elif method == "DELETE":
            return "DELETE"
        else:
            return method.upper()

    async def _read_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Прочитать и распарсить тело запроса"""
        try:
            if not self.log_request_body:
                return None
            
            content_type = request.headers.get('content-type', '')
            if 'application/json' not in content_type:
                return None
            
            # Читаем тело запроса
            body = await request.body()
            if len(body) > self.max_body_size:
                return {"_truncated": f"Body too large ({len(body)} bytes)"}
            
            if body:
                return json.loads(body.decode('utf-8'))
            
        except Exception as e:
            return {"_error": f"Failed to parse body: {str(e)}"}
        
        return None

    async def dispatch(self, request: Request, call_next) -> Response:
        # Проверяем, нужно ли логировать
        if not self._should_log_request(request):
            return await call_next(request)
        
        # Генерируем уникальный ID запроса
        request_id = str(uuid.uuid4())
        
        # Засекаем время начала
        start_time = time.time()
        
        # Извлекаем информацию о запросе
        user_id = self._extract_user_info(request)
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get('User-Agent')
        method = request.method
        path = request.url.path
        action = self._determine_action(method, path)
        table_name, record_id = self._extract_table_and_id_from_path(path, method)
        
        # Читаем тело запроса для логирования (только для POST/PUT/PATCH)
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:
            request_body = await self._read_body(request)
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Вычисляем время выполнения
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Определяем сообщение об ошибке
        error_message = None
        if response.status_code >= 400:
            if response.status_code == 401:
                error_message = "Unauthorized"
            elif response.status_code == 403:
                error_message = "Forbidden"
            elif response.status_code == 404:
                error_message = "Not Found"
            elif response.status_code >= 500:
                error_message = "Internal Server Error"
            else:
                error_message = f"HTTP {response.status_code}"
        
        # Логируем в базу данных (в отдельной сессии)
        try:
            db = SessionLocal()
            try:
                # Объединяем техническую информацию с основной записью
                technical_info = {
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "query_params": dict(request.query_params) if request.query_params else None,
                }
                
                # Объединяем request_body с технической информацией
                combined_values = {}
                if request_body:
                    combined_values.update(request_body)
                combined_values.update(technical_info)
                
                log_user_action(
                    db=db,
                    user_id=user_id,
                    action=action,
                    table_name=table_name,
                    record_id=record_id,
                    old_values=None,  # Для HTTP логирования old_values не применимо
                    new_values=combined_values,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=path,
                    method=method,
                )
            finally:
                db.close()
                
        except Exception as e:
            # Логирование не должно ломать основной запрос
            print(f"Audit logging failed: {str(e)}")
        
        return response


def create_audit_entry(
    db: Session,
    user_id: Optional[int],
    action: str,
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Утилитная функция для создания записи аудита из кода приложения"""
    try:
        log_user_action(
            db=db,
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        print(f"Manual audit logging failed: {str(e)}")


def log_database_change(
    db: Session,
    user_id: Optional[int],
    action: str,  # CREATE, UPDATE, DELETE
    table_name: str,
    record_id: int,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
):
    """Специализированная функция для логирования изменений в базе данных"""
    try:
        log_user_action(
            db=db,
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
        )
    except Exception as e:
        print(f"Database change audit logging failed: {str(e)}")


def log_authentication_event(
    db: Session,
    user_id: Optional[int],
    action: str,  # LOGIN, LOGOUT, FAILED_LOGIN
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None,
):
    """Специализированная функция для логирования событий аутентификации"""
    try:
        log_user_action(
            db=db,
            user_id=user_id,
            action=action,
            table_name="users",
            record_id=user_id,
            old_values=None,
            new_values=additional_info,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        print(f"Authentication audit logging failed: {str(e)}")
