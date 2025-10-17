import os
import uuid
import mimetypes
import shutil
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime, timezone

from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from app.settings import settings
from app.services.storage_base import StorageBackend


class LocalFileStorageService(StorageBackend):
    """Сервис для работы с файловым хранилищем"""

    def __init__(self):
        # Создаем базовую директорию для хранения файлов
        self.base_path = Path(getattr(settings, "UPLOAD_DIR", "./uploads"))
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Максимальный размер файла (по умолчанию 50MB)
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

    def generate_file_path(
        self, original_filename: str, document_type: str
    ) -> tuple[str, str]:
        """Генерирует путь для сохранения файла"""

        # Создаем уникальное имя файла
        file_extension = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"

        # Создаем структуру папок: uploads/document_type/year/month/
        now = datetime.now(timezone.utc)
        folder_path = (
            self.base_path / document_type / str(now.year) / f"{now.month:02d}"
        )
        folder_path.mkdir(parents=True, exist_ok=True)

        # Полный путь к файлу
        file_path = folder_path / unique_filename

        # Возвращаем относительный путь от base_path и полный путь
        relative_path = str(file_path.relative_to(self.base_path))

        return str(file_path), relative_path

    def save_file(self, file: UploadFile, document_type: str) -> tuple[str, str, int]:
        """Сохраняет файл на диск"""

        # Валидация
        self.validate_file(file)

        # Генерируем путь
        full_path, relative_path = self.generate_file_path(file.filename, document_type)

        # Сохраняем файл
        try:
            with open(full_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
                file_size = len(content)

                # Сбрасываем позицию файла на случай повторного чтения
                file.file.seek(0)

            return full_path, relative_path, file_size

        except Exception as e:
            # Удаляем файл в случае ошибки
            if os.path.exists(full_path):
                os.unlink(full_path)
            raise HTTPException(
                status_code=500, detail=f"Failed to save file: {str(e)}"
            )

    def delete_file(self, file_path: str) -> bool:
        """Удаляет файл с диска"""
        try:
            full_path = self.base_path / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception:
            return False

    def get_file_path(self, relative_path: str) -> Path:
        """Возвращает полный путь к файлу"""
        return self.base_path / relative_path

    def file_exists(self, relative_path: str) -> bool:
        """Проверяет существование файла"""
        return self.get_file_path(relative_path).exists()

    def get_mime_type(self, filename: str) -> str:
        """Определяет MIME тип по имени файла"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def get_file_url(self, relative_path: str) -> str:
        """Получить URL для доступа к файлу"""
        return f"/api/documents/files/{relative_path}"

    def get_download_response(self, relative_path: str, filename: str, mime_type: str):
        """Получить ответ для скачивания файла"""
        file_path = self.get_file_path(relative_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        # Очищаем имя файла от проблемных символов для заголовков
        # Используем только латинские буквы и цифры для HTTP заголовков
        safe_filename = "".join(
            c if c.isascii() and c.isalnum() and ord(c) < 128 else "_" for c in filename
        )
        # Убираем множественные подчеркивания
        while "__" in safe_filename:
            safe_filename = safe_filename.replace("__", "_")
        # Убираем подчеркивания в начале и конце
        safe_filename = safe_filename.strip("_")
        if not safe_filename:
            safe_filename = "download"

        return FileResponse(
            path=str(file_path), filename=safe_filename, media_type=mime_type
        )

    def generate_download_url(self, document_id: int, relative_path: str) -> str:
        """Генерирует URL для скачивания файла"""
        # В продакшене здесь может быть CDN URL или signed URL
        return f"/api/documents/{document_id}/download"

    def get_storage_stats(self) -> dict:
        """Возвращает статистику хранилища"""
        total_size = 0
        file_count = 0

        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1

        return {
            "total_files": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "base_path": str(self.base_path),
        }


# Singleton moved to storage_factory.py
