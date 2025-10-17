from pydantic import BaseModel, ConfigDict, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ApiTokenScope(str, Enum):
    """Области доступа для API токенов"""
    # Основные ресурсы
    machines = "machines"
    terminals = "terminals"
    users = "users"
    accounts = "accounts"
    counterparties = "counterparties"
    owners = "owners"
    
    # Операции
    transactions = "transactions"
    inventory_movements = "inventory_movements"
    terminal_operations = "terminal_operations"
    
    # Данные и отчеты
    reports = "reports"
    charts = "charts"
    items = "items"
    warehouses = "warehouses"
    
    # Справочники
    item_categories = "item_categories"
    transaction_categories = "transaction_categories"
    phones = "phones"
    
    # Система
    audit = "audit"
    documents = "documents"
    info_cards = "info_cards"


class ApiTokenPermission(str, Enum):
    """Разрешения для API токенов"""
    # Чтение
    read = "read"
    
    # Запись
    write = "write"
    create = "create"
    update = "update"
    delete = "delete"
    
    # Специальные разрешения
    export = "export"
    import_ = "import"
    admin = "admin"


class ApiTokenCreateRequest(BaseModel):
    """Запрос на создание API токена"""
    name: str
    description: Optional[str] = None
    permissions: List[str] = []  # Формат: ["read:machines", "write:reports"]
    scopes: Optional[List[ApiTokenScope]] = None
    ip_whitelist: Optional[List[str] | str] = None
    rate_limit: Optional[int] = 1000
    expires_at: Optional[datetime] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Название токена должно содержать минимум 3 символа')
        return v.strip()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """Проверяет формат разрешений"""
        valid_permissions = []
        for perm in v:
            if ':' not in perm:
                raise ValueError(f'Неверный формат разрешения: {perm}. Ожидается "action:scope"')
            
            action, scope = perm.split(':', 1)
            
            # Проверяем действие
            try:
                ApiTokenPermission(action)
            except ValueError:
                raise ValueError(f'Неверное действие: {action}')
            
            # Проверяем область (scope может быть как из enum, так и произвольным)
            valid_permissions.append(perm)
        
        return valid_permissions
    
    @validator('ip_whitelist')
    def validate_ip_whitelist(cls, v):
        """Проверяет IP адреса"""
        if v is None or v == []:
            return []
        
        # Если передана строка, разбиваем её на список
        if isinstance(v, str):
            if not v.strip():
                return []
            v = [ip.strip() for ip in v.split('\n') if ip.strip()]
        
        # Проверяем каждый IP адрес
        import ipaddress
        for ip in v:
            try:
                ipaddress.ip_address(ip.strip())
            except ValueError:
                raise ValueError(f'Неверный IP адрес: {ip}')
        
        return [ip.strip() for ip in v]


class ApiTokenUpdateRequest(BaseModel):
    """Запрос на обновление API токена"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    scopes: Optional[List[ApiTokenScope]] = None
    ip_whitelist: Optional[List[str] | str] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    
    @validator('ip_whitelist')
    def validate_ip_whitelist(cls, v):
        """Проверяет IP адреса"""
        if v is None or v == []:
            return []
        
        # Если передана строка, разбиваем её на список
        if isinstance(v, str):
            if not v.strip():
                return []
            v = [ip.strip() for ip in v.split('\n') if ip.strip()]
        
        # Проверяем каждый IP адрес
        import ipaddress
        for ip in v:
            try:
                ipaddress.ip_address(ip.strip())
            except ValueError:
                raise ValueError(f'Неверный IP адрес: {ip}')
        
        return [ip.strip() for ip in v]


class ApiTokenResponse(BaseModel):
    """Ответ с информацией об API токене"""
    id: int
    name: str
    description: Optional[str] = None
    token_prefix: str  # Первые 8 символов токена для идентификации
    permissions: List[str] = []
    scopes: Optional[List[str]] = None
    ip_whitelist: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    creator_username: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ApiTokenCreateResponse(BaseModel):
    """Ответ при создании токена (включает полный токен)"""
    token_info: ApiTokenResponse
    token: str  # Полный токен - показывается только один раз!
    
    model_config = ConfigDict(from_attributes=True)


class ApiTokenStats(BaseModel):
    """Статистика по API токенам"""
    total_tokens: int
    active_tokens: int
    expired_tokens: int
    inactive_tokens: int
    total_usage: int
    tokens_by_user: Dict[str, int]
    most_used_tokens: List[Dict[str, Any]]
    recent_usage: List[Dict[str, Any]]


class ApiTokenFilter(BaseModel):
    """Фильтр для поиска API токенов"""
    name_contains: Optional[str] = None
    created_by: Optional[int] = None
    is_active: Optional[bool] = None
    has_scope: Optional[ApiTokenScope] = None
    expires_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    last_used_before: Optional[datetime] = None
    last_used_after: Optional[datetime] = None


class ApiTokenUsageLog(BaseModel):
    """Лог использования API токена"""
    id: int
    token_id: int
    token_name: str
    endpoint: str
    method: str
    status_code: int
    ip_address: str
    user_agent: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    used_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Предустановленные наборы разрешений
PERMISSION_PRESETS = {
    "readonly": [
        "read:machines", "read:terminals", "read:accounts", "read:counterparties",
        "read:transactions", "read:reports", "read:items", "read:warehouses"
    ],
    "reports_only": [
        "read:reports", "read:charts", "read:transactions", "read:machines",
        "read:terminals", "export:reports"
    ],
    "machines_management": [
        "read:machines", "write:machines", "update:machines",
        "read:items", "read:warehouses", "read:inventory_movements"
    ],
    "financial_management": [
        "read:accounts", "write:accounts", "read:transactions", "write:transactions",
        "read:counterparties", "write:counterparties", "read:reports"
    ],
    "admin": [
        "read:*", "write:*", "create:*", "update:*", "delete:*", "admin:*"
    ]
}
