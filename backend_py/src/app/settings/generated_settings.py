from typing import List, Literal

from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict, BaseSettings


class PostgreSQLSettings(BaseModel):
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: str
    postgres_database: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter=".",
        extra="ignore",
    )

    postgres: PostgreSQLSettings = Field()
    log_level: Literal["DEBUG", "INFO"] = "DEBUG"

    # CORS Settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,https://aif-tech.ru",
        description="Разрешенные CORS origins (через запятую)",
    )

    # JWT Settings
    secret_key: str = Field(default="your-secret-key-here-change-in-production")
    access_token_expire_minutes: int = Field(default=1440)

    # Info Cards Encryption Key
    info_cards_secret_key: str = Field(
        default="info-cards-encryption-key-change-in-production-for-security"
    )

    # Vendista API Settings
    vendista_token_url: str = Field(
        default="https://api.vendista.ru:99/token",
        description="URL для получения токена Vendista API",
    )
    vendista_report_url: str = Field(
        default="https://api.vendista.ru:99/reports/common",
        description="URL для получения отчетов Vendista API",
    )
