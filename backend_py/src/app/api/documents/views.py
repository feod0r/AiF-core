from typing import List, Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.documents.models import (
    DocumentOut, DocumentUpdate, DocumentFilter, DocumentStats,
    DocumentType, EntityType, DownloadToken
)
from app.api.documents import controllers
from app.external.sqlalchemy.session import get_db
from app.api.auth.middleware_dependencies import get_current_user, get_user_id

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentOut, tags=["documents"])
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    entity_type: Optional[EntityType] = Form(EntityType.general),
    entity_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of tags
    db: Session = Depends(get_db)
):
    """Загрузить новый документ"""
    
    user_id = get_user_id(request)
    
    # Парсим теги из JSON строки
    tags_list = []
    if tags:
        try:
            import json
            tags_list = json.loads(tags)
        except:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    return controllers.upload_document(
        db=db,
        file=file,
        document_type=document_type,
        uploaded_by=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        tags=tags_list
    )


@router.get("/documents", response_model=List[DocumentOut], tags=["documents"])
def get_documents(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    document_type: Optional[DocumentType] = Query(None),
    entity_type: Optional[EntityType] = Query(None),
    entity_id: Optional[int] = Query(None),
    filename_contains: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Получить список документов с фильтрацией"""
    
    # Проверяем авторизацию через middleware
    get_current_user(request)
    
    filters = DocumentFilter(
        document_type=document_type,
        entity_type=entity_type,
        entity_id=entity_id,
        filename_contains=filename_contains
    )
    
    return controllers.get_documents_list(db, filters, skip, limit)


@router.get("/documents/{document_id}", response_model=DocumentOut, tags=["documents"])
def get_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Получить документ по ID"""
    
    get_current_user(request)
    
    document = controllers.get_document_by_id(db, document_id)
    if not document:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.put("/documents/{document_id}", response_model=DocumentOut, tags=["documents"])
def update_document(
    request: Request,
    document_id: int,
    document_data: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """Обновить информацию о документе"""
    
    get_current_user(request)
    
    document = controllers.update_document_info(db, document_id, document_data)
    if not document:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.delete("/documents/{document_id}", tags=["documents"])
def delete_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Удалить документ"""
    
    get_current_user(request)
    
    success = controllers.delete_document_by_id(db, document_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}


@router.post("/documents/{document_id}/download-token", response_model=DownloadToken, tags=["documents"])
def generate_download_token(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Создать временный токен для скачивания документа"""
    
    user_id = get_user_id(request)
    
    return controllers.generate_download_token_for_document(db, document_id, user_id)


@router.get("/documents/download/{token}", tags=["documents"])
def download_document_by_token(
    token: str
):
    """Скачать файл документа по временному токену (без авторизации)"""
    
    return controllers.download_file_by_token(token)


@router.get("/documents/{document_id}/download", tags=["documents"])
def download_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Скачать файл документа (требует авторизации)"""
    
    get_current_user(request)
    
    # Контроллер теперь возвращает готовый response
    return controllers.get_file_for_download(db, document_id)


@router.get("/entities/{entity_type}/{entity_id}/documents", 
           response_model=List[DocumentOut], tags=["documents"])
def get_entity_documents(
    request: Request,
    entity_type: EntityType,
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Получить все документы для конкретной сущности"""
    
    get_current_user(request)
    
    return controllers.get_entity_documents(db, entity_type, entity_id, skip, limit)


@router.get("/documents/search/{search_query}", 
           response_model=List[DocumentOut], tags=["documents"])
def search_documents(
    request: Request,
    search_query: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Поиск документов по запросу"""
    
    get_current_user(request)
    
    return controllers.search_documents_by_query(db, search_query, skip, limit)


@router.get("/documents/stats/summary", response_model=DocumentStats, tags=["documents"])
def get_documents_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить статистику по документам"""
    
    get_current_user(request)
    
    return controllers.get_documents_statistics(db)


@router.get("/documents/types/list", tags=["documents"])
def get_document_types(request: Request):
    """Получить список доступных типов документов"""
    
    get_current_user(request)
    
    # Переводы типов документов
    document_type_labels = {
        "receipt": "Чеки",
        "contract": "Договоры", 
        "invoice": "Счета",
        "certificate": "Сертификаты",
        "photo": "Фотографии",
        "report": "Отчеты",
        "other": "Прочие"
    }
    
    # Переводы типов сущностей
    entity_type_labels = {
        "transaction": "Транзакция",
        "machine": "Автомат",
        "counterparty": "Контрагент", 
        "user": "Пользователь",
        "terminal": "Терминал",
        "inventory_movement": "Движение товаров",
        "rent": "Аренда",
        "general": "Общие документы"
    }
    
    return {
        "document_types": [
            {"value": dt.value, "label": document_type_labels.get(dt.value, dt.value.title())} 
            for dt in DocumentType
        ],
        "entity_types": [
            {"value": et.value, "label": entity_type_labels.get(et.value, et.value.title())} 
            for et in EntityType
        ]
    }
