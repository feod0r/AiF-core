from sqlalchemy.orm import Session
from ..models import User, UserOwner, Role
from typing import List, Optional
from datetime import datetime


# Получить пользователя по id
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


# Получить пользователя по username
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


# Получить пользователя по email
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


# Получить всех пользователей
def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


# Создать пользователя
def create_user(db: Session, user_in) -> User:
    from ..models import User, UserOwner
    from passlib.context import CryptContext
    
    # Используем ту же библиотеку, что и в JWT модуле
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Создаем SQLAlchemy модель из Pydantic данных
    user = User(
        username=user_in.username,
        password_hash=pwd_context.hash(user_in.password),
        email=user_in.email,
        full_name=user_in.full_name,
        role_id=user_in.role_id,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Добавляем связи с владельцами, если указаны
    if hasattr(user_in, 'owner_ids') and user_in.owner_ids:
        for owner_id in user_in.owner_ids:
            user_owner = UserOwner(
                user_id=user.id,
                owner_id=owner_id
            )
            db.add(user_owner)
        
        db.commit()
        db.refresh(user)
    
    return user


# Обновить пользователя
def update_user(db: Session, user_id: int, user_update) -> User:
    from passlib.context import CryptContext
    from ..models import UserOwner
    
    # Используем ту же библиотеку, что и в JWT модуле
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Обновляем поля из Pydantic модели
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.password is not None:
        user.password_hash = pwd_context.hash(user_update.password)
    if user_update.role_id is not None:
        user.role_id = user_update.role_id
    
    # Обновляем связи с владельцами, если указаны
    if hasattr(user_update, 'owner_ids') and user_update.owner_ids is not None:
        # Удаляем существующие связи
        db.query(UserOwner).filter(UserOwner.user_id == user_id).delete()
        
        # Добавляем новые связи
        for owner_id in user_update.owner_ids:
            user_owner = UserOwner(
                user_id=user_id,
                owner_id=owner_id
            )
            db.add(user_owner)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


# Удалить пользователя
def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


# Получить роль по имени
def get_role_by_name(db: Session, role_name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == role_name).first()


# Получить роль по id
def get_role_by_id(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()


# Получить все роли
def get_roles(db: Session) -> List[Role]:
    return db.query(Role).filter(Role.is_active == True).all()


# Сменить пароль пользователя
def change_user_password(db: Session, user_id: int, new_password: str) -> bool:
    from passlib.context import CryptContext
    
    # Используем ту же библиотеку, что и в JWT модуле
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    user.password_hash = pwd_context.hash(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    return True
