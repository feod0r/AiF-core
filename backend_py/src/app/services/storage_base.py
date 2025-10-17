from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from fastapi import UploadFile


class StorageBackend(ABC):
    """Абстрактный базовый класс для различных типов хранилищ"""
    
    @abstractmethod
    def validate_file(self, file: UploadFile) -> None:
        """Валидация загружаемого файла"""
        pass
    
    @abstractmethod
    def save_file(self, file: UploadFile, document_type: str) -> tuple[str, str, int]:
        """Сохранить файл
        
        Returns:
            tuple[full_path, relative_path, file_size]
        """
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Удалить файл"""
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Проверить существование файла"""
        pass
    
    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        """Получить URL для доступа к файлу"""
        pass
    
    @abstractmethod
    def get_download_response(self, file_path: str, filename: str, mime_type: str):
        """Получить ответ для скачивания файла"""
        pass
    
    @abstractmethod
    def get_storage_stats(self) -> dict:
        """Получить статистику хранилища"""
        pass
    
    @abstractmethod
    def generate_download_url(self, document_id: int, file_path: str) -> str:
        """Сгенерировать URL для скачивания файла"""
        pass
