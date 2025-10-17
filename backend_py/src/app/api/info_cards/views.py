from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db
from .models import (
    InfoCardOut, 
    InfoCardCreate, 
    InfoCardUpdate, 
    InfoCardWithSecrets,
    InfoCardSecretsRequest
)
from .controllers import (
    create_info_card,
    get_info_cards,
    get_info_card,
    update_info_card,
    delete_info_card,
    get_card_secrets,
    has_secrets
)

router = APIRouter()


@router.get("/info-cards", response_model=List[InfoCardOut])
def list_info_cards(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Получить список всех информационных карточек"""
    cards = get_info_cards(db, include_inactive=include_inactive)
    return [
        InfoCardOut(
            id=card.id,
            title=card.title,
            description=card.description,
            external_link=card.external_link,
            created_at=card.created_at,
            updated_at=card.updated_at,
            is_active=card.is_active,
            has_secrets=has_secrets(card)
        )
        for card in cards
    ]


@router.get("/info-cards/{card_id}", response_model=InfoCardOut)
def get_info_card_by_id(
    card_id: int,
    db: Session = Depends(get_db)
):
    """Получить карточку по ID"""
    card = get_info_card(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карточка не найдена"
        )
    
    return InfoCardOut(
        id=card.id,
        title=card.title,
        description=card.description,
        external_link=card.external_link,
        created_at=card.created_at,
        updated_at=card.updated_at,
        is_active=card.is_active,
        has_secrets=has_secrets(card)
    )


@router.post("/info-cards", response_model=InfoCardOut)
def create_new_info_card(
    card_data: InfoCardCreate,
    db: Session = Depends(get_db)
):
    """Создать новую информационную карточку"""
    card = create_info_card(db, card_data)
    return InfoCardOut(
        id=card.id,
        title=card.title,
        description=card.description,
        external_link=card.external_link,
        created_at=card.created_at,
        updated_at=card.updated_at,
        is_active=card.is_active,
        has_secrets=has_secrets(card)
    )


@router.put("/info-cards/{card_id}", response_model=InfoCardOut)
def update_info_card_by_id(
    card_id: int,
    card_data: InfoCardUpdate,
    db: Session = Depends(get_db)
):
    """Обновить карточку"""
    card = update_info_card(db, card_id, card_data)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карточка не найдена"
        )
    
    return InfoCardOut(
        id=card.id,
        title=card.title,
        description=card.description,
        external_link=card.external_link,
        created_at=card.created_at,
        updated_at=card.updated_at,
        is_active=card.is_active,
        has_secrets=has_secrets(card)
    )


@router.delete("/info-cards/{card_id}")
def delete_info_card_by_id(
    card_id: int,
    db: Session = Depends(get_db)
):
    """Удалить карточку"""
    success = delete_info_card(db, card_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карточка не найдена"
        )
    
    return {"message": "Карточка удалена успешно"}


@router.post("/info-cards/{card_id}/secrets", response_model=InfoCardWithSecrets)
def get_info_card_secrets(
    card_id: int,
    request: InfoCardSecretsRequest,
    db: Session = Depends(get_db)
):
    """Получить карточку с расшифрованными секретами"""
    card = get_info_card(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карточка не найдена"
        )
    
    # В простой реализации мы всегда возвращаем секреты
    # В production здесь должна быть проверка мастер-пароля
    secrets = get_card_secrets(db, card_id)
    
    return InfoCardWithSecrets(
        id=card.id,
        title=card.title,
        description=card.description,
        external_link=card.external_link,
        created_at=card.created_at,
        updated_at=card.updated_at,
        is_active=card.is_active,
        has_secrets=has_secrets(card),
        secrets=secrets
    )
