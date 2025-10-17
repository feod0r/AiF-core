"""
Планировщик задач для автоматизации рутинных операций
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlalchemy.orm import Session

from app.external.sqlalchemy.models import ScheduledJob, Phone, Rent, MachineStock, TelegramBot
from app.external.sqlalchemy.session import get_db
from app.api.telegram.controllers import send_notification_system


class TaskScheduler:
    """Планировщик задач для автоматизации"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
        self._http_client: Optional[httpx.AsyncClient] = None
        
    async def get_http_client(self) -> httpx.AsyncClient:
        """Получить HTTP клиент для выполнения запросов"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
        
    async def start(self):
        """Запустить планировщик"""
        # Добавляем встроенные задачи
        await self._add_built_in_jobs()
        
        # Загружаем задачи из базы данных
        await self._load_jobs_from_db()
        
        # Запускаем планировщик
        self.scheduler.start()
        logger.info("Task scheduler started successfully")
        
    async def shutdown(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()
        if self._http_client:
            await self._http_client.aclose()
        logger.info("Task scheduler stopped")
        
    async def _add_built_in_jobs(self):
        """Добавить встроенные задачи"""
        # Создаем встроенные задачи в БД, если их еще нет
        await self._create_builtin_jobs_in_db()
        
        logger.info("Built-in scheduled jobs added")
        
    async def _create_builtin_jobs_in_db(self):
        """Создать встроенные задачи в базе данных"""
        try:
            db = next(get_db())
            
            # Список встроенных задач
            builtin_jobs = [
                {
                    'name': '🔔 Проверка оплаты телефонов (встроенная)',
                    'description': 'Автоматическая проверка и отправка уведомлений об оплате телефонов каждый день в 06:00',
                    'job_type': 'cron',
                    'cron_expression': '0 6 * * *',
                    'function_path': 'app.services.scheduler:_check_phone_payments_wrapper',
                    'function_params': {},
                },
                {
                    'name': '🔔 Проверка оплаты аренды (встроенная)',
                    'description': 'Автоматическая проверка и отправка уведомлений об оплате аренды каждый день в 06:00',
                    'job_type': 'cron',
                    'cron_expression': '0 6 * * *',
                    'function_path': 'app.services.scheduler:_check_rent_payments_wrapper',
                    'function_params': {},
                },
                {
                    'name': '🔔 Проверка низких остатков (встроенная)',
                    'description': 'Автоматическая проверка низких остатков игрушек и отправка уведомлений каждый день в 06:00',
                    'job_type': 'cron',
                    'cron_expression': '0 6 * * *',
                    'function_path': 'app.services.scheduler:_check_low_stock_wrapper',
                    'function_params': {},
                },
            ]
            
            # Проверяем и создаем задачи
            for job_data in builtin_jobs:
                existing = db.query(ScheduledJob).filter(
                    ScheduledJob.name == job_data['name']
                ).first()
                
                if not existing:
                    # Создаем задачу с ID системного пользователя (1)
                    job = ScheduledJob(
                        **job_data,
                        created_by=1,  # Системный пользователь
                        is_active=True,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.add(job)
                    logger.info(f"Created built-in job: {job_data['name']}")
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Error creating built-in jobs in DB: {e}")
            if db:
                db.close()
        
    async def _check_phone_payments(self):
        """Проверить оплату телефонов и отправить уведомления"""
        logger.info("Running phone payments check...")
        
        try:
            db = next(get_db())
            current_day = datetime.now(timezone.utc).day
            
            # Получаем все активные телефоны с текущим днем оплаты
            phones = db.query(Phone).filter(
                Phone.pay_date == current_day,
                Phone.end_date > datetime.now(timezone.utc)
            ).all()
            
            if not phones:
                logger.info(f"No phone payments due on day {current_day}")
                return
                
            # Формируем сообщение
            message_lines = [
                f"💳 <b>Напоминание об оплате телефонов</b>",
                f"",
                f"Сегодня ({current_day} число) необходимо оплатить следующие телефоны:",
                ""
            ]
            
            total_amount = 0
            for phone in phones:
                message_lines.append(
                    f"📱 {phone.phone}: <b>{phone.amount} ₽</b>"
                )
                if phone.details:
                    message_lines.append(f"   └ {phone.details}")
                total_amount += float(phone.amount)
                
            message_lines.append("")
            message_lines.append(f"💰 <b>Итого: {total_amount:.2f} ₽</b>")
            
            message = "\n".join(message_lines)
            
            # Отправляем уведомление через Telegram
            await self._send_telegram_notification(
                db=db,
                notification_type="payment_due_phone",
                title="Напоминание об оплате телефонов",
                message=message,
                priority="high"
            )
            
            logger.info(f"Phone payment notifications sent for {len(phones)} phones")
            
        except Exception as e:
            logger.error(f"Error checking phone payments: {e}")
        finally:
            db.close()
            
    async def _check_rent_payments(self):
        """Проверить оплату аренды и отправить уведомления"""
        logger.info("Running rent payments check...")
        
        try:
            db = next(get_db())
            current_day = datetime.now(timezone.utc).day
            
            # Получаем все активные аренды с текущим днем оплаты
            rents = db.query(Rent).filter(
                Rent.pay_date == current_day,
                Rent.end_date > datetime.now(timezone.utc)
            ).all()
            
            if not rents:
                logger.info(f"No rent payments due on day {current_day}")
                return
                
            # Формируем сообщение
            message_lines = [
                f"🏠 <b>Напоминание об оплате аренды</b>",
                f"",
                f"Сегодня ({current_day} число) необходимо оплатить аренду:",
                ""
            ]
            
            total_amount = 0
            for rent in rents:
                payer_info = f" ({rent.payer.name})" if rent.payer else ""
                message_lines.append(
                    f"📍 {rent.location}{payer_info}: <b>{rent.amount} ₽</b>"
                )
                if rent.details:
                    message_lines.append(f"   └ {rent.details}")
                total_amount += float(rent.amount)
                
            message_lines.append("")
            message_lines.append(f"💰 <b>Итого: {total_amount:.2f} ₽</b>")
            
            message = "\n".join(message_lines)
            
            # Отправляем уведомление через Telegram
            await self._send_telegram_notification(
                db=db,
                notification_type="payment_due_rent",
                title="Напоминание об оплате аренды",
                message=message,
                priority="high"
            )
            
            logger.info(f"Rent payment notifications sent for {len(rents)} locations")
            
        except Exception as e:
            logger.error(f"Error checking rent payments: {e}")
        finally:
            db.close()
            
    async def _check_low_stock(self):
        """Проверить низкие остатки игрушек и отправить уведомления"""
        logger.info("Running low stock check...")
        
        try:
            db = next(get_db())
            
            # Получаем все остатки со связанными товарами
            all_stocks = db.query(MachineStock).join(MachineStock.item).all()
            
            # Фильтруем вручную, учитывая min_quantity из machine_stocks 
            # или min_stock из items, если min_quantity не задан
            low_stocks = []      # Критически низкие остатки
            warning_stocks = []  # Близкие к минимуму (предупреждение)
            
            for stock in all_stocks:
                # Используем min_quantity из machine_stocks, если задан (> 0),
                # иначе используем min_stock из items
                min_threshold = stock.min_quantity if stock.min_quantity > 0 else (stock.item.min_stock if stock.item else 0)
                
                if min_threshold <= 0:  # Пропускаем товары без настроенного минимума
                    continue
                
                # Приводим к float для вычислений
                min_threshold_float = float(min_threshold)
                quantity_float = float(stock.quantity)
                
                # Критически низкий остаток
                if quantity_float <= min_threshold_float:
                    low_stocks.append(stock)
                # Близко к минимуму (в пределах 20% от минимума)
                elif quantity_float <= min_threshold_float * 1.2:
                    warning_stocks.append(stock)
            
            if not low_stocks and not warning_stocks:
                logger.info("No low stock items found")
                return
                
            # Группируем критически низкие остатки по автоматам
            critical_machines = {}
            for stock in low_stocks:
                machine_id = stock.machine_id
                if machine_id not in critical_machines:
                    critical_machines[machine_id] = {
                        'machine': stock.machine,
                        'items': []
                    }
                critical_machines[machine_id]['items'].append(stock)
            
            # Группируем предупреждения по автоматам
            warning_machines = {}
            for stock in warning_stocks:
                machine_id = stock.machine_id
                if machine_id not in warning_machines:
                    warning_machines[machine_id] = {
                        'machine': stock.machine,
                        'items': []
                    }
                warning_machines[machine_id]['items'].append(stock)
            
            # Формируем сообщение
            message_lines = []
            
            # Критически низкие остатки
            if critical_machines:
                message_lines.extend([
                    f"🔴 <b>КРИТИЧЕСКИ НИЗКИЕ ОСТАТКИ</b>",
                    f"",
                    f"В следующих автоматах заканчиваются игрушки:",
                    ""
                ])
                
                critical_items = 0
                for machine_id, data in critical_machines.items():
                    machine = data['machine']
                    items = data['items']
                    
                    machine_name = machine.name if machine else f"Автомат #{machine_id}"
                    message_lines.append(f"🎰 <b>{machine_name}</b>")
                    
                    for stock in items:
                        item_name = stock.item.name if stock.item else f"Товар #{stock.item_id}"
                        quantity = float(stock.quantity)
                        
                        # Определяем, какой минимальный порог используется
                        min_qty = float(stock.min_quantity) if stock.min_quantity > 0 else float(stock.item.min_stock if stock.item else 0)
                        min_source = "автомат" if stock.min_quantity > 0 else "товар"
                        
                        message_lines.append(
                            f"   🧸 {item_name}: <b>{quantity}</b> шт. (мин: {min_qty}, источник: {min_source})"
                        )
                        critical_items += 1
                    
                    message_lines.append("")
                
                message_lines.extend([
                    f"📊 <b>Критических позиций: {critical_items}</b>",
                    f"🏪 <b>Автоматов требует срочного пополнения: {len(critical_machines)}</b>",
                    ""
                ])
            
            # Предупреждения о близких к минимуму остатках
            if warning_machines:
                if critical_machines:
                    message_lines.append("🟡 <b>ПРЕДУПРЕЖДЕНИЯ</b>")
                else:
                    message_lines.extend([
                        f"🟡 <b>ПРЕДУПРЕЖДЕНИЯ О НИЗКИХ ОСТАТКАХ</b>",
                        f"",
                        f"В следующих автоматах остатки близки к минимуму:",
                        ""
                    ])
                
                warning_items = 0
                for machine_id, data in warning_machines.items():
                    machine = data['machine']
                    items = data['items']
                    
                    machine_name = machine.name if machine else f"Автомат #{machine_id}"
                    message_lines.append(f"🎰 <b>{machine_name}</b>")
                    
                    for stock in items:
                        item_name = stock.item.name if stock.item else f"Товар #{stock.item_id}"
                        quantity = float(stock.quantity)
                        
                        # Определяем, какой минимальный порог используется
                        min_qty = float(stock.min_quantity) if stock.min_quantity > 0 else float(stock.item.min_stock if stock.item else 0)
                        min_source = "автомат" if stock.min_quantity > 0 else "товар"
                        
                        # Вычисляем процент от минимума
                        percentage = (quantity / min_qty * 100) if min_qty > 0 else 0
                        
                        message_lines.append(
                            f"   🧸 {item_name}: <b>{quantity}</b> шт. (мин: {min_qty}, {percentage:.0f}%, источник: {min_source})"
                        )
                        warning_items += 1
                    
                    message_lines.append("")
                
                message_lines.extend([
                    f"📊 <b>Позиций с предупреждением: {warning_items}</b>",
                    f"🏪 <b>Автоматов рекомендуется пополнить: {len(warning_machines)}</b>"
                ])
            
            message = "\n".join(message_lines)
            
            # Отправляем уведомление через Telegram
            await self._send_telegram_notification(
                db=db,
                notification_type="low_stock",
                title="Предупреждение о низких остатках",
                message=message,
                priority="high"
            )
            
            total_critical = sum(len(data['items']) for data in critical_machines.values())
            total_warnings = sum(len(data['items']) for data in warning_machines.values())
            
            logger.info(
                f"Low stock notifications sent: {total_critical} critical items in {len(critical_machines)} machines, "
                f"{total_warnings} warning items in {len(warning_machines)} machines"
            )
            
        except Exception as e:
            logger.error(f"Error checking low stock: {e}")
        finally:
            db.close()
            
    async def _send_telegram_notification(
        self, 
        db: Session, 
        notification_type: str,
        title: str,
        message: str,
        priority: str = "medium"
    ):
        """Отправить уведомление в Telegram через централизованное API"""
        try:
            result = await send_notification_system(
                db=db,
                notification_type=notification_type,
                message=message,
                title=title,
                priority=priority,
                created_by_id=1  # Системный пользователь
            )
            
            if result['success']:
                logger.info(
                    f"Notification sent: type={notification_type}, "
                    f"sent_to={result['sent_to']}, failed={result['failed']}"
                )
            else:
                logger.warning(f"Notification not sent: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
                
    async def _load_jobs_from_db(self):
        """Загрузить запланированные задачи из базы данных"""
        try:
            db = next(get_db())
            
            # Получаем все активные задачи
            jobs = db.query(ScheduledJob).filter(ScheduledJob.is_active == True).all()
            
            for job in jobs:
                try:
                    await self._add_job_from_model(job)
                    logger.info(f"Loaded scheduled job: {job.name}")
                except Exception as e:
                    logger.error(f"Error loading job {job.name}: {e}")
                    
            db.close()
            
        except Exception as e:
            logger.error(f"Error loading jobs from database: {e}")
            
    async def _add_job_from_model(self, job: ScheduledJob):
        """Добавить задачу из модели базы данных"""
        # Определяем trigger на основе типа задачи
        trigger = None
        
        if job.job_type == 'cron' and job.cron_expression:
            # Парсим cron выражение (формат: минута час день месяц день_недели)
            parts = job.cron_expression.split()
            if len(parts) == 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
        elif job.job_type == 'interval' and job.interval_seconds:
            trigger = IntervalTrigger(seconds=job.interval_seconds)
        elif job.job_type == 'date' and job.scheduled_time:
            # Для однократных задач используем date trigger
            from apscheduler.triggers.date import DateTrigger
            trigger = DateTrigger(run_date=job.scheduled_time)
            
        if trigger:
            self.scheduler.add_job(
                self._execute_job,
                trigger,
                args=[job.id],
                id=f"job_{job.id}",
                name=job.name,
                replace_existing=True
            )
            
    async def _execute_job(self, job_id: int):
        """Выполнить задачу через прямой вызов функции"""
        logger.info(f"Executing job {job_id}...")
        
        db = None
        try:
            db = next(get_db())
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            
            if not job or not job.is_active:
                logger.warning(f"Job {job_id} not found or inactive")
                return
                
            # Парсим путь к функции (формат: module.path:function_name)
            try:
                module_path, function_name = job.function_path.split(':')
            except ValueError:
                raise ValueError(f"Invalid function_path format. Expected 'module.path:function_name', got '{job.function_path}'")
            
            # Импортируем модуль и получаем функцию
            try:
                import importlib
                module = importlib.import_module(module_path)
                func = getattr(module, function_name)
            except (ImportError, AttributeError) as e:
                raise ImportError(f"Cannot import {function_name} from {module_path}: {e}")
            
            # Подготавливаем параметры
            params = job.function_params or {}
            
            # Рекурсивная функция для замены "today" на текущую дату
            def replace_today(obj):
                from datetime import date as date_type
                if isinstance(obj, dict):
                    return {k: replace_today(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [replace_today(item) for item in obj]
                elif obj == "today":
                    return date_type.today()
                return obj
            
            params = replace_today(params)
            
            # Специальная обработка для close_data - преобразуем в объект CloseDayRequest
            if 'close_data' in params and isinstance(params['close_data'], dict):
                from app.api.terminal_operations.models import CloseDayRequest
                close_data_dict = params['close_data']
                params['close_data'] = CloseDayRequest(**close_data_dict)
                
            # Специальная обработка для sync_data - преобразуем в объект VendistaSyncRequest
            if 'sync_data' in params and isinstance(params['sync_data'], dict):
                from app.api.terminal_operations.models import VendistaSyncRequest
                sync_data_dict = params['sync_data']
                params['sync_data'] = VendistaSyncRequest(**sync_data_dict)
                
            # Добавляем db в параметры, если функция её требует
            import inspect
            sig = inspect.signature(func)
            if 'db' in sig.parameters:
                params['db'] = db
                
            # Выполняем функцию
            try:
                if inspect.iscoroutinefunction(func):
                    result = await func(**params)
                else:
                    result = func(**params)
                    
                # Обновляем статистику задачи
                job.last_run = datetime.now(timezone.utc)
                job.run_count += 1
                job.last_error = None
                
                logger.info(f"Job {job_id} ({job.name}) completed successfully. Result: {result}")
                    
            except Exception as e:
                job.error_count += 1
                job.last_error = str(e)[:500]
                logger.error(f"Job {job_id} ({job.name}) failed with exception: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
            db.commit()
            
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            if db:
                db.close()
            
    async def reload_jobs(self):
        """Перезагрузить задачи из базы данных"""
        # Удаляем все пользовательские задачи (кроме встроенных)
        for job in self.scheduler.get_jobs():
            if job.id.startswith('job_'):
                job.remove()
                
        # Загружаем задачи заново
        await self._load_jobs_from_db()
        logger.info("Scheduled jobs reloaded")
        
    async def add_or_update_job(self, job_id: int):
        """Добавить или обновить задачу"""
        try:
            db = next(get_db())
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            
            if not job:
                logger.warning(f"Job {job_id} not found")
                return
                
            # Удаляем существующую задачу
            if self.scheduler.get_job(f"job_{job_id}"):
                self.scheduler.remove_job(f"job_{job_id}")
                
            # Добавляем задачу заново, если она активна
            if job.is_active:
                await self._add_job_from_model(job)
                logger.info(f"Job {job_id} added/updated successfully")
            else:
                logger.info(f"Job {job_id} is inactive, not adding to scheduler")
                
            db.close()
            
        except Exception as e:
            logger.error(f"Error adding/updating job {job_id}: {e}")
            
    async def remove_job(self, job_id: int):
        """Удалить задачу из планировщика"""
        try:
            if self.scheduler.get_job(f"job_{job_id}"):
                self.scheduler.remove_job(f"job_{job_id}")
                logger.info(f"Job {job_id} removed from scheduler")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            
    def get_all_jobs_info(self):
        """Получить информацию о всех задачах в планировщике"""
        jobs_info = []
        
        for job in self.scheduler.get_jobs():
            # Определяем, является ли задача встроенной
            is_builtin = not job.id.startswith('job_')
            
            # Получаем информацию о следующем запуске
            next_run_time = job.next_run_time
            
            # Формируем информацию о задаче
            job_info = {
                'id': job.id,
                'name': job.name,
                'next_run': next_run_time.isoformat() if next_run_time else None,
                'is_builtin': is_builtin,
                'trigger': str(job.trigger),
            }
            
            jobs_info.append(job_info)
            
        return jobs_info


# Wrapper функции для встроенных задач (чтобы их можно было вызвать извне)
async def _check_phone_payments_wrapper():
    """Wrapper для проверки оплаты телефонов"""
    await task_scheduler._check_phone_payments()


async def _check_rent_payments_wrapper():
    """Wrapper для проверки оплаты аренды"""
    await task_scheduler._check_rent_payments()


async def _check_low_stock_wrapper():
    """Wrapper для проверки низких остатков"""
    await task_scheduler._check_low_stock()


# Глобальный экземпляр планировщика
task_scheduler = TaskScheduler()

