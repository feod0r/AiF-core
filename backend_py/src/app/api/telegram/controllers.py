import httpx
import asyncio
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, Depends
from ..auth.dependencies import get_current_user
from ...external.sqlalchemy.models import TelegramBot, NotificationHistory, User
from ...external.sqlalchemy.session import get_db
from .models import (
    TelegramBotCreate,
    TelegramBotUpdate,
    TelegramBot as TelegramBotModel,
    SendNotificationRequest,
    SendNotificationResponse,
    TestMessageRequest,
    NotificationHistory as NotificationHistoryModel,
    TelegramBotStats,
    NotificationStats,
)

# Telegram Bot API URL
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


async def send_telegram_message(
    bot_token: str, chat_id: str, message: str, parse_mode: str = "HTML"
) -> bool:
    """Отправляет сообщение через Telegram Bot API"""
    try:
        url = TELEGRAM_API_URL.format(token=bot_token)
        data = {"chat_id": chat_id, "text": message, "parse_mode": parse_mode}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=data)
            return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


def format_notification_message(
    title: Optional[str], message: str, priority: str = "medium"
) -> str:
    """Форматирует сообщение для Telegram"""
    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    priority_text = {"high": "ВЫСОКИЙ", "medium": "СРЕДНИЙ", "low": "НИЗКИЙ"}

    formatted_message = ""

    if title:
        formatted_message += f"<b>{title}</b>\n\n"

    formatted_message += f"{priority_emoji.get(priority, '🟡')} <b>Приоритет:</b> {priority_text.get(priority, 'СРЕДНИЙ')}\n"
    formatted_message += (
        f"📅 <b>Дата:</b> {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}\n\n"
    )
    formatted_message += message

    return formatted_message


async def send_notification_system(
    db: Session,
    notification_type: str,
    message: str,
    title: Optional[str] = None,
    priority: str = "medium",
    created_by_id: int = 1,  # Системный пользователь
) -> dict:
    """
    Отправляет уведомление без требования авторизованного пользователя.
    Используется для встроенных системных задач (планировщик).
    """
    # Получаем всех активных ботов и фильтруем в Python
    all_bots = db.query(TelegramBot).filter(TelegramBot.is_active == True).all()
    
    # Фильтруем ботов, которые подписаны на данный тип уведомлений
    bots = [
        bot for bot in all_bots
        if bot.notification_types and notification_type in bot.notification_types
    ]
    
    if not bots:
        return {
            "success": False,
            "sent_to": 0,
            "failed": 0,
            "message": f"No active bots found for notification type: {notification_type}",
        }
    
    # Форматируем сообщение
    formatted_message = format_notification_message(
        title or "Системное уведомление", message, priority
    )
    
    # Отправляем сообщения
    sent_count = 0
    failed_count = 0
    details = []
    
    for bot in bots:
        try:
            success = await send_telegram_message(
                bot.bot_token, bot.chat_id, formatted_message
            )
            if success:
                sent_count += 1
            else:
                failed_count += 1
            
            details.append({
                "bot_id": bot.id,
                "bot_name": bot.name,
                "status": "success" if success else "failed",
            })
        except Exception as e:
            failed_count += 1
            details.append({
                "bot_id": bot.id,
                "bot_name": bot.name,
                "status": "failed",
                "error": str(e),
            })
    
    # Сохраняем в историю
    bot_info = {
        "bot_ids": [bot.id for bot in bots],
        "bot_names": [bot.name for bot in bots],
        "details": details,
    }
    
    history = NotificationHistory(
        notification_type=notification_type,
        message=message,
        title=title,
        priority=priority,
        sent_to=sent_count,
        failed=failed_count,
        success=sent_count > 0,
        created_by=created_by_id,
        data=bot_info,
    )
    db.add(history)
    db.commit()
    
    return {
        "success": sent_count > 0,
        "sent_to": sent_count,
        "failed": failed_count,
        "details": details,
    }


class TelegramController:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def create_bot(self, bot_data: TelegramBotCreate) -> TelegramBotModel:
        """Создает нового Telegram бота"""
        db_bot = TelegramBot(
            name=bot_data.name,
            bot_token=bot_data.bot_token,
            chat_id=bot_data.chat_id,
            notification_types=bot_data.notification_types,
            description=bot_data.description,
            is_active=bot_data.is_active,
            created_by=self.current_user.id,
        )

        self.db.add(db_bot)
        self.db.commit()
        self.db.refresh(db_bot)

        return TelegramBotModel.model_validate(db_bot)

    def get_bots(self, skip: int = 0, limit: int = 100) -> List[TelegramBotModel]:
        """Получает список всех ботов"""
        bots = self.db.query(TelegramBot).offset(skip).limit(limit).all()
        return [TelegramBotModel.model_validate(bot) for bot in bots]

    def get_bot(self, bot_id: int) -> TelegramBotModel:
        """Получает бота по ID"""
        bot = self.db.query(TelegramBot).filter(TelegramBot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Бот не найден")
        return TelegramBotModel.model_validate(bot)

    def update_bot(self, bot_id: int, bot_data: TelegramBotUpdate) -> TelegramBotModel:
        """Обновляет бота"""
        bot = self.db.query(TelegramBot).filter(TelegramBot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Бот не найден")

        update_data = bot_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bot, field, value)

        bot.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(bot)

        return TelegramBotModel.model_validate(bot)

    def delete_bot(self, bot_id: int):
        """Удаляет бота"""
        bot = self.db.query(TelegramBot).filter(TelegramBot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Бот не найден")

        self.db.delete(bot)
        self.db.commit()

    def activate_bot(self, bot_id: int) -> TelegramBotModel:
        """Активирует бота"""
        bot = self.db.query(TelegramBot).filter(TelegramBot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Бот не найден")

        bot.is_active = True
        bot.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(bot)

        return TelegramBotModel.model_validate(bot)

    def deactivate_bot(self, bot_id: int) -> TelegramBotModel:
        """Деактивирует бота"""
        bot = self.db.query(TelegramBot).filter(TelegramBot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Бот не найден")

        bot.is_active = False
        bot.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(bot)

        return TelegramBotModel.model_validate(bot)

    async def test_bot(self, bot_id: int, message: str) -> dict:
        """Тестирует бота отправкой сообщения"""
        bot = self.db.query(TelegramBot).filter(TelegramBot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Бот не найден")

        formatted_message = format_notification_message("Тестовое сообщение", message)
        success = await send_telegram_message(
            bot.bot_token, bot.chat_id, formatted_message
        )

        # Обновляем статус тестирования
        bot.last_test_message_at = datetime.now(timezone.utc)
        bot.test_message_status = "success" if success else "failed"
        self.db.commit()

        return {
            "success": success,
            "message": "Тестовое сообщение отправлено"
            if success
            else "Ошибка отправки",
        }

    async def send_notification(
        self, notification_data: SendNotificationRequest
    ) -> SendNotificationResponse:
        """Отправляет уведомление во все подходящие чаты"""
        # Получаем всех активных ботов и фильтруем в Python
        # (PostgreSQL JSON операторы работают по-разному в разных версиях)
        all_bots = (
            self.db.query(TelegramBot)
            .filter(TelegramBot.is_active == True)
            .all()
        )
        
        # Фильтруем ботов, которые подписаны на данный тип уведомлений
        bots = [
            bot for bot in all_bots
            if bot.notification_types and notification_data.notification_type in bot.notification_types
        ]

        if not bots:
            raise HTTPException(
                status_code=400,
                detail="Нет активных ботов для данного типа уведомлений",
            )

        # Форматируем сообщение
        title = notification_data.title or "Уведомление"
        formatted_message = format_notification_message(
            title, notification_data.message, notification_data.priority
        )

        # Отправляем сообщения
        sent_count = 0
        failed_count = 0
        details = []

        for bot in bots:
            try:
                success = await send_telegram_message(
                    bot.bot_token, bot.chat_id, formatted_message
                )
                if success:
                    sent_count += 1
                else:
                    failed_count += 1

                details.append(
                    {
                        "bot_id": bot.id,
                        "bot_name": bot.name,
                        "status": "success" if success else "failed",
                        "error": None if success else "Ошибка отправки",
                    }
                )
            except Exception as e:
                failed_count += 1
                details.append(
                    {
                        "bot_id": bot.id,
                        "bot_name": bot.name,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        # Сохраняем в историю
        bot_info = {
            "bot_ids": [bot.id for bot in bots],
            "bot_names": [bot.name for bot in bots],
            "details": details,
        }

        history = NotificationHistory(
            notification_type=notification_data.notification_type,
            message=notification_data.message,
            title=notification_data.title,
            priority=notification_data.priority,
            sent_to=sent_count,
            failed=failed_count,
            success=sent_count > 0,
            created_by=self.current_user.id,
            data={**(notification_data.data or {}), **bot_info},
        )
        self.db.add(history)
        self.db.commit()

        return SendNotificationResponse(
            success=sent_count > 0,
            sent_to=sent_count,
            failed=failed_count,
            details=details,
        )

    def get_notification_history(
        self, skip: int = 0, limit: int = 100
    ) -> List[NotificationHistoryModel]:
        """Получает историю уведомлений"""
        history = (
            self.db.query(NotificationHistory)
            .order_by(desc(NotificationHistory.sent_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [NotificationHistoryModel.model_validate(item) for item in history]

    def get_bot_stats(self) -> TelegramBotStats:
        """Получает статистику по ботам"""
        total_bots = self.db.query(func.count(TelegramBot.id)).scalar()
        active_bots = (
            self.db.query(func.count(TelegramBot.id))
            .filter(TelegramBot.is_active == True)
            .scalar()
        )
        inactive_bots = total_bots - active_bots

        # Статистика по типам уведомлений
        bots_by_type = {}
        bots = self.db.query(TelegramBot).all()
        for bot in bots:
            for notification_type in bot.notification_types:
                bots_by_type[notification_type] = (
                    bots_by_type.get(notification_type, 0) + 1
                )

        # Самые активные боты (по количеству упоминаний в истории)
        bot_activity = {}
        history_records = (
            self.db.query(NotificationHistory)
            .filter(NotificationHistory.data.isnot(None))
            .all()
        )

        for record in history_records:
            if record.data and "bot_ids" in record.data:
                for bot_id in record.data["bot_ids"]:
                    bot_activity[bot_id] = bot_activity.get(bot_id, 0) + 1

        # Получаем ботов с их активностью
        most_active_bots = []
        for bot_id, count in sorted(
            bot_activity.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            bot = self.db.query(TelegramBot).filter(TelegramBot.id == bot_id).first()
            if bot:
                most_active_bots.append(
                    {"id": bot.id, "name": bot.name, "notifications_sent": count}
                )

        # Если нет активных ботов, показываем последние протестированные
        if not most_active_bots:
            recent_tested_bots = (
                self.db.query(TelegramBot)
                .filter(TelegramBot.last_test_message_at.isnot(None))
                .order_by(desc(TelegramBot.last_test_message_at))
                .limit(5)
                .all()
            )

            most_active_bots = [
                {"id": bot.id, "name": bot.name, "notifications_sent": 0}
                for bot in recent_tested_bots
            ]

        # Последние сообщения
        recent_messages = (
            self.db.query(NotificationHistory)
            .order_by(desc(NotificationHistory.sent_at))
            .limit(10)
            .all()
        )

        recent_messages_list = []
        for msg in recent_messages:
            bot_names = []
            if msg.data and "bot_names" in msg.data:
                bot_names = msg.data["bot_names"]

            recent_messages_list.append(
                {
                    "id": msg.id,
                    "bot_name": ", ".join(bot_names) if bot_names else "System",
                    "message_type": msg.notification_type,
                    "sent_at": msg.sent_at.isoformat(),
                    "status": "success" if msg.success else "failed",
                }
            )

        return TelegramBotStats(
            total_bots=total_bots,
            active_bots=active_bots,
            inactive_bots=inactive_bots,
            total_notifications_sent=self.db.query(
                func.count(NotificationHistory.id)
            ).scalar(),
            bots_by_type=bots_by_type,
            most_active_bots=most_active_bots,
            recent_messages=recent_messages_list,
        )

    def get_notification_stats(self) -> NotificationStats:
        """Получает статистику по уведомлениям"""
        total_notifications = self.db.query(func.count(NotificationHistory.id)).scalar()
        successful_notifications = (
            self.db.query(func.count(NotificationHistory.id))
            .filter(NotificationHistory.success == True)
            .scalar()
        )
        failed_notifications = total_notifications - successful_notifications
        active_bots = (
            self.db.query(func.count(TelegramBot.id))
            .filter(TelegramBot.is_active == True)
            .scalar()
        )

        # Статистика по типам уведомлений
        notifications_by_type = {}
        type_stats = (
            self.db.query(
                NotificationHistory.notification_type,
                func.count(NotificationHistory.id),
            )
            .group_by(NotificationHistory.notification_type)
            .all()
        )

        for notification_type, count in type_stats:
            notifications_by_type[notification_type] = count

        # Статистика по приоритетам
        notifications_by_priority = {}
        priority_stats = (
            self.db.query(
                NotificationHistory.priority, func.count(NotificationHistory.id)
            )
            .group_by(NotificationHistory.priority)
            .all()
        )

        for priority, count in priority_stats:
            notifications_by_priority[priority] = count

        return NotificationStats(
            total_notifications_sent=total_notifications,
            successful_notifications=successful_notifications,
            failed_notifications=failed_notifications,
            active_bots=active_bots,
            notifications_by_type=notifications_by_type,
            notifications_by_priority=notifications_by_priority,
        )
