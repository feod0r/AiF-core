from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.auth.controllers import (
    login_user,
    register_user,
)
from app.api.auth.dependencies import get_current_active_user
from app.api.auth.middleware_dependencies import get_current_user
from app.api.auth.models import UserLogin, UserRegister, UserResponse
from app.external.sqlalchemy.session import get_db

router = APIRouter()


@router.post("/login", response_model=dict)
def login(request: Request, user_credentials: UserLogin, db: Session = Depends(get_db)):
    # Извлекаем IP адрес и User-Agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get('User-Agent')
    
    return login_user(db, user_credentials, ip_address, user_agent)


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    return register_user(db, user_data)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(request: Request):
    """Получить информацию о текущем пользователе через middleware"""
    current_user = get_current_user(request)
    return UserResponse.model_validate(current_user)
