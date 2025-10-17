import os
import uuid
import mimetypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from io import BytesIO

from fastapi import UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from minio import Minio
from minio.error import S3Error

from app.settings import settings
from app.services.storage_base import StorageBackend


class MinIOStorageService(StorageBackend):
    """Сервис для работы с MinIO объектным хранилищем"""

    def __init__(self):
        # Инициализация клиента MinIO
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            region=settings.MINIO_REGION,
        )

        self.bucket_name = settings.MINIO_BUCKET
        self.max_file_size = getattr(settings, "MAX_FILE_SIZE", 50 * 1024 * 1024)

        # Разрешенные MIME типы
        self.allowed_mime_types = {
            # Изображения
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
            # Документы
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            # Текстовые файлы
            "text/plain",
            "text/csv",
            # Архивы
            "application/zip",
            "application/x-rar-compressed",
            # Другие
            "application/json",
        }

        # Создаем bucket если не существует
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Создать bucket если не существует"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(
                    self.bucket_name, location=settings.MINIO_REGION
                )
                print(f"✅ MinIO bucket '{self.bucket_name}' created")
            else:
                print(f"✅ MinIO bucket '{self.bucket_name}' already exists")
        except S3Error as e:
            print(f"❌ Error creating MinIO bucket: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to initialize MinIO bucket: {str(e)}"
            )

    def validate_file(self, file: UploadFile) -> None:
        """Валидация загружаемого файла"""

        # Проверяем размер файла
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.max_file_size / (1024 * 1024):.1f}MB",
            )

        # Проверяем MIME тип
        mime_type = file.content_type
        if mime_type not in self.allowed_mime_types:
            raise HTTPException(
                status_code=415, detail=f"File type '{mime_type}' not allowed"
            )

        # Проверяем имя файла
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

    def _generate_object_name(self, original_filename: str, document_type: str) -> str:
        """Генерирует имя объекта для MinIO"""

        # Создаем уникальное имя файла
        file_extension = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"

        # Создаем структуру: document_type/year/month/unique_filename
        now = datetime.now(timezone.utc)
        object_name = f"{document_type}/{now.year}/{now.month:02d}/{unique_filename}"

        return object_name

    def save_file(self, file: UploadFile, document_type: str) -> tuple[str, str, int]:
        """Сохраняет файл в MinIO"""

        # Валидация
        self.validate_file(file)

        # Генерируем имя объекта
        object_name = self._generate_object_name(file.filename, document_type)

        # Получаем содержимое файла
        try:
            file_content = file.file.read()
            file_size = len(file_content)

            # Сбрасываем позицию файла на случай повторного чтения
            file.file.seek(0)

            # Создаем BytesIO объект для MinIO
            file_stream = BytesIO(file_content)
            file_stream.seek(0)

            # Загружаем в MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=file_size,
                content_type=file.content_type,
                metadata={
                    "original-filename": quote(file.filename),
                    "document-type": document_type,
                    "upload-timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Для MinIO возвращаем object_name как relative_path
            return f"minio://{self.bucket_name}/{object_name}", object_name, file_size

        except S3Error as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to upload file to MinIO: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to save file: {str(e)}"
            )

    def delete_file(self, object_name: str) -> bool:
        """Удаляет файл из MinIO"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting file from MinIO: {e}")
            return False

    def file_exists(self, object_name: str) -> bool:
        """Проверяет существование файла в MinIO"""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False

    def get_file_url(self, object_name: str) -> str:
        """Получить presigned URL для доступа к файлу"""
        try:
            # Генерируем presigned URL на 1 час
            url = self.client.presigned_get_object(
                self.bucket_name, object_name, expires=timedelta(hours=1)
            )
            return url
        except S3Error as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to generate file URL: {str(e)}"
            )

    def get_download_response(self, object_name: str, filename: str, mime_type: str):
        """Получить ответ для скачивания файла (redirect на presigned URL)"""
        try:
            # Очищаем имя файла от проблемных символов для заголовков
            # Используем только латинские буквы и цифры для HTTP заголовков
            safe_filename = "".join(
                c if c.isascii() and c.isalnum() and ord(c) < 128 else "_"
                for c in filename
            )
            # Убираем множественные подчеркивания
            while "__" in safe_filename:
                safe_filename = safe_filename.replace("__", "_")
            # Убираем подчеркивания в начале и конце
            safe_filename = safe_filename.strip("_")
            if not safe_filename:
                safe_filename = "download"

            # Генерируем presigned URL с правильными заголовками
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(minutes=30),
                response_headers={
                    "response-content-disposition": f'attachment; filename="{quote(safe_filename)}"',
                    "response-content-type": mime_type,
                },
            )
            return RedirectResponse(url=url)
        except S3Error as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to generate download URL: {str(e)}"
            )

    def generate_download_url(self, document_id: int, object_name: str) -> str:
        """Генерирует URL для скачивания файла"""
        # В случае MinIO возвращаем API endpoint для скачивания
        return f"/api/documents/{document_id}/download"

    def get_storage_stats(self) -> dict:
        """Возвращает статистику MinIO хранилища"""
        try:
            total_size = 0
            file_count = 0

            # Получаем список всех объектов в bucket
            objects = self.client.list_objects(self.bucket_name, recursive=True)

            for obj in objects:
                file_count += 1
                total_size += obj.size if obj.size else 0

            return {
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_type": "MinIO",
                "bucket": self.bucket_name,
                "endpoint": settings.MINIO_ENDPOINT,
            }

        except S3Error as e:
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "storage_type": "MinIO",
                "error": str(e),
            }

    def get_file_info(self, object_name: str) -> dict:
        """Получить информацию о файле"""
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata,
            }
        except S3Error as e:
            raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
