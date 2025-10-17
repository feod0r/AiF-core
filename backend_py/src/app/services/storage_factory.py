from app.settings import settings
from app.services.storage_base import StorageBackend
from app.services.file_storage import LocalFileStorageService


def get_storage_service() -> StorageBackend:
    """Фабрика для получения сервиса хранения файлов"""
    
    storage_type = getattr(settings, 'STORAGE_TYPE', 'local').lower()
    
    if storage_type == 'minio':
        try:
            from app.services.minio_storage import MinIOStorageService
            return MinIOStorageService()
        except ImportError as e:
            print(f"❌ MinIO not available: {e}")
            print("📁 Falling back to local storage")
            return LocalFileStorageService()
    
    elif storage_type == 'minio_proxy':
        try:
            from app.services.proxy_storage import ProxyStorageService
            return ProxyStorageService()
        except ImportError as e:
            print(f"❌ MinIO Proxy not available: {e}")
            print("📁 Falling back to local storage")
            return LocalFileStorageService()
    
    elif storage_type == 'local':
        return LocalFileStorageService()
    
    else:
        print(f"❌ Unknown storage type: {storage_type}")
        print("📁 Falling back to local storage")
        return LocalFileStorageService()


# Singleton instance
file_storage = get_storage_service()
