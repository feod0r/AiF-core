from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from enum import Enum


class DocumentType(str, Enum):
    """Типы документов"""
    receipt = "receipt"  # Чеки
    contract = "contract"  # Договоры
    invoice = "invoice"  # Счета
    certificate = "certificate"  # Сертификаты
    photo = "photo"  # Фотографии
    report = "report"  # Отчеты
    other = "other"  # Прочие


class EntityType(str, Enum):
    """Типы сущностей, к которым привязаны документы"""
    transaction = "transaction"  # Транзакция
    machine = "machine"  # Автомат
    counterparty = "counterparty"  # Контрагент
    user = "user"  # Пользователь
    terminal = "terminal"  # Терминал
    inventory_movement = "inventory_movement"  # Движение товаров
    rent = "rent"  # Аренда
    general = "general"  # Общие документы


class DocumentIn(BaseModel):
    """Модель для загрузки документа"""
    filename: str
    document_type: DocumentType
    entity_type: Optional[EntityType] = EntityType.general
    entity_id: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        return v.strip()


class DocumentUpdate(BaseModel):
    """Модель для обновления документа"""
    filename: Optional[str] = None
    document_type: Optional[DocumentType] = None
    entity_type: Optional[EntityType] = None
    entity_id: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentOut(BaseModel):
    """Модель для вывода документа"""
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    document_type: DocumentType
    entity_type: EntityType
    entity_id: Optional[int] = None
    description: Optional[str] = None
    tags: List[str] = []
    upload_date: datetime
    uploaded_by: int
    download_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DocumentFilter(BaseModel):
    """Фильтры для поиска документов"""
    document_type: Optional[DocumentType] = None
    entity_type: Optional[EntityType] = None
    entity_id: Optional[int] = None
    uploaded_by: Optional[int] = None
    filename_contains: Optional[str] = None
    tags: Optional[List[str]] = []
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class DocumentStats(BaseModel):
    """Статистика по документам"""
    total_documents: int
    total_size_bytes: int
    total_size_mb: float
    documents_by_type: dict
    documents_by_entity: dict
    recent_uploads: List[DocumentOut]


class DownloadToken(BaseModel):
    """Временный токен для скачивания документа"""
    download_url: str
    expires_at: datetime
    token: str
