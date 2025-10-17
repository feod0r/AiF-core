from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.users import controllers
from app.api.users.models import UserIn, UserOut, UserUpdate, PasswordChange
from app.external.sqlalchemy.session import get_db
from app.api.auth.dependencies import get_current_active_user, require_admin, require_admin_from_middleware

router: APIRouter = APIRouter()


# --- Users endpoints ---
@router.get("/users", response_model=List[UserOut], tags=["users"])
def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(require_admin_from_middleware),
    db: Session = Depends(get_db),
):
    return controllers.get_users(db, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UserOut, tags=["users"])
def read_user(
    request: Request,
    user_id: int, 
    current_user=Depends(require_admin_from_middleware), 
    db: Session = Depends(get_db)
):
    return controllers.get_user(db, user_id)


@router.post("/users", response_model=UserOut, tags=["users"])
def create_user(
    request: Request,
    user_in: UserIn, 
    current_user=Depends(require_admin_from_middleware), 
    db: Session = Depends(get_db)
):
    return controllers.create_user(db, user_in)


@router.put("/users/{user_id}", response_model=UserOut, tags=["users"])
def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    current_user=Depends(require_admin_from_middleware),
    db: Session = Depends(get_db),
):
    return controllers.update_user(db, user_id, user_update)


@router.delete("/users/{user_id}", tags=["users"])
def delete_user(
    request: Request,
    user_id: int, 
    current_user=Depends(require_admin_from_middleware), 
    db: Session = Depends(get_db)
):
    return controllers.delete_user(db, user_id)


@router.patch("/users/{user_id}/password", tags=["users"])
def change_user_password(
    request: Request,
    user_id: int,
    password_change: PasswordChange,
    current_user=Depends(require_admin_from_middleware),
    db: Session = Depends(get_db)
):
    return controllers.change_user_password(db, user_id, password_change.new_password)
