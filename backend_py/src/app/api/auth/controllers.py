from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth.jwt import create_access_token, get_password_hash, verify_password
from app.api.auth.models import PasswordChange, UserLogin, UserRegister, UserResponse
from app.settings import settings
from app.external.sqlalchemy.models import User
from app.external.sqlalchemy.utils.users import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.middleware.audit import log_authentication_event


def authenticate_user(db: Session, username: str, password: str):
    """Аутентификация пользователя"""
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def login_user(
    db: Session, 
    user_credentials: UserLogin, 
    ip_address: str = None, 
    user_agent: str = None
):
    """Вход пользователя"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        # Логируем неудачную попытку входа
        log_authentication_event(
            db=db,
            user_id=None,
            action="FAILED_LOGIN",
            ip_address=ip_address,
            user_agent=user_agent,
            additional_info={"username": user_credentials.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Логируем успешный вход
    log_authentication_event(
        db=db,
        user_id=user.id,
        action="LOGIN",
        ip_address=ip_address,
        user_agent=user_agent,
        additional_info={
            "username": user.username,
            "token_expires": access_token_expires.total_seconds()
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


def register_user(db: Session, user_data: UserRegister):
    """Регистрация нового пользователя"""
    # Проверяем, что пользователь с таким username не существует
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Проверяем, что email не занят
    existing_email = get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Хешируем пароль
    hashed_password = get_password_hash(user_data.password)

    # Создаем пользователя
    user_in = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role_id=user_data.role_id,
        is_active=True,
    )

    user = create_user(db, user_in)
    return UserResponse.model_validate(user)
