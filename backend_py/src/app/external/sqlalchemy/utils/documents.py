from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime

from app.external.sqlalchemy.models import Document, User
from app.api.documents.models import DocumentIn, DocumentUpdate, DocumentFilter, DocumentStats


def create_document(
    db: Session,
    document_data: DocumentIn,
    file_path: str,
    file_size: int,
    mime_type: str,
    uploaded_by: int
) -> Document:
    """Создать новый документ"""
    
    document = Document(
        filename=document_data.filename,
        original_filename=document_data.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        document_type=document_data.document_type.value,
        entity_type=document_data.entity_type.value if document_data.entity_type else "general",
        entity_id=document_data.entity_id,
        description=document_data.description,
        tags=document_data.tags or [],
        uploaded_by=uploaded_by,
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document(db: Session, document_id: int) -> Optional[Document]:
    """Получить документ по ID"""
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents(
    db: Session,
    filters: DocumentFilter = None,
    skip: int = 0,
    limit: int = 100
) -> List[Document]:
    """Получить список документов с фильтрацией"""
    
    query = db.query(Document)
    
    if filters:
        if filters.document_type:
            query = query.filter(Document.document_type == filters.document_type.value)
        
        if filters.entity_type:
            query = query.filter(Document.entity_type == filters.entity_type.value)
        
        if filters.entity_id:
            query = query.filter(Document.entity_id == filters.entity_id)
        
        if filters.uploaded_by:
            query = query.filter(Document.uploaded_by == filters.uploaded_by)
        
        if filters.filename_contains:
            search_term = f"%{filters.filename_contains}%"
            query = query.filter(
                or_(
                    Document.filename.ilike(search_term),
                    Document.original_filename.ilike(search_term),
                    Document.description.ilike(search_term)
                )
            )
        
        if filters.tags:
            # Поиск по тегам (JSON contains)
            for tag in filters.tags:
                query = query.filter(Document.tags.contains([tag]))
        
        if filters.date_from:
            query = query.filter(Document.upload_date >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Document.upload_date <= filters.date_to)
    
    return query.order_by(desc(Document.upload_date)).offset(skip).limit(limit).all()


def update_document(
    db: Session,
    document_id: int,
    document_data: DocumentUpdate
) -> Optional[Document]:
    """Обновить документ"""
    
    document = get_document(db, document_id)
    if not document:
        return None
    
    update_data = document_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in ['document_type', 'entity_type'] and value:
            # Конвертируем enum в строку
            value = value.value
        setattr(document, field, value)
    
    document.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, document_id: int) -> bool:
    """Удалить документ"""
    
    document = get_document(db, document_id)
    if not document:
        return False
    
    db.delete(document)
    db.commit()
    return True


def get_documents_by_entity(
    db: Session,
    entity_type: str,
    entity_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Document]:
    """Получить все документы для конкретной сущности"""
    
    return (
        db.query(Document)
        .filter(
            and_(
                Document.entity_type == entity_type,
                Document.entity_id == entity_id
            )
        )
        .order_by(desc(Document.upload_date))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_documents_stats(db: Session) -> DocumentStats:
    """Получить статистику по документам"""
    
    # Общее количество и размер
    total_query = db.query(
        func.count(Document.id).label('count'),
        func.sum(Document.file_size).label('total_size')
    ).first()
    
    total_documents = total_query.count or 0
    total_size_bytes = total_query.total_size or 0
    
    # Статистика по типам документов
    documents_by_type = {}
    type_stats = (
        db.query(
            Document.document_type,
            func.count(Document.id).label('count')
        )
        .group_by(Document.document_type)
        .all()
    )
    
    for doc_type, count in type_stats:
        documents_by_type[doc_type] = count
    
    # Статистика по типам сущностей
    documents_by_entity = {}
    entity_stats = (
        db.query(
            Document.entity_type,
            func.count(Document.id).label('count')
        )
        .group_by(Document.entity_type)
        .all()
    )
    
    for entity_type, count in entity_stats:
        documents_by_entity[entity_type] = count
    
    # Последние загрузки
    recent_uploads = (
        db.query(Document)
        .order_by(desc(Document.upload_date))
        .limit(10)
        .all()
    )
    
    return DocumentStats(
        total_documents=total_documents,
        total_size_bytes=total_size_bytes,
        total_size_mb=round(total_size_bytes / (1024 * 1024), 2),
        documents_by_type=documents_by_type,
        documents_by_entity=documents_by_entity,
        recent_uploads=recent_uploads
    )


def search_documents(
    db: Session,
    search_query: str,
    skip: int = 0,
    limit: int = 100
) -> List[Document]:
    """Полнотекстовый поиск по документам"""
    
    search_term = f"%{search_query}%"
    
    # Создаем базовый запрос для поиска по текстовым полям
    query = db.query(Document).filter(
        or_(
            Document.filename.ilike(search_term),
            Document.original_filename.ilike(search_term),
            Document.description.ilike(search_term)
        )
    )
    
    # Получаем все документы, найденные по текстовым полям
    documents = query.order_by(desc(Document.upload_date)).all()
    
    # Фильтруем по тегам в Python (более надежно)
    filtered_documents = []
    for doc in documents:
        # Проверяем, есть ли поисковый запрос в тегах
        tag_match = False
        if doc.tags:
            for tag in doc.tags:
                if search_query.lower() in tag.lower():
                    tag_match = True
                    break
        
        # Добавляем документ, если он найден по текстовым полям или по тегам
        if tag_match or not doc.tags:
            filtered_documents.append(doc)
    
    # Применяем пагинацию
    return filtered_documents[skip:skip + limit]
