from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import uuid
import time
from datetime import datetime, timedelta, timezone

from app.api.documents.models import (
    DocumentIn,
    DocumentUpdate,
    DocumentOut,
    DocumentFilter,
    DocumentStats,
    DocumentType,
    EntityType,
    DownloadToken,
)
from app.external.sqlalchemy.utils.documents import (
    create_document,
    get_document,
    get_documents,
    update_document,
    delete_document,
    get_documents_by_entity,
    get_documents_stats,
    search_documents,
)
from app.services.storage_factory import file_storage

# Простая в памяти система временных токенов
# В продакшене можно использовать Redis или базу данных
_download_tokens = {}


def _cleanup_expired_tokens():
    """Очистка истекших токенов"""
    current_time = time.time()
    expired_tokens = [
        token
        for token, data in _download_tokens.items()
        if data["expires_at"] < current_time
    ]
    for token in expired_tokens:
        del _download_tokens[token]


def _generate_download_token(
    document_id: int, user_id: int, expires_in_minutes: int = 15
) -> str:
    """Генерация временного токена для скачивания"""
    _cleanup_expired_tokens()

    token = str(uuid.uuid4())
    expires_at = time.time() + (expires_in_minutes * 60)

    _download_tokens[token] = {
        "document_id": document_id,
        "user_id": user_id,
        "expires_at": expires_at,
        "created_at": time.time(),
    }

    return token


def _validate_download_token(token: str) -> Optional[dict]:
    """Проверка валидности токена"""
    _cleanup_expired_tokens()

    if token not in _download_tokens:
        return None

    token_data = _download_tokens[token]
    if token_data["expires_at"] < time.time():
        del _download_tokens[token]
        return None

    return token_data


def _convert_document_to_out(document) -> DocumentOut:
    """Конвертирует SQLAlchemy объект Document в DocumentOut с заполненным download_url"""
    download_url = file_storage.generate_download_url(document.id, document.file_path)

    document_dict = {
        "id": document.id,
        "filename": document.filename,
        "original_filename": document.original_filename,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "document_type": document.document_type,
        "entity_type": document.entity_type,
        "entity_id": document.entity_id,
        "description": document.description,
        "tags": document.tags or [],
        "upload_date": document.upload_date,
        "uploaded_by": document.uploaded_by,
        "download_url": download_url,
    }
    return DocumentOut.model_validate(document_dict)


def upload_document(
    db: Session,
    file: UploadFile,
    document_type: DocumentType,
    uploaded_by: int,
    entity_type: Optional[EntityType] = None,
    entity_id: Optional[int] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> DocumentOut:
    """Загрузить новый документ"""

    # Сохраняем файл
    full_path, relative_path, file_size = file_storage.save_file(
        file, document_type.value
    )

    try:
        # Создаем запись в БД
        document_data = DocumentIn(
            filename=file.filename,
            document_type=document_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            tags=tags or [],
        )

        document = create_document(
            db=db,
            document_data=document_data,
            file_path=relative_path,
            file_size=file_size,
            mime_type=file.content_type,
            uploaded_by=uploaded_by,
        )

        # Конвертируем в выходную модель
        return _convert_document_to_out(document)

    except Exception as e:
        # Удаляем файл в случае ошибки при создании записи в БД
        file_storage.delete_file(relative_path)
        raise HTTPException(
            status_code=500, detail=f"Failed to create document record: {str(e)}"
        )


def get_document_by_id(db: Session, document_id: int) -> Optional[DocumentOut]:
    """Получить документ по ID"""

    document = get_document(db, document_id)
    if not document:
        return None

    return _convert_document_to_out(document)


def get_documents_list(
    db: Session,
    filters: Optional[DocumentFilter] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[DocumentOut]:
    """Получить список документов с фильтрацией"""

    documents = get_documents(db, filters, skip, limit)

    result = []
    for document in documents:
        result.append(_convert_document_to_out(document))

    return result


def update_document_info(
    db: Session, document_id: int, document_data: DocumentUpdate
) -> Optional[DocumentOut]:
    """Обновить информацию о документе"""

    document = update_document(db, document_id, document_data)
    if not document:
        return None

    return _convert_document_to_out(document)


def delete_document_by_id(db: Session, document_id: int) -> bool:
    """Удалить документ"""

    # Получаем документ для удаления файла
    document = get_document(db, document_id)
    if not document:
        return False

    # Удаляем файл
    file_storage.delete_file(document.file_path)

    # Удаляем запись из БД
    return delete_document(db, document_id)


def get_entity_documents(
    db: Session,
    entity_type: EntityType,
    entity_id: int,
    skip: int = 0,
    limit: int = 100,
) -> List[DocumentOut]:
    """Получить все документы для конкретной сущности"""

    documents = get_documents_by_entity(db, entity_type.value, entity_id, skip, limit)

    result = []
    for document in documents:
        result.append(_convert_document_to_out(document))

    return result


def get_documents_statistics(db: Session) -> DocumentStats:
    """Получить статистику по документам"""

    stats = get_documents_stats(db)

    # Конвертируем последние загрузки в DocumentOut
    recent_uploads_converted = []
    for document in stats.recent_uploads:
        recent_uploads_converted.append(_convert_document_to_out(document))

    # Создаем новый объект статистики с конвертированными загрузками
    from app.api.documents.models import DocumentStats

    return DocumentStats(
        total_documents=stats.total_documents,
        total_size_bytes=stats.total_size_bytes,
        total_size_mb=stats.total_size_mb,
        documents_by_type=stats.documents_by_type,
        documents_by_entity=stats.documents_by_entity,
        recent_uploads=recent_uploads_converted,
    )


def search_documents_by_query(
    db: Session, search_query: str, skip: int = 0, limit: int = 100
) -> List[DocumentOut]:
    """Поиск документов по запросу"""

    documents = search_documents(db, search_query, skip, limit)

    result = []
    for document in documents:
        result.append(_convert_document_to_out(document))

    return result


def generate_download_token_for_document(
    db: Session, document_id: int, user_id: int
) -> DownloadToken:
    """Генерация временного токена для скачивания документа"""
    # Проверяем что документ существует
    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Генерируем токен
    token = _generate_download_token(document_id, user_id, expires_in_minutes=15)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Формируем URL для скачивания
    download_url = f"/api/documents/download/{token}"

    return DownloadToken(download_url=download_url, expires_at=expires_at, token=token)


def download_file_by_token(token: str):
    """Скачивание файла по временному токену"""
    # Проверяем токен
    token_data = _validate_download_token(token)
    if not token_data:
        raise HTTPException(status_code=404, detail="Invalid or expired download token")

    document_id = token_data["document_id"]

    # Удаляем токен после использования (одноразовый)
    if token in _download_tokens:
        del _download_tokens[token]

    # Получаем файл
    from app.external.sqlalchemy.session import SessionLocal

    db = SessionLocal()
    try:
        return get_file_for_download_internal(db, document_id)
    finally:
        db.close()


def get_file_for_download_internal(db: Session, document_id: int):
    """Внутренняя функция для получения файла (без проверки авторизации)"""
    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Проверяем существование файла
    if not file_storage.file_exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Возвращаем ответ через storage service
    return file_storage.get_download_response(
        document.file_path, document.original_filename, document.mime_type
    )


def get_file_for_download(db: Session, document_id: int):
    """Получить ответ для скачивания файла (требует авторизации)"""
    return get_file_for_download_internal(db, document_id)
