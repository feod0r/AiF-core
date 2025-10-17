from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class InfoCardBase(BaseModel):
    title: str
    description: Optional[str] = None
    external_link: Optional[str] = None


class InfoCardCreate(InfoCardBase):
    secrets: Optional[Dict[str, str]] = None  # Словарь с секретами (ключ: значение)


class InfoCardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    external_link: Optional[str] = None
    secrets: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class InfoCardOut(InfoCardBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    has_secrets: bool  # Указывает, есть ли секреты (без раскрытия содержимого)

    model_config = ConfigDict(from_attributes=True)


class InfoCardWithSecrets(InfoCardOut):
    secrets: Optional[Dict[str, str]] = None  # Расшифрованные секреты для владельца


class InfoCardSecretsRequest(BaseModel):
    action: str  # 'view' или 'update'
    password: Optional[str] = None  # Мастер-пароль для доступа к секретам
