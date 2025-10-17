import json
import base64
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from app.external.sqlalchemy.models import InfoCard
from app.settings import settings
from .models import InfoCardCreate, InfoCardUpdate


def get_encryption_key() -> bytes:
    """Получить ключ шифрования из настроек приложения"""
    # Используем настройку из settings и создаем правильный ключ для Fernet
    key_string = settings.info_cards_secret_key
    # Создаем 32-байтовый ключ из строки настроек и кодируем в base64url для Fernet
    key_bytes = hashlib.sha256(key_string.encode()).digest()
    # Fernet требует base64url-encoded ключ
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_secrets(secrets: Dict[str, str]) -> str:
    """Зашифровать словарь секретов"""
    if not secrets:
        return ""

    fernet = Fernet(get_encryption_key())
    json_str = json.dumps(secrets)
    encrypted = fernet.encrypt(json_str.encode())
    # Fernet.encrypt уже возвращает base64url-encoded данные
    return encrypted.decode()


def decrypt_secrets(encrypted_secrets: str) -> Dict[str, str]:
    """Расшифровать секреты"""
    if not encrypted_secrets:
        return {}

    try:
        fernet = Fernet(get_encryption_key())
        # Fernet.decrypt ожидает bytes, не base64-decoded данные
        decrypted = fernet.decrypt(encrypted_secrets.encode())
        return json.loads(decrypted.decode())
    except Exception:
        return {}


def create_info_card(db: Session, card_data: InfoCardCreate) -> InfoCard:
    """Создать новую информационную карточку"""
    encrypted_secrets = ""
    if card_data.secrets:
        encrypted_secrets = encrypt_secrets(card_data.secrets)

    db_card = InfoCard(
        title=card_data.title,
        description=card_data.description,
        external_link=card_data.external_link,
        secrets=encrypted_secrets,
    )

    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


def get_info_cards(db: Session, include_inactive: bool = False) -> List[InfoCard]:
    """Получить список всех карточек"""
    query = db.query(InfoCard)
    if not include_inactive:
        query = query.filter(InfoCard.is_active == True)
    return query.order_by(InfoCard.updated_at.desc()).all()


def get_info_card(db: Session, card_id: int) -> Optional[InfoCard]:
    """Получить карточку по ID"""
    return db.query(InfoCard).filter(InfoCard.id == card_id).first()


def update_info_card(
    db: Session, card_id: int, card_data: InfoCardUpdate
) -> Optional[InfoCard]:
    """Обновить карточку"""
    db_card = get_info_card(db, card_id)
    if not db_card:
        return None

    # Обновляем основные поля
    if card_data.title is not None:
        db_card.title = card_data.title
    if card_data.description is not None:
        db_card.description = card_data.description
    if card_data.external_link is not None:
        db_card.external_link = card_data.external_link
    if card_data.is_active is not None:
        db_card.is_active = card_data.is_active

    # Обновляем секреты
    if card_data.secrets is not None:
        if card_data.secrets:
            db_card.secrets = encrypt_secrets(card_data.secrets)
        else:
            db_card.secrets = ""

    db_card.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_card)
    return db_card


def delete_info_card(db: Session, card_id: int) -> bool:
    """Удалить карточку"""
    db_card = get_info_card(db, card_id)
    if not db_card:
        return False

    db.delete(db_card)
    db.commit()
    return True


def get_card_secrets(db: Session, card_id: int) -> Dict[str, str]:
    """Получить расшифрованные секреты карточки"""
    db_card = get_info_card(db, card_id)
    if not db_card or not db_card.secrets:
        return {}

    return decrypt_secrets(db_card.secrets)


def has_secrets(card: InfoCard) -> bool:
    """Проверить, есть ли у карточки секреты"""
    return bool(card.secrets and card.secrets.strip())
