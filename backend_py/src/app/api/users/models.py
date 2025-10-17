from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr
from app.api.reference_tables.models import ReferenceItemOut


class UserOwnerOut(BaseModel):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    full_name: str
    role: ReferenceItemOut
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    user_owners: List[UserOwnerOut] = []

    model_config = ConfigDict(from_attributes=True)

class UserIn(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    full_name: str
    role_id: int
    owner_ids: Optional[List[int]] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    owner_ids: Optional[List[int]] = None


class PasswordChange(BaseModel):
    new_password: str
