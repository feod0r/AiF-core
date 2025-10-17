from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..auth.dependencies import get_current_user
from ...external.sqlalchemy.models import User
from ...external.sqlalchemy.session import get_db
from .controllers import TelegramController
from .models import (
    TelegramBotCreate, TelegramBotUpdate, TelegramBot,
    SendNotificationRequest, SendNotificationResponse, TestMessageRequest,
    NotificationHistory, TelegramBotStats, NotificationStats
)

router = APIRouter(prefix="/telegram", tags=["telegram"])

def get_telegram_controller(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TelegramController:
    return TelegramController(db, current_user)

# Bot management endpoints
@router.post("/bots", response_model=TelegramBot)
async def create_bot(
    bot_data: TelegramBotCreate,
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Создает нового Telegram бота"""
    return controller.create_bot(bot_data)

@router.get("/bots", response_model=List[TelegramBot])
async def list_bots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Получает список всех Telegram ботов"""
    return controller.get_bots(skip=skip, limit=limit)

@router.get("/bots/{bot_id}", response_model=TelegramBot)
async def get_bot(
    bot_id: int,
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Получает Telegram бота по ID"""
    return controller.get_bot(bot_id)

@router.put("/bots/{bot_id}", response_model=TelegramBot)
async def update_bot(
    bot_id: int,
    bot_data: TelegramBotUpdate,
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Обновляет Telegram бота"""
    return controller.update_bot(bot_id, bot_data)

@router.delete("/bots/{bot_id}")
async def delete_bot(
    bot_id: int,
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Удаляет Telegram бота"""
    controller.delete_bot(bot_id)
    return {"message": "Бот успешно удален"}

@router.post("/bots/{bot_id}/activate", response_model=TelegramBot)
async def activate_bot(
    bot_id: int,
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Активирует Telegram бота"""
    return controller.activate_bot(bot_id)

@router.post("/bots/{bot_id}/deactivate", response_model=TelegramBot)
async def deactivate_bot(
    bot_id: int,
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Деактивирует Telegram бота"""
    return controller.deactivate_bot(bot_id)

@router.post("/bots/{bot_id}/test")
async def test_bot(
    bot_id: int,
    test_data: TestMessageRequest,
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Тестирует Telegram бота отправкой сообщения"""
    return await controller.test_bot(bot_id, test_data.message)

# Notification endpoints
@router.post("/notifications/send", response_model=SendNotificationResponse)
async def send_notification(
    notification_data: SendNotificationRequest,
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Отправляет уведомление во все подходящие чаты"""
    return await controller.send_notification(notification_data)

@router.get("/notifications/history", response_model=List[NotificationHistory])
async def get_notification_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Получает историю уведомлений"""
    return controller.get_notification_history(skip=skip, limit=limit)

@router.get("/notifications/types")
async def get_notification_types():
    """Получает список доступных типов уведомлений"""
    return [
        {"id": "low_stock", "name": "Низкий остаток игрушек", "category": "inventory"},
        {"id": "payment_due_phone", "name": "День оплаты телефона", "category": "payments"},
        {"id": "payment_due_rent", "name": "День оплаты аренды", "category": "payments"},
        {"id": "machine_error", "name": "Ошибка автомата", "category": "technical"},
        {"id": "daily_report", "name": "Ежедневный отчет", "category": "reports"},
        {"id": "weekly_report", "name": "Еженедельный отчет", "category": "reports"},
        {"id": "monthly_report", "name": "Ежемесячный отчет", "category": "reports"},
        {"id": "custom", "name": "Пользовательское сообщение", "category": "custom"},
    ]

# Statistics endpoints
@router.get("/bots/stats/summary", response_model=TelegramBotStats)
async def get_bot_stats(
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Получает статистику по Telegram ботам"""
    return controller.get_bot_stats()

@router.get("/stats/summary", response_model=NotificationStats)
async def get_notification_stats(
    controller: TelegramController = Depends(get_telegram_controller)
):
    """Получает общую статистику по уведомлениям"""
    return controller.get_notification_stats()
