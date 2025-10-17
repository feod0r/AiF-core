from .generated_settings import Settings


class SpecialSettings(Settings):
    # Секретный ключ для шифрования InfoCard
    INFO_CARD_SECRET_KEY: str = "my-super-secret-key-for-info-cards-2024"

    # Настройки файлового хранилища
    STORAGE_TYPE: str = "minio_proxy"  # "local", "minio" или "minio_proxy"
    UPLOAD_DIR: str = "./uploads"  # Директория для локального хранения
    TEMP_UPLOAD_DIR: str = "./temp_uploads"  # Временная директория для прокси
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB максимальный размер файла

    # Настройки MinIO
    MINIO_ENDPOINT: str = "192.168.2.99:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "aif-core"
    MINIO_SECURE: bool = False  # True для HTTPS
    MINIO_REGION: str = "us-east-1"
