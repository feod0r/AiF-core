from typing import List
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session

from app.api.users import controllers
from app.api.users.models import UserIn, UserOut, UserUpdate
from app.external.sqlalchemy.session import get_db
from app.api.auth.middleware_dependencies import (
    get_current_user,
    require_admin,
    require_user_role,
    get_user_id,
)

router: APIRouter = APIRouter()


# --- Users endpoints с использованием middleware ---

@router.get("/users", response_model=List[UserOut], tags=["users"])
def read_users_middleware(
    request: Request,
    skip: int = 0,
    limit: int = 100,
):
    """Получить список пользователей (только для админов)"""
    # Проверка прав администратора через middleware
    require_admin(request)
    
    # Получение сессии БД
    db = next(get_db())
    try:
        return controllers.get_users(db, skip=skip, limit=limit)
    finally:
        db.close()


@router.get("/users/{user_id}", response_model=UserOut, tags=["users"])
def read_user_middleware(request: Request, user_id: int):
    """Получить пользователя по ID (только для админов)"""
    # Проверка прав администратора через middleware
    require_admin(request)
    
    # Получение сессии БД
    db = next(get_db())
    try:
        return controllers.get_user(db, user_id)
    finally:
        db.close()


@router.post("/users", response_model=UserOut, tags=["users"])
def create_user_middleware(request: Request, user: UserIn):
    """Создать пользователя (только для админов)"""
    # Проверка прав администратора через middleware
    require_admin(request)
    
    # Получение сессии БД
    db = next(get_db())
    try:
        return controllers.create_user(db, user)
    finally:
        db.close()


@router.put("/users/{user_id}", response_model=UserOut, tags=["users"])
def update_user_middleware(request: Request, user_id: int, user: UserUpdate):
    """Обновить пользователя (только для админов)"""
    # Проверка прав администратора через middleware
    require_admin(request)
    
    # Получение сессии БД
    db = next(get_db())
    try:
        return controllers.update_user(db, user_id, user)
    finally:
        db.close()


@router.delete("/users/{user_id}", tags=["users"])
def delete_user_middleware(request: Request, user_id: int):
    """Удалить пользователя (только для админов)"""
    # Проверка прав администратора через middleware
    require_admin(request)
    
    # Получение сессии БД
    db = next(get_db())
    try:
        return controllers.delete_user(db, user_id)
    finally:
        db.close()


@router.get("/users/me/profile", response_model=UserOut, tags=["users"])
def get_my_profile_middleware(request: Request):
    """Получить свой профиль (для всех авторизованных пользователей)"""
    # Получение текущего пользователя из middleware
    current_user = get_current_user(request)
    
    # Возвращаем данные пользователя
    return current_user


@router.put("/users/me/profile", response_model=UserOut, tags=["users"])
def update_my_profile_middleware(request: Request, user_update: UserUpdate):
    """Обновить свой профиль (для всех авторизованных пользователей)"""
    # Получение ID текущего пользователя из middleware
    current_user_id = get_user_id(request)
    
    # Получение сессии БД
    db = next(get_db())
    try:
        # Обновляем только свой профиль
        return controllers.update_user(db, current_user_id, user_update)
    finally:
        db.close()


# Пример эндпоинта для разных ролей
@router.get("/users/stats", tags=["users"])
def get_users_stats_middleware(request: Request):
    """Получить статистику пользователей (для user и admin)"""
    # Проверка роли пользователя через middleware
    require_user_role(request)
    
    # Получение сессии БД
    db = next(get_db())
    try:
        # Возвращаем только базовую статистику
        from sqlalchemy import func
        from app.external.sqlalchemy.models import User
        
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
        }
    finally:
        db.close()
