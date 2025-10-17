import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from loguru import logger

from app.external.sqlalchemy.models import Base
from app.external.sqlalchemy.session import engine

from .api.accounts.views import router as account_router
from .api.api_tokens.views import router as api_tokens_router
from .api.audit.views import router as audit_router
from .api.auth.views import router as auth_router
from .api.counterparties.views import router as counterparty_router
from .api.documents.views import router as documents_router
from .api.info_cards.views import router as info_cards_router
from .api.inventory_movements.views import router as inventory_movement_router
from .api.item_categories.views import router as item_category_router
from .api.items.views import router as item_router
from .api.machine_stocks.views import router as machine_stock_router
from .api.machines.views import router as machine_router
from .api.monitoring.views import router as monitoring_router
from .api.owners.views import router as owner_router
from .api.phones.views import router as phone_router
from .api.reference_tables.views import router as reference_tables_router
from .api.rent.views import router as rent_router
from .api.reports.views import router as reports_router
from .api.scheduled_jobs.views import router as scheduled_jobs_router
from .api.telegram.views import router as telegram_router
from .api.terminal_operations.views import router as terminal_operations_router
from .api.terminals.views import router as terminal_router
from .api.transaction_categories.views import router as transaction_category_router
from .api.transactions.views import router as transaction_router
from .api.users.views import router as user_router
from .api.warehouse_stocks.views import router as warehouse_stock_router
from .api.warehouses.views import router as warehouse_router
from .app_status import status_router
from .middleware.audit import AuditMiddleware
from .middleware.auth import AuthMiddleware
from .middleware.temp_file_cleanup import TempFileCleanupMiddleware
from .services.scheduler import task_scheduler
from .settings import settings


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Ant Admin API",
        version=os.getenv("APP_VERSION", default="DEV"),
        description="API для системы управления автоматами",
        routes=app.routes,
    )

    # Добавляем схемы безопасности для JWT и API токенов
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT токен для веб-интерфейса. Получите через /api/auth/login",
        },
        "ApiTokenAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "⚠️ ВАЖНО: Введите ПОЛНЫЙ токен с префиксом!\n\nФормат: Token <ваш_api_токен>\nПример: Token abc123def456...\n\n1. Создайте токен в разделе 'API Токены'\n2. Скопируйте полученный токен\n3. Добавьте префикс 'Token ' перед токеном\n4. Вставьте полную строку в поле ниже",
        },
    }

    # Применяем безопасность ко всем эндпоинтам, кроме исключенных
    excluded_paths = {
        "/api/auth/login",
        "/api/auth/register",
        "/api/docs",
        "/api/redoc",
        "/openapi.json",
        "/api/status",
    }

    # Пути, которые не требуют авторизации
    excluded_patterns = [
        "/api/documents/download/"  # Скачивание по временному токену
    ]

    for path, path_data in openapi_schema["paths"].items():
        # Пропускаем исключенные пути
        if path in excluded_paths:
            continue

        # Пропускаем пути по паттернам
        is_excluded = False
        for pattern in excluded_patterns:
            if path.startswith(pattern):
                is_excluded = True
                break

        if is_excluded:
            continue

        for method, method_data in path_data.items():
            if method.upper() != "OPTIONS":  # Пропускаем OPTIONS
                # Применяем оба типа авторизации (OR логика)
                method_data["security"] = [
                    {"BearerAuth": []},  # JWT токен
                    {"ApiTokenAuth": []},  # API токен
                ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="Ant Admin API",
    description="""
# API для системы управления автоматами

## Авторизация

Поддерживаются два типа авторизации:

### 1. JWT Токены (для веб-интерфейса)
- Получите токен через `/api/auth/login`
- Используйте в заголовке: `Authorization: Bearer <jwt_token>`
- Срок действия: ограничен

### 2. API Токены (для программного доступа)
- Создайте токен в разделе "API Токены" веб-интерфейса
- Используйте в заголовке: `Authorization: Token <api_token>`
- Настраиваемые разрешения и ограничения
- Возможность установки срока действия

## Использование в Swagger UI

1. **Для JWT токенов**: 
   - Нажмите "Authorize" и выберите "BearerAuth"
   - Введите JWT токен БЕЗ префикса "Bearer"

2. **Для API токенов**:
   - Нажмите "Authorize" и выберите "ApiTokenAuth"  
   - ⚠️ **ВАЖНО**: Введите ПОЛНЫЙ токен С префиксом "Token "
   - Формат: `Token ваш_токен_здесь`
   - Пример: `Token 5pjfnF3d_EHGciAwwxhDj-xfE4_B4As-BReu5fR3-jM`
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    version=os.getenv("APP_VERSION", default="DEV"),
    # Настройка безопасности для Swagger
    openapi_tags=[
        {"name": "auth", "description": "Аутентификация и авторизация"},
        {"name": "users", "description": "Управление пользователями"},
        {"name": "machines", "description": "Управление автоматами"},
        {"name": "reports", "description": "Отчеты и аналитика"},
        {"name": "api_tokens", "description": "🔑 API токены для программного доступа"},
        {"name": "documents", "description": "📁 Управление документами"},
        {"name": "audit", "description": "📋 Аудит и логирование"},
    ],
)

# Добавляем CORS middleware
from app.settings import settings

# Парсим CORS origins из переменной окружения
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Разрешенные источники из переменной окружения
    allow_credentials=True,  # Разрешаем передачу cookies и заголовков авторизации
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
        "PATCH",
    ],  # Явно указываем методы
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods",
    ],  # Явно указываем заголовки
)

# Добавляем Authentication middleware
app.add_middleware(
    AuthMiddleware,
    excluded_paths=[
        "/api/auth/login",
        "/api/auth/register",
        "/api/docs",
        "/api/redoc",
        "/openapi.json",
        "/api/status",
    ],
)

# Добавляем Audit middleware (после Authentication, чтобы иметь доступ к user_id)
app.add_middleware(
    AuditMiddleware,
    excluded_paths=[
        "/api/docs",
        "/api/redoc",
        "/openapi.json",
        "/api/status",
        "/api/audit/logs",  # Избегаем циклического логирования
        "/api/audit/stats",
        "/api/audit/actions",
        "/api/audit/tables",
        "/api/documents/download/",  # Скачивание по токену
    ],
    log_get_requests=False,  # Не логируем GET запросы (слишком много шума)
    log_request_body=True,  # Логируем тела запросов
    max_body_size=1024 * 5,  # 5KB лимит
)

# Добавляем middleware для очистки временных файлов
app.add_middleware(TempFileCleanupMiddleware)


def create_tables():
    try:
        Base.metadata.create_all(engine)
        logger.info("All tables checked/created successfully.")

        # Инициализируем базу данных данными по умолчанию
        init_database()

    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        raise


def init_database():
    """Инициализация базы данных с данными по умолчанию"""
    try:
        from sqlalchemy.orm import Session

        from app.api.auth.jwt import get_password_hash
        from app.external.sqlalchemy.models import (
            AccountType,
            CounterpartyCategory,
            InventoryCountStatus,
            ItemCategoryType,
            Owner,
            PurchaseOrderStatus,
            Rent,
            Role,
            Terminal,
            TransactionType,
            User,
        )
        from app.external.sqlalchemy.session import get_db

        db = next(get_db())

        # Проверяем, есть ли уже данные в базе
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            logger.info("Database already contains data. Initialization skipped.")
            return

        logger.info("Initializing database with default data...")

        # Создаем роли
        roles = [
            Role(name="admin", description="Полный доступ к системе", is_active=True),
            Role(name="user", description="Обычный пользователь", is_active=True),
            Role(name="readonly", description="Только чтение", is_active=True),
        ]

        for role in roles:
            db.add(role)
        db.commit()
        db.add(Owner(name="ИП Трубник А.Д.", inn=123456))
        db.add(Owner(name="ИП Дудка Ф.А.", inn=654321))
        db.add(
            Terminal(
                terminal=123456,
                name="Вендиста 3",
                owner_id=1,
            )
        )
        db.add(
            Rent(
                pay_date=5,
                location="кораблик",
                amount=15000,
                details="Куда платить и реквезиты",
                payer_id=1,
            )
        )
        db.commit()
        # Получаем ID ролей
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        user_role = db.query(Role).filter(Role.name == "user").first()
        readonly_role = db.query(Role).filter(Role.name == "readonly").first()

        # Создаем пользователей по умолчанию
        users = [
            User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                email="admin@example.com",
                full_name="Системный администратор",
                role_id=admin_role.id,
                is_active=True,
            ),
            User(
                username="user",
                password_hash=get_password_hash("user123"),
                email="user@example.com",
                full_name="Тестовый пользователь",
                role_id=user_role.id,
                is_active=True,
            ),
            User(
                username="readonly",
                password_hash=get_password_hash("readonly123"),
                email="readonly@example.com",
                full_name="Пользователь только для чтения",
                role_id=readonly_role.id,
                is_active=True,
            ),
        ]

        for user in users:
            db.add(user)

        # Создаем справочные данные
        account_types = [
            AccountType(name="Расчетный счет", description="Основной расчетный счет"),
            AccountType(name="Касса", description="Наличные средства"),
            AccountType(name="Валютный счет", description="Счет в иностранной валюте"),
            AccountType(name="Депозит", description="Депозитный счет"),
        ]

        transaction_types = [
            TransactionType(name="income", description="Доход"),
            TransactionType(name="expense", description="Расход"),
            TransactionType(name="transfer", description="Перевод"),
        ]

        inventory_statuses = [
            InventoryCountStatus(name="draft", description="Черновик"),
            InventoryCountStatus(name="approved", description="Утвержден"),
            InventoryCountStatus(name="executed", description="Выполнен"),
            InventoryCountStatus(name="cancelled", description="Отменен"),
        ]

        order_statuses = [
            PurchaseOrderStatus(name="draft", description="Черновик"),
            PurchaseOrderStatus(name="sent", description="Отправлен"),
            PurchaseOrderStatus(name="confirmed", description="Подтвержден"),
            PurchaseOrderStatus(name="received", description="Получен"),
            PurchaseOrderStatus(name="cancelled", description="Отменен"),
        ]

        item_category_types = [
            ItemCategoryType(name="inventory", description="Товарные запасы"),
            ItemCategoryType(name="equipment", description="Оборудование"),
            ItemCategoryType(name="consumables", description="Расходные материалы"),
        ]

        counterparty_categories = [
            CounterpartyCategory(
                name="Поставщики", description="Поставщики товаров и услуг"
            ),
            CounterpartyCategory(name="Клиенты", description="Покупатели и заказчики"),
            CounterpartyCategory(name="Банки", description="Банковские организации"),
            CounterpartyCategory(
                name="Госучреждения", description="Государственные учреждения"
            ),
        ]

        # Добавляем все справочные данные
        for item in (
            account_types
            + transaction_types
            + inventory_statuses
            + order_statuses
            + item_category_types
            + counterparty_categories
        ):
            db.add(item)

        db.commit()
        logger.info("Database initialized successfully with default data.")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        db.close()


async def start_scheduler():
    """Запустить планировщик задач"""
    await task_scheduler.start()
    logger.info("Task scheduler started")


async def shutdown_scheduler():
    """Остановить планировщик задач"""
    await task_scheduler.shutdown()
    logger.info("Task scheduler stopped")


def create_app():
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": settings.log_level,
                "format": "<level>{level}: {message}</level>",
            }
        ]
    )

    app.add_event_handler("startup", create_tables)
    app.add_event_handler("startup", start_scheduler)
    app.add_event_handler("shutdown", shutdown_scheduler)
    app.include_router(status_router)
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(user_router, prefix="/api", tags=["users"])
    app.include_router(owner_router, prefix="/api", tags=["owners"])
    app.include_router(terminal_router, prefix="/api", tags=["terminals"])
    app.include_router(machine_router, prefix="/api", tags=["machines"])
    app.include_router(monitoring_router, prefix="/api", tags=["monitoring"])
    app.include_router(rent_router, prefix="/api", tags=["rent"])
    app.include_router(phone_router, prefix="/api", tags=["phones"])
    app.include_router(counterparty_router, prefix="/api", tags=["counterparties"])
    app.include_router(
        transaction_category_router, prefix="/api", tags=["transaction-categories"]
    )
    app.include_router(transaction_router, prefix="/api", tags=["transactions"])
    app.include_router(account_router, prefix="/api", tags=["accounts"])
    app.include_router(item_category_router, prefix="/api", tags=["item-categories"])
    app.include_router(warehouse_router, prefix="/api", tags=["warehouses"])
    app.include_router(item_router, prefix="/api", tags=["items"])
    app.include_router(warehouse_stock_router, prefix="/api", tags=["warehouse-stocks"])
    app.include_router(machine_stock_router, prefix="/api", tags=["machine-stocks"])
    app.include_router(
        inventory_movement_router, prefix="/api", tags=["inventory-movements"]
    )
    app.include_router(
        reference_tables_router, prefix="/api", tags=["reference-tables"]
    )
    app.include_router(reports_router, prefix="/api", tags=["reports"])
    app.include_router(info_cards_router, prefix="/api", tags=["info-cards"])
    app.include_router(terminal_operations_router)
    app.include_router(documents_router, prefix="/api", tags=["documents"])
    app.include_router(audit_router, prefix="/api", tags=["audit"])
    app.include_router(api_tokens_router, prefix="/api", tags=["api_tokens"])
    app.include_router(telegram_router, prefix="/api", tags=["telegram"])
    app.include_router(
        scheduled_jobs_router, prefix="/api/scheduled", tags=["scheduled-jobs"]
    )

    # Настройка кастомной OpenAPI схемы для Swagger
    app.openapi = custom_openapi

    return app
