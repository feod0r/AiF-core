from datetime import datetime, timezone

from sqlalchemy import (
    DECIMAL,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    users = relationship("User", back_populates="role", cascade="all, delete-orphan")


class AccountType(Base):
    __tablename__ = "account_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)


class TransactionType(Base):
    __tablename__ = "transaction_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class InventoryCountStatus(Base):
    __tablename__ = "inventory_count_statuses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class PurchaseOrderStatus(Base):
    __tablename__ = "purchase_order_statuses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class ItemCategoryType(Base):
    __tablename__ = "item_category_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class CounterpartyCategory(Base):
    __tablename__ = "counterparty_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    counterparties = relationship(
        "Counterparty", back_populates="category", cascade="all, delete-orphan"
    )


class Counterparty(Base):
    __tablename__ = "counterparties"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category_id = Column(
        Integer,
        ForeignKey("counterparty_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    inn = Column(String(20))
    kpp = Column(String(20))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    contact_person = Column(String(255))
    notes = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    category = relationship("CounterpartyCategory", back_populates="counterparties")


class TransactionCategory(Base):
    __tablename__ = "transaction_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    transaction_type_id = Column(
        Integer, ForeignKey("transaction_types.id", ondelete="CASCADE"), nullable=False
    )
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    transaction_type = relationship("TransactionType")
    transactions = relationship(
        "Transaction", back_populates="category", cascade="all, delete-orphan"
    )


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    account_type_id = Column(
        Integer, ForeignKey("account_types.id", ondelete="CASCADE"), nullable=False
    )
    owner_id = Column(
        Integer, ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    initial_balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="RUB")
    account_number = Column(String(50))
    bank_name = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    account_type = relationship("AccountType")
    owner = relationship("Owner")
    transactions = relationship(
        "Transaction",
        back_populates="account",
        foreign_keys="Transaction.account_id",
        cascade="all, delete-orphan",
    )
    to_transactions = relationship(
        "Transaction", foreign_keys="Transaction.to_account_id"
    )


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    account_id = Column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    to_account_id = Column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True
    )
    category_id = Column(
        Integer,
        ForeignKey("transaction_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    counterparty_id = Column(
        Integer, ForeignKey("counterparties.id", ondelete="SET NULL"), nullable=True
    )
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type_id = Column(
        Integer, ForeignKey("transaction_types.id", ondelete="CASCADE"), nullable=False
    )
    description = Column(Text)
    machine_id = Column(
        Integer, ForeignKey("machines.id", ondelete="SET NULL"), nullable=True
    )
    rent_location_id = Column(
        Integer, ForeignKey("rent.id", ondelete="SET NULL"), nullable=True
    )
    reference_number = Column(String(50))
    is_confirmed = Column(Boolean, nullable=False, default=False)
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=datetime.now,
    )

    # Relationships
    account = relationship(
        "Account", back_populates="transactions", foreign_keys=[account_id]
    )
    to_account = relationship(
        "Account", back_populates="to_transactions", foreign_keys=[to_account_id]
    )
    category = relationship("TransactionCategory", back_populates="transactions")
    counterparty = relationship("Counterparty")
    transaction_type = relationship("TransactionType")
    machine = relationship("Machine")
    rent_location = relationship("Rent")
    created_by_user = relationship("User")


class Phone(Base):
    __tablename__ = "phones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pay_date = Column(
        Integer, nullable=False
    )  # День месяца (1-31) для ежемесячной оплаты
    phone = Column(String(20), nullable=False)  # Номер телефона/сим-карты
    amount = Column(Numeric(10, 2), nullable=False)  # Сумма оплаты
    details = Column(Text)  # Детали/описание
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )

    # Relationships
    machine = relationship(
        "Machine", back_populates="phone", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=datetime.now,
    )
    role = relationship("Role", back_populates="users")
    user_owners = relationship(
        "UserOwner", back_populates="user", cascade="all, delete-orphan"
    )


class UserOwner(Base):
    __tablename__ = "user_owners"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner_id = Column(
        Integer, nullable=False
    )  # Внешний ключ на owners, можно добавить relationship если потребуется
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    user = relationship("User", back_populates="user_owners")


class Owner(Base):
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    inn = Column(String(50), nullable=False)
    vendista_user = Column(String(50))
    vendista_pass = Column(String(50))
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    terminals = relationship(
        "Terminal", back_populates="owner", cascade="all, delete-orphan"
    )
    rents = relationship("Rent", back_populates="payer", cascade="all, delete-orphan")


class Terminal(Base):
    __tablename__ = "terminals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    terminal = Column(Integer)  # Номер терминала
    name = Column(String(255), nullable=False)
    owner_id = Column(
        Integer, ForeignKey("owners.id", ondelete="CASCADE"), nullable=True
    )
    account_id = Column(
        Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )  # Расчетный счет терминала
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    owner = relationship("Owner", back_populates="terminals")
    account = relationship("Account")
    machines = relationship(
        "Machine", back_populates="terminal", cascade="all, delete-orphan"
    )


class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    game_cost = Column(Numeric(10, 2))  # Стоимость игры
    terminal_id = Column(
        Integer, ForeignKey("terminals.id", ondelete="SET NULL"), nullable=True
    )
    rent_id = Column(Integer, ForeignKey("rent.id", ondelete="SET NULL"), nullable=True)
    phone_id = Column(
        Integer, ForeignKey("phones.id", ondelete="SET NULL"), nullable=True
    )
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    terminal = relationship("Terminal", back_populates="machines")
    monitoring_records = relationship(
        "Monitoring", back_populates="machine", cascade="all, delete-orphan"
    )
    cashless_payments = relationship(
        "CashlessPayment", back_populates="machine", cascade="all, delete-orphan"
    )
    rent = relationship("Rent", back_populates="machine")
    phone = relationship("Phone", back_populates="machine")


class Monitoring(Base):
    __tablename__ = "monitoring"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    coins = Column(Numeric(10, 2), nullable=False)  # Количество монет
    toys = Column(Integer, nullable=False)  # Количество игрушек
    machine_id = Column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False
    )
    machine = relationship("Machine", back_populates="monitoring_records")

    # Уникальный ключ для предотвращения дублирования
    __table_args__ = (
        UniqueConstraint(
            "machine_id", "coins", "toys", name="unique_machine_coins_toys"
        ),
    )


class CashlessPayment(Base):
    __tablename__ = "cashless_payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(
        DateTime(timezone=True), nullable=False
    )  # Дата (без времени, только день)
    amount = Column(
        Numeric(10, 2), nullable=False, default=0
    )  # Сумма безналичных платежей
    transactions_count = Column(
        Integer, nullable=False, default=0
    )  # Количество транзакций
    machine_id = Column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False
    )
    machine = relationship("Machine", back_populates="cashless_payments")
    # Уникальный ключ: один автомат - одна запись на день
    __table_args__ = (
        UniqueConstraint("machine_id", "date", name="unique_machine_date"),
    )


class Rent(Base):
    __tablename__ = "rent"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pay_date = Column(Integer, nullable=False)  # Дата оплаты аренды
    location = Column(String(255), nullable=False)  # Местоположение
    amount = Column(Numeric(10, 2), nullable=False)  # Сумма аренды
    details = Column(Text)  # Детали/описание
    latitude = Column(DECIMAL(10, 8), nullable=True)  # Широта (latitude)
    longitude = Column(DECIMAL(11, 8), nullable=True)  # Долгота (longitude)
    payer_id = Column(
        Integer, ForeignKey("owners.id", ondelete="CASCADE"), nullable=True
    )
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    payer = relationship("Owner", back_populates="rents")
    machine = relationship(
        "Machine", back_populates="rent", cascade="all, delete-orphan"
    )


class ItemCategory(Base):
    __tablename__ = "item_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category_type_id = Column(
        Integer,
        ForeignKey("item_category_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    description = Column(Text)
    parent_id = Column(
        Integer, ForeignKey("item_categories.id", ondelete="SET NULL"), nullable=True
    )  # Иерархия категорий
    is_active = Column(Boolean, nullable=False, default=True)
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )

    # Relationships
    category_type = relationship("ItemCategoryType")
    parent = relationship("ItemCategory", remote_side=[id])
    children = relationship(
        "ItemCategory", back_populates="parent", cascade="all, delete-orphan"
    )
    items = relationship(
        "Item", back_populates="category", cascade="all, delete-orphan"
    )


class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    contact_person_id = Column(
        Integer, ForeignKey("counterparties.id", ondelete="SET NULL"), nullable=True
    )
    owner_id = Column(
        Integer, ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    is_active = Column(Boolean, nullable=False, default=True)
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )

    # Relationships
    owner = relationship("Owner")
    stocks = relationship(
        "WarehouseStock", back_populates="warehouse", cascade="all, delete-orphan"
    )
    contact_person = relationship("Counterparty")


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), unique=True, nullable=False)  # Артикул товара
    category_id = Column(
        Integer, ForeignKey("item_categories.id", ondelete="CASCADE"), nullable=False
    )
    description = Column(Text)
    unit = Column(String(20), nullable=False, default="шт")  # Единица измерения
    weight = Column(Numeric(10, 3))  # Вес в кг
    dimensions = Column(String(100))  # Габариты (ДxШxВ см)
    barcode = Column(String(50))  # Штрихкод
    min_stock = Column(Numeric(15, 3), nullable=False, default=0)  # Минимальный остаток
    max_stock = Column(Numeric(15, 3))  # Максимальный остаток
    is_active = Column(Boolean, nullable=False, default=True)
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )

    # Relationships
    category = relationship("ItemCategory", back_populates="items")
    warehouse_stocks = relationship(
        "WarehouseStock", back_populates="item", cascade="all, delete-orphan"
    )
    machine_stocks = relationship(
        "MachineStock", back_populates="item", cascade="all, delete-orphan"
    )
    prices = relationship("Price", back_populates="item", cascade="all, delete-orphan")


class WarehouseStock(Base):
    __tablename__ = "warehouse_stocks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(
        Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    quantity = Column(Numeric(15, 3), nullable=False, default=0)  # Количество
    reserved_quantity = Column(
        Numeric(15, 3), nullable=False, default=0
    )  # Зарезервированное количество
    min_quantity = Column(
        Numeric(15, 3), nullable=False, default=0
    )  # Минимальный остаток
    max_quantity = Column(Numeric(15, 3))  # Максимальный остаток
    location = Column(String(255))  # Место хранения на складе
    last_updated = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=datetime.now,
    )

    # Relationships
    warehouse = relationship("Warehouse", back_populates="stocks")
    item = relationship("Item", back_populates="warehouse_stocks")

    # Уникальный ключ: один товар - одна запись на складе
    __table_args__ = (
        UniqueConstraint("warehouse_id", "item_id", name="unique_warehouse_item"),
    )


class MachineStock(Base):
    __tablename__ = "machine_stocks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    quantity = Column(
        Numeric(15, 3), nullable=False, default=0
    )  # Количество в автомате
    capacity = Column(Numeric(15, 3))  # Вместимость автомата для данного товара
    min_quantity = Column(
        Numeric(15, 3), nullable=False, default=0
    )  # Минимальный остаток
    last_updated = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=datetime.now,
    )

    # Relationships
    machine = relationship("Machine")
    item = relationship("Item", back_populates="machine_stocks")

    # Уникальный ключ: один товар - одна запись в автомате
    __table_args__ = (
        UniqueConstraint("machine_id", "item_id", name="unique_machine_item"),
    )


class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    price_type = Column(
        String(50), nullable=False, default="sale"
    )  # Тип цены: sale, purchase, wholesale
    price = Column(Numeric(15, 2), nullable=False)  # Цена
    currency = Column(String(3), nullable=False, default="RUB")
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime(9999, 12, 31, 0, 0, 0)
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    item = relationship("Item", back_populates="prices")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    movement_type = Column(
        String(50), nullable=False
    )  # Тип движения: receipt, issue, transfer, adjustment, sale
    document_date = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )  # Дата документа
    status_id = Column(
        Integer,
        ForeignKey("inventory_count_statuses.id", ondelete="CASCADE"),
        nullable=False,
    )  # Статус документа
    description = Column(Text)  # Описание операции

    # Места отправления и назначения
    from_warehouse_id = Column(
        Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True
    )  # Склад отправления
    to_warehouse_id = Column(
        Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True
    )  # Склад назначения
    from_machine_id = Column(
        Integer, ForeignKey("machines.id", ondelete="SET NULL"), nullable=True
    )  # Автомат отправления
    to_machine_id = Column(
        Integer, ForeignKey("machines.id", ondelete="SET NULL"), nullable=True
    )  # Автомат назначения

    # Контрагенты
    counterparty_id = Column(
        Integer, ForeignKey("counterparties.id", ondelete="SET NULL"), nullable=True
    )  # Контрагент

    # Ответственные лица
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # Кто создал
    approved_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # Кто утвердил
    executed_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # Кто выполнил

    # Даты
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)  # Дата утверждения
    executed_at = Column(DateTime(timezone=True), nullable=True)  # Дата выполнения

    # Суммы
    total_amount = Column(
        Numeric(15, 2), nullable=False, default=0.00
    )  # Общая сумма документа
    currency = Column(String(3), nullable=False, default="RUB")  # Валюта

    # Relationships
    status = relationship("InventoryCountStatus")
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id])
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id])
    from_machine = relationship("Machine", foreign_keys=[from_machine_id])
    to_machine = relationship("Machine", foreign_keys=[to_machine_id])
    counterparty = relationship("Counterparty")
    created_by_user = relationship("User", foreign_keys=[created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    executed_by_user = relationship("User", foreign_keys=[executed_by])
    items = relationship(
        "InventoryMovementItem", back_populates="movement", cascade="all, delete-orphan"
    )


class InventoryMovementItem(Base):
    __tablename__ = "inventory_movement_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    movement_id = Column(
        Integer,
        ForeignKey("inventory_movements.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    quantity = Column(Numeric(15, 3), nullable=False)  # Количество
    price = Column(Numeric(15, 2), nullable=False, default=0.00)  # Цена за единицу
    amount = Column(Numeric(15, 2), nullable=False, default=0.00)  # Сумма по позиции
    description = Column(Text)  # Описание позиции

    # Relationships
    movement = relationship("InventoryMovement", back_populates="items")
    item = relationship("Item")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    machine_id = Column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False
    )
    revenue = Column(Numeric(15, 2), nullable=False, default=0)  # Выручка (руб)
    toy_consumption = Column(Integer, nullable=False, default=0)  # Расход игрушек (шт)
    plays_per_toy = Column(Numeric(15, 4), nullable=False, default=0)  # Игр на игрушку
    profit = Column(Numeric(15, 2), nullable=False, default=0)  # Прибыль (руб)
    days_count = Column(Integer, nullable=False, default=0)
    rent_cost = Column(Numeric(15, 2), nullable=False, default=0)  # Аренда за дни (руб)

    machine = relationship("Machine")

    __table_args__ = (
        UniqueConstraint(
            "report_date", "machine_id", name="unique_report_per_day_machine"
        ),
    )


class InfoCard(Base):
    __tablename__ = "info_cards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    external_link = Column(String(500), nullable=True)
    secrets = Column(Text, nullable=True)  # JSON строка с зашифрованными секретами
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = Column(Boolean, nullable=False, default=True)


class TerminalOperation(Base):
    __tablename__ = "terminal_operations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_date = Column(Date, nullable=False)  # Дата операции
    terminal_id = Column(
        Integer, ForeignKey("terminals.id", ondelete="CASCADE"), nullable=False
    )  # Терминал
    amount = Column(Numeric(15, 2), nullable=False, default=0.00)  # Сумма покупок
    transaction_count = Column(
        Integer, nullable=False, default=0
    )  # Количество транзакций
    commission = Column(Numeric(15, 2), nullable=False, default=0.00)  # Комиссия
    is_closed = Column(Boolean, nullable=False, default=False)  # Закрыт ли день
    closed_at = Column(DateTime(timezone=True), nullable=True)  # Когда закрыт день
    closed_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # Кто закрыл день
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Уникальный ключ: дата + терминал
    __table_args__ = (
        UniqueConstraint(
            "operation_date", "terminal_id", name="unique_terminal_operation_per_day"
        ),
    )

    # Relationships
    terminal = relationship("Terminal")
    closed_by_user = relationship("User", foreign_keys=[closed_by])


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)  # Имя файла для отображения
    original_filename = Column(String(255), nullable=False)  # Оригинальное имя файла
    file_path = Column(String(500), nullable=False)  # Путь к файлу на диске/URL
    file_size = Column(BigInteger, nullable=False)  # Размер файла в байтах
    mime_type = Column(String(100), nullable=False)  # MIME тип файла
    document_type = Column(
        String(50), nullable=False
    )  # Тип документа (receipt, contract, etc.)
    entity_type = Column(
        String(50), nullable=False, default="general"
    )  # К какой сущности привязан
    entity_id = Column(Integer, nullable=True)  # ID сущности
    description = Column(Text, nullable=True)  # Описание документа
    tags = Column(JSON, nullable=True)  # Теги для поиска
    upload_date = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    uploaded_by = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Отношения
    uploader = relationship("User")


class AuditLog(Base):
    """Модель для хранения аудит-логов системы"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action = Column(
        String(50), nullable=False
    )  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    table_name = Column(String(100), nullable=True)  # Название таблицы
    record_id = Column(Integer, nullable=True)  # ID записи
    old_values = Column(JSON, nullable=True)  # Старые значения (для UPDATE/DELETE)
    new_values = Column(JSON, nullable=True)  # Новые значения (для CREATE/UPDATE)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 адрес
    user_agent = Column(Text, nullable=True)  # User-Agent браузера
    endpoint = Column(String(255), nullable=True)  # API эндпоинт
    method = Column(String(10), nullable=True)  # HTTP метод (GET, POST, PUT, DELETE)
    request_id = Column(String(50), nullable=True)  # Уникальный ID запроса
    duration_ms = Column(Integer, nullable=True)  # Длительность выполнения в мс
    status_code = Column(Integer, nullable=True)  # HTTP статус код ответа
    error_message = Column(Text, nullable=True)  # Сообщение об ошибке (если есть)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    # Отношения
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, table={self.table_name}, user_id={self.user_id})>"


class ApiToken(Base):
    """Модель для API токенов"""

    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # Название токена
    description = Column(Text, nullable=True)  # Описание назначения
    token_hash = Column(
        String(255), nullable=False, unique=True, index=True
    )  # Хеш токена
    token_prefix = Column(
        String(10), nullable=False
    )  # Префикс для идентификации (например, первые 8 символов)

    # Владелец токена
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Разрешения
    permissions = Column(
        JSON, nullable=True
    )  # Список разрешений ['read:machines', 'write:reports']
    scopes = Column(
        JSON, nullable=True
    )  # Области доступа ['machines', 'reports', 'users']

    # Ограничения
    ip_whitelist = Column(JSON, nullable=True)  # Список разрешенных IP адресов
    rate_limit = Column(Integer, nullable=True, default=1000)  # Лимит запросов в час

    # Статус и время
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Дата истечения (None = бессрочный)
    last_used_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Последнее использование
    usage_count = Column(Integer, nullable=False, default=0)  # Количество использований

    # Временные метки
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Отношения
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ApiToken(id={self.id}, name={self.name}, prefix={self.token_prefix}, active={self.is_active})>"

    def is_expired(self):
        """Проверяет, истек ли токен"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        """Проверяет, валиден ли токен"""
        return self.is_active and not self.is_expired()

    def has_permission(self, permission: str) -> bool:
        """Проверяет, есть ли у токена определенное разрешение"""
        if not self.permissions:
            return False
        return permission in self.permissions

    def has_scope(self, scope: str) -> bool:
        """Проверяет, есть ли у токена доступ к определенной области"""
        if not self.scopes:
            return True  # Если не указано, доступ ко всему
        return scope in self.scopes

    def is_ip_allowed(self, ip_address: str) -> bool:
        """Проверяет, разрешен ли IP адрес"""
        if not self.ip_whitelist:
            return True  # Если не указано, разрешены все IP
        return ip_address in self.ip_whitelist


# Telegram Notifications Models
class TelegramBot(Base):
    __tablename__ = "telegram_bots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    bot_token = Column(String(255), nullable=False)
    chat_id = Column(String(255), nullable=False)
    notification_types = Column(JSON, nullable=False, default=list)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_test_message_at = Column(DateTime(timezone=True), nullable=True)
    test_message_status = Column(String(50), nullable=True)  # 'success', 'failed', null

    # Relationships
    creator = relationship("User", back_populates="telegram_bots")


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    priority = Column(String(20), default="medium")  # 'low', 'medium', 'high'
    sent_to = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    data = Column(JSON, nullable=True)  # Дополнительные данные
    # Связь с ботами через JSON поле в data
    # data может содержать {"bot_ids": [1, 2, 3], "bot_names": ["Bot1", "Bot2", "Bot3"]}

    # Relationships
    creator = relationship("User", back_populates="notification_history")


class ScheduledJob(Base):
    """Модель для хранения запланированных задач"""
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    job_type = Column(String(50), nullable=False)  # 'cron', 'interval', 'date'
    
    # Параметры расписания
    cron_expression = Column(String(100), nullable=True)  # Для cron задач
    interval_seconds = Column(Integer, nullable=True)  # Для интервальных задач
    scheduled_time = Column(DateTime(timezone=True), nullable=True)  # Для однократных задач
    
    # Параметры вызова функции
    function_path = Column(String(500), nullable=False)  # Путь к функции (module.path:function_name)
    function_params = Column(JSON, nullable=True)  # Параметры для вызова функции
    
    # Статус и управление
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    run_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User")


# Добавляем обратные связи в модель User
User.telegram_bots = relationship("TelegramBot", back_populates="creator")
User.notification_history = relationship(
    "NotificationHistory", back_populates="creator"
)
