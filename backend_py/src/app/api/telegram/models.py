from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    LOW_STOCK = "low_stock"
    PAYMENT_DUE_PHONE = "payment_due_phone"
    PAYMENT_DUE_RENT = "payment_due_rent"
    MACHINE_ERROR = "machine_error"
    DAILY_REPORT = "daily_report"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_REPORT = "monthly_report"
    CUSTOM = "custom"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TelegramBotBase(BaseModel):
    name: str = Field(..., description="Название бота")
    bot_token: str = Field(..., description="Токен бота от BotFather")
    chat_id: str = Field(..., description="ID чата для отправки сообщений")
    notification_types: List[str] = Field(..., description="Типы уведомлений")
    description: Optional[str] = Field(None, description="Описание бота")
    is_active: bool = Field(True, description="Активен ли бот")

class TelegramBotCreate(TelegramBotBase):
    pass

class TelegramBotUpdate(BaseModel):
    name: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    notification_types: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class TelegramBot(TelegramBotBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    creator_username: Optional[str] = None
    last_test_message_at: Optional[datetime] = None
    test_message_status: Optional[str] = None

    class Config:
        from_attributes = True

class SendNotificationRequest(BaseModel):
    notification_type: str = Field(..., description="Тип уведомления")
    message: str = Field(..., description="Текст сообщения")
    title: Optional[str] = Field(None, description="Заголовок сообщения")
    priority: Priority = Field(Priority.MEDIUM, description="Приоритет уведомления")
    data: Optional[dict] = Field(None, description="Дополнительные данные")

class SendNotificationResponse(BaseModel):
    success: bool
    sent_to: int
    failed: int
    details: List[dict]

class TestMessageRequest(BaseModel):
    message: str = Field(..., description="Тестовое сообщение")

class NotificationHistory(BaseModel):
    id: int
    notification_type: str
    message: str
    title: Optional[str]
    priority: str
    sent_to: int
    failed: int
    success: bool
    sent_at: datetime
    created_by: int
    creator_username: Optional[str] = None

    class Config:
        from_attributes = True

class TelegramBotStats(BaseModel):
    total_bots: int
    active_bots: int
    inactive_bots: int
    total_notifications_sent: int
    bots_by_type: dict
    most_active_bots: List[dict]
    recent_messages: List[dict]

class NotificationStats(BaseModel):
    total_notifications_sent: int
    successful_notifications: int
    failed_notifications: int
    active_bots: int
    notifications_by_type: dict
    notifications_by_priority: dict
