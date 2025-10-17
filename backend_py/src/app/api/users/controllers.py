from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.users.models import UserIn, UserUpdate
from app.external.sqlalchemy.utils import users as user_crud


def get_user(db: Session, user_id: int):
    user = user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return user_crud.get_users(db, skip=skip, limit=limit)


def create_user(db: Session, user_in: UserIn):
    if user_crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    return user_crud.create_user(db, user_in)


def update_user(db: Session, user_id: int, user_update: UserUpdate):
    user = user_crud.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def delete_user(db: Session, user_id: int):
    success = user_crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}


def change_user_password(db: Session, user_id: int, new_password: str):
    success = user_crud.change_user_password(db, user_id, new_password)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}
