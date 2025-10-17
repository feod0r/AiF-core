from datetime import datetime
from typing import List, Optional, Type, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Generic type для справочных таблиц
T = TypeVar("T")


class ReferenceTableCRUD:
    """Универсальный CRUD для справочных таблиц с одинаковой структурой"""

    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    def get_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None,
        start_date_from: str = None,
        start_date_to: str = None
    ) -> List[T]:
        """Получить все записи с фильтрацией"""
        query = db.query(self.model_class)
        
        # Поиск по названию и описанию
        if search:
            from sqlalchemy import or_
            search_filter = or_(
                self.model_class.name.ilike(f"%{search}%"),
                self.model_class.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Фильтр по дате создания от
        if start_date_from:
            try:
                from_date = datetime.fromisoformat(start_date_from.replace('Z', '+00:00'))
                query = query.filter(self.model_class.start_date >= from_date)
            except (ValueError, AttributeError):
                pass
        
        # Фильтр по дате создания до
        if start_date_to:
            try:
                to_date = datetime.fromisoformat(start_date_to.replace('Z', '+00:00'))
                query = query.filter(self.model_class.start_date <= to_date)
            except (ValueError, AttributeError):
                pass
        
        return query.offset(skip).limit(limit).all()

    def get_by_id(self, db: Session, item_id: int) -> Optional[T]:
        """Получить запись по ID"""
        return db.query(self.model_class).filter(self.model_class.id == item_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[T]:
        """Получить запись по имени"""
        return db.query(self.model_class).filter(self.model_class.name == name).first()

    def create(self, db: Session, name: str, description: str = None) -> T:
        """Создать новую запись"""
        db_item = self.model_class(name=name, description=description)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    def update(
        self, db: Session, item_id: int, name: str = None, description: str = None
    ) -> Optional[T]:
        """Обновить запись"""
        item = self.get_by_id(db, item_id)
        if not item:
            return None

        if name is not None:
            item.name = name
        if description is not None:
            item.description = description

        db.commit()
        db.refresh(item)
        return item

    def delete(self, db: Session, item_id: int) -> bool:
        """Удалить запись"""
        item = self.get_by_id(db, item_id)
        if not item:
            return False

        db.delete(item)
        db.commit()
        return True

    def create_or_update(self, db: Session, name: str, description: str = None) -> T:
        """Создать или обновить запись по имени"""
        try:
            return self.create(db, name, description)
        except IntegrityError:
            # Если запись с таким именем уже существует, обновляем
            db.rollback()
            existing = self.get_by_name(db, name)
            if existing:
                if description is not None:
                    existing.description = description
                    db.commit()
                    db.refresh(existing)
                return existing
            else:
                raise


# Создаем экземпляры CRUD для каждой справочной таблицы
from ..models import (
    AccountType,
    CounterpartyCategory,
    InventoryCountStatus,
    ItemCategoryType,
    PurchaseOrderStatus,
    Role,
    TransactionType,
)

role_crud = ReferenceTableCRUD(Role)
account_type_crud = ReferenceTableCRUD(AccountType)
transaction_type_crud = ReferenceTableCRUD(TransactionType)
inventory_count_status_crud = ReferenceTableCRUD(InventoryCountStatus)
purchase_order_status_crud = ReferenceTableCRUD(PurchaseOrderStatus)
item_category_type_crud = ReferenceTableCRUD(ItemCategoryType)
counterparty_category_crud = ReferenceTableCRUD(CounterpartyCategory)

# Словарь для удобного доступа к CRUD по имени таблицы
reference_cruds = {
    "roles": role_crud,
    "account_types": account_type_crud,
    "transaction_types": transaction_type_crud,
    "inventory_count_statuses": inventory_count_status_crud,
    "purchase_order_statuses": purchase_order_status_crud,
    "item_category_types": item_category_type_crud,
    "counterparty_categories": counterparty_category_crud,
}
