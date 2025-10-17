"""
Pydantic модели для запланированных задач
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field, validator


class ScheduledJobBase(BaseModel):
    """Базовая модель для запланированной задачи"""
    name: str = Field(..., description="Название задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    job_type: str = Field(..., description="Тип задачи: cron, interval, date")
    
    # Параметры расписания
    cron_expression: Optional[str] = Field(None, description="Cron выражение (минута час день месяц день_недели)")
    interval_seconds: Optional[int] = Field(None, description="Интервал в секундах")
    scheduled_time: Optional[datetime] = Field(None, description="Время для однократного выполнения")
    
    # Параметры вызова функции
    function_path: str = Field(..., description="Путь к функции (app.api.module.controllers:function_name)")
    function_params: Optional[Dict[str, Any]] = Field(None, description="Параметры для вызова функции")
    
    is_active: bool = Field(True, description="Активна ли задача")
    
    @validator('job_type')
    def validate_job_type(cls, v):
        if v not in ['cron', 'interval', 'date']:
            raise ValueError('job_type must be one of: cron, interval, date')
        return v
        
    @validator('cron_expression')
    def validate_cron(cls, v, values):
        if values.get('job_type') == 'cron':
            if not v:
                raise ValueError('cron_expression is required for cron jobs')
            parts = v.split()
            if len(parts) != 5:
                raise ValueError('cron_expression must have 5 parts: minute hour day month day_of_week')
        return v
        
    @validator('interval_seconds')
    def validate_interval(cls, v, values):
        if values.get('job_type') == 'interval':
            if not v or v <= 0:
                raise ValueError('interval_seconds must be positive for interval jobs')
        return v
        
    @validator('scheduled_time')
    def validate_scheduled_time(cls, v, values):
        if values.get('job_type') == 'date' and not v:
            raise ValueError('scheduled_time is required for date jobs')
        return v


class ScheduledJobCreate(ScheduledJobBase):
    """Модель для создания задачи"""
    pass


class ScheduledJobUpdate(BaseModel):
    """Модель для обновления задачи"""
    name: Optional[str] = None
    description: Optional[str] = None
    job_type: Optional[str] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    function_path: Optional[str] = None
    function_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ScheduledJobOut(ScheduledJobBase):
    """Модель для вывода задачи"""
    id: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: int
    
    model_config = ConfigDict(from_attributes=True)


class ScheduledJobStats(BaseModel):
    """Статистика по задачам"""
    total_jobs: int
    active_jobs: int
    inactive_jobs: int
    total_runs: int
    total_errors: int
    jobs_by_type: Dict[str, int]


class JobExecutionResult(BaseModel):
    """Результат выполнения задачи"""
    success: bool
    message: str
    job_id: int
    executed_at: datetime


class JobTemplate(BaseModel):
    """Шаблон для быстрого создания задачи"""
    name: str
    description: str
    job_type: str
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    function_path: str
    function_params: Optional[Dict[str, Any]] = None
    example_description: str


# Предустановленные шаблоны задач
JOB_TEMPLATES: List[JobTemplate] = [
    JobTemplate(
        name="Синхронизация Vendista (каждый час)",
        description="Автоматическая синхронизация данных из Vendista API каждый час",
        job_type="cron",
        cron_expression="0 * * * *",
        function_path="app.api.terminal_operations.controllers:sync_vendista_data",
        function_params={"sync_data": {"sync_date": "today"}},
        example_description="Выполняется каждый час в начале часа (00 минут)"
    ),
    JobTemplate(
        name="Закрытие операций терминалов (ежедневно)",
        description="Автоматическое закрытие операций терминалов каждый день в 23:00",
        job_type="cron",
        cron_expression="0 23 * * *",
        function_path="app.api.terminal_operations.controllers:close_day_operations",
        function_params={"close_data": {"operation_date": "today", "closed_by": 1}},
        example_description="Выполняется каждый день в 23:00. Закрывает все открытые операции за текущий день."
    ),
    JobTemplate(
        name="Генерация отчетов (ежедневно)",
        description="Автоматическая генерация отчетов каждый день в 01:00",
        job_type="cron",
        cron_expression="0 1 * * *",
        function_path="app.api.reports.controllers:compute_and_store_reports",
        function_params={},
        example_description="Выполняется каждый день в 01:00"
    ),
]

