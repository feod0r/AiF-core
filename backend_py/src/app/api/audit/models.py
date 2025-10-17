from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class UserSimple(BaseModel):
    """Упрощенная модель пользователя для аудита"""
    id: int
    username: str
    full_name: Optional[str] = None
    role: Optional[Dict[str, str]] = None
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogOut(BaseModel):
    """Модель для вывода аудит-лога"""
    id: int
    user: Optional[UserSimple] = None
    action: str
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogCreate(BaseModel):
    """Модель для создания аудит-лога"""
    user_id: Optional[int] = None
    action: str = Field(..., description="Действие (CREATE, UPDATE, DELETE, LOGIN, etc.)")
    table_name: Optional[str] = Field(None, description="Название таблицы")
    record_id: Optional[int] = Field(None, description="ID записи")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Старые значения")
    new_values: Optional[Dict[str, Any]] = Field(None, description="Новые значения")
    ip_address: Optional[str] = Field(None, description="IP адрес")
    user_agent: Optional[str] = Field(None, description="User-Agent")
    endpoint: Optional[str] = Field(None, description="API эндпоинт")
    method: Optional[str] = Field(None, description="HTTP метод")
    request_id: Optional[str] = Field(None, description="ID запроса")
    duration_ms: Optional[int] = Field(None, description="Длительность в мс")
    status_code: Optional[int] = Field(None, description="HTTP статус код")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")


class AuditLogFilter(BaseModel):
    """Фильтры для поиска аудит-логов"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    table_name: Optional[str] = None
    date_from: Optional[str] = Field(None, description="Дата от (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Дата до (YYYY-MM-DD)")
    search: Optional[str] = Field(None, description="Поиск по IP, User-Agent, endpoint")
    page: int = Field(1, ge=1, description="Номер страницы")
    limit: int = Field(50, ge=1, le=1000, description="Количество записей на странице")
    order_by: str = Field("created_at", description="Поле для сортировки")
    order_direction: str = Field("desc", pattern="^(asc|desc)$", description="Направление сортировки")


class AuditActionStats(BaseModel):
    """Статистика по действиям"""
    action: str
    count: int


class AuditUserStats(BaseModel):
    """Статистика по пользователям"""
    user: Optional[UserSimple] = None
    count: int


class AuditTableStats(BaseModel):
    """Статистика по таблицам"""
    table_name: str
    count: int


class AuditHourlyStats(BaseModel):
    """Почасовая статистика"""
    hour: str
    count: int


class AuditStatistics(BaseModel):
    """Общая статистика аудита"""
    total_count: int
    action_stats: List[AuditActionStats]
    user_stats: List[AuditUserStats]
    table_stats: List[AuditTableStats]
    hourly_stats: List[AuditHourlyStats]


class AuditLogsList(BaseModel):
    """Список аудит-логов с пагинацией"""
    logs: List[AuditLogOut]
    pagination: Dict[str, Any]


class AuditResponse(BaseModel):
    """Общий ответ API аудита"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None


class CleanupResult(BaseModel):
    """Результат очистки старых логов"""
    deleted_count: int
    cutoff_date: datetime
    message: str
